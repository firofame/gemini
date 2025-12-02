import subprocess
import modal

def hf_download():
    from huggingface_hub import hf_hub_download
    
    REPO_ID = "Comfy-Org/z_image_turbo"
    BASE_PATH = "/root/comfy/ComfyUI/models"
    
    models = [
        ("split_files/text_encoders/qwen_3_4b.safetensors", "text_encoders/qwen_3_4b.safetensors"),
        ("split_files/diffusion_models/z_image_turbo_bf16.safetensors", "diffusion_models/z_image_turbo_bf16.safetensors"),
        ("split_files/vae/ae.safetensors", "vae/ae.safetensors"),
    ]
    
    for remote_path, local_path in models:
        downloaded = hf_hub_download(repo_id=REPO_ID, filename=remote_path)
        subprocess.run(["ln", "-s", downloaded, f"{BASE_PATH}/{local_path}"], check=True)


vol = modal.Volume.from_name("hf-hub-cache", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install("git")
    .uv_pip_install("comfy-cli", "huggingface-hub")
    .run_commands("comfy --skip-prompt install --nvidia")
    .env({"HF_XET_HIGH_PERFORMANCE": "1", "HF_HOME": "/cache"})
    .run_function(hf_download, volumes={"/cache": vol})
)

app = modal.App(name="comfyapp", image=image, volumes={"/cache": vol})


@app.function(max_containers=1, gpu="L40s")
@modal.concurrent(max_inputs=10)
@modal.web_server(8188, startup_timeout=60)
def ui():
    subprocess.Popen(["comfy", "launch", "--", "--listen", "0.0.0.0"])