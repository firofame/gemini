import subprocess
import json
from pathlib import Path
import modal

# ============================================================
# Shared Image Configuration
# ============================================================
image = (
    modal.Image.debian_slim(python_version="3.13")
    .run_commands("apt update")
    .apt_install("git")
    .run_commands("pip install --upgrade pip")
    .uv_pip_install("comfy-cli")
    .run_commands("comfy --skip-prompt install --nvidia")
)

def hf_download():
    from huggingface_hub import hf_hub_download
    import os

    def download_and_link(repo_id, filename, subfolder, link_dir, link_name=None):
        path = hf_hub_download(repo_id=repo_id, filename=filename, subfolder=subfolder)
        link_name = link_name or filename
        os.makedirs(link_dir, exist_ok=True)
        subprocess.run(f"ln -s {path} {link_dir}/{link_name}", shell=True, check=True)

    ltx_model = hf_hub_download(repo_id="Lightricks/LTX-2.3-fp8", filename="ltx-2.3-22b-dev-fp8.safetensors")
    subprocess.run(f"ln -s {ltx_model} /root/comfy/ComfyUI/models/checkpoints/ltx-2.3-22b-dev-fp8.safetensors", shell=True, check=True)

    download_and_link("Lightricks/LTX-2.3", "ltx-2.3-22b-distilled-lora-384.safetensors", None, "/root/comfy/ComfyUI/models/loras")
    download_and_link("Lightricks/LTX-2.3", "ltx-2.3-spatial-upscaler-x2-1.0.safetensors", None, "/root/comfy/ComfyUI/models/latent_upscale_models")
    download_and_link("Comfy-Org/ltx-2", "gemma_3_12B_it_fp4_mixed.safetensors", "split_files/text_encoders", "/root/comfy/ComfyUI/models/text_encoders")
    download_and_link("Comfy-Org/ltx-2", "gemma-3-12b-it-abliterated_lora_rank64_bf16.safetensors", "split_files/loras", "/root/comfy/ComfyUI/models/loras")


vol = modal.Volume.from_name("hf-hub-cache", create_if_missing=True)
image = (
    image.uv_pip_install("huggingface-hub")
    .env({"HF_XET_HIGH_PERFORMANCE": "1", "HF_HOME": "/cache"})
    .run_function(hf_download, volumes={"/cache": vol})
)
image = image.add_local_file(
    Path(__file__).parent / "video_ltx2_3_i2v.json", "/root/video_ltx2_3_i2v.json"
)

# ============================================================
# App 1: API Inference - modal run comfyapp.py
# ============================================================
app = modal.App(name="comfyapp", image=image, volumes={"/cache": vol})


@app.cls(scaledown_window=300, gpu="L40S")
@modal.concurrent(max_inputs=5)
class ComfyUI:
    @modal.enter()
    def launch_comfy_background(self):
        subprocess.run("comfy launch --background", shell=True, check=True)

    @modal.method()
    def infer(
        self,
        image_bytes: bytes,
        prompt: str,
        workflow_path: str = "/root/video_ltx2_3_i2v.json",
    ):
        input_dir = Path("/root/comfy/ComfyUI/input")
        input_dir.mkdir(parents=True, exist_ok=True)
        input_image_path = input_dir / "input_image.png"
        input_image_path.write_bytes(image_bytes)

        workflow = json.loads(Path(workflow_path).read_text())
        workflow["269"]["inputs"]["image"] = "input_image.png"
        workflow["267:266"]["inputs"]["value"] = prompt

        modified_workflow_path = Path("/root/modified_workflow.json")
        modified_workflow_path.write_text(json.dumps(workflow, indent=2))

        cmd = f"comfy run --workflow {modified_workflow_path} --wait --timeout 1200 --verbose"
        subprocess.run(cmd, shell=True, check=True)

        output_dir = Path("/root/comfy/ComfyUI/output")
        file_prefix = workflow["75"]["inputs"]["filename_prefix"]

        if "/" in file_prefix:
            prefix_dir = file_prefix.rsplit("/", 1)[0]
            prefix_name = file_prefix.rsplit("/", 1)[1]
            search_dir = output_dir / prefix_dir
        else:
            search_dir = output_dir
            prefix_name = file_prefix

        if search_dir.exists():
            for f in search_dir.iterdir():
                if f.is_file() and f.name.startswith(prefix_name) and f.suffix == ".mp4":
                    return f.read_bytes()

        raise FileNotFoundError(
            f"No output file found matching '{prefix_name}*' in {search_dir}"
        )


@app.local_entrypoint()
def main(
    image_path: str = "/Users/firozahmed/Downloads/photo.jpg",
    prompt: str = "A majestic Egyptian pharaoh standing in front of pyramids, golden sunlight, cinematic movement",
):
    image_bytes = Path(image_path).read_bytes()

    print(f"Input image: {image_path}")
    print(f"Prompt: {prompt}")
    print("Starting video generation...")

    comfy = ComfyUI()
    file_bytes = comfy.infer.remote(image_bytes=image_bytes, prompt=prompt)

    output_dir = Path("/Users/firozahmed/Downloads")
    filename = output_dir / "output.mp4"
    filename.write_bytes(file_bytes)
    print(f"Saved to '{filename}'")


# ============================================================
# App 2: Web UI - modal serve comfyapp.py::ui_app
# ============================================================
ui_app = modal.App(name="comfyapp-ui", image=image, volumes={"/cache": vol})


@ui_app.function(
    max_containers=1,
    gpu="L40S",
    timeout=3600,
)
@modal.concurrent(max_inputs=10)
@modal.web_server(8000, startup_timeout=120)
def ui():
    subprocess.Popen("comfy launch -- --listen 0.0.0.0 --port 8000", shell=True)