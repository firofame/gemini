import subprocess
import modal

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

    # Helper to download and symlink
    def download_and_link(repo_id, filename, subfolder, link_dir, link_name=None):
        path = hf_hub_download(repo_id=repo_id, filename=filename, subfolder=subfolder)
        link_name = link_name or filename
        os.makedirs(link_dir, exist_ok=True)
        subprocess.run(f"ln -s {path} {link_dir}/{link_name}", shell=True, check=True)

    # Original model
    ltx_model = hf_hub_download(repo_id="Lightricks/LTX-2.3-fp8", filename="ltx-2.3-22b-dev-fp8.safetensors")
    subprocess.run(f"ln -s {ltx_model} /root/comfy/ComfyUI/models/checkpoints/ltx-2.3-22b-dev-fp8.safetensors", shell=True, check=True)

    # Added models
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

app = modal.App(name="comfyapp", image=image)
@app.function(max_containers=1, gpu="L40s", volumes={"/cache": vol})
@modal.concurrent(max_inputs=10)
@modal.web_server(8000, startup_timeout=60)
def ui():
    subprocess.Popen("comfy launch -- --listen 0.0.0.0 --port 8000", shell=True)