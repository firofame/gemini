import subprocess
import modal
import json
from pathlib import Path
from datetime import datetime
import random

width = 512
height = 768
prompt = "change background to a forest"
file_name = "photo.png"
file_path = "/Users/firozahmed/Downloads"

def hf_download():
    import subprocess
    from huggingface_hub import hf_hub_download
    
    models = [
        ("Phr00t/Qwen-Image-Edit-Rapid-AIO", "v12/Qwen-Rapid-AIO-NSFW-v12.safetensors", "checkpoints/Qwen-Rapid-AIO-NSFW-v12.safetensors"),
    ]
    
    for repo_id, remote_path, local_path in models:
        downloaded = hf_hub_download(repo_id=repo_id, filename=remote_path)
        subprocess.run(["ln", "-s", downloaded, f"/root/comfy/ComfyUI/models/{local_path}"], check=True)

vol = modal.Volume.from_name("hf-hub-cache", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install("git")
    .uv_pip_install("comfy-cli", "huggingface-hub")
    .run_commands("comfy --skip-prompt install --nvidia")
    .env({"HF_XET_HIGH_PERFORMANCE": "1", "HF_HOME": "/cache"})
    .run_function(hf_download, volumes={"/cache": vol})
    .add_local_file(f"{file_path}/{file_name}", f"/root/comfy/ComfyUI/input/{file_name}")
)

app = modal.App(name="comfyapp", image=image, volumes={"/cache": vol})


# @app.function(max_containers=1, gpu="T4")
# @modal.concurrent(max_inputs=10)
# @modal.web_server(8188, startup_timeout=60)
# def ui():
#     subprocess.Popen(["comfy", "launch", "--", "--listen", "0.0.0.0"])

@app.cls(scaledown_window=300, gpu="L40S")
@modal.concurrent(max_inputs=5)
class ComfyUI:
    @modal.enter()
    def launch_comfy_background(self):
        seed = random.randint(1, 1000000)
        workflow = {"1":{"inputs":{"ckpt_name":"Qwen-Rapid-AIO-NSFW-v12.safetensors"},"class_type":"CheckpointLoaderSimple","_meta":{"title":"Load Checkpoint"}},"2":{"inputs":{"seed":seed,"steps":4,"cfg":1,"sampler_name":"sa_solver","scheduler":"beta","denoise":1,"model":["1",0],"positive":["3",0],"negative":["4",0],"latent_image":["9",0]},"class_type":"KSampler","_meta":{"title":"KSampler"}},"3":{"inputs":{"prompt":prompt,"clip":["1",1],"vae":["1",2],"image1":["7",0]},"class_type":"TextEncodeQwenImageEditPlus","_meta":{"title":"TextEncodeQwenImageEditPlus Input Prompt"}},"4":{"inputs":{"prompt":"","clip":["1",1],"vae":["1",2]},"class_type":"TextEncodeQwenImageEditPlus","_meta":{"title":"TextEncodeQwenImageEditPlus Negative (leave blank)"}},"5":{"inputs":{"samples":["2",0],"vae":["1",2]},"class_type":"VAEDecode","_meta":{"title":"VAE Decode"}},"7":{"inputs":{"image":file_name},"class_type":"LoadImage","_meta":{"title":"Optional Input Image"}},"9":{"inputs":{"width":width,"height":height,"batch_size":1},"class_type":"EmptyLatentImage","_meta":{"title":"Final Image Size"}},"10":{"inputs":{"filename_prefix":"ComfyUI","images":["5",0]},"class_type":"SaveImage","_meta":{"title":"Save Image"}}}
        with open("/root/workflow_api.json", "w") as f:
            json.dump(workflow, f)
        subprocess.run("comfy launch --background", shell=True, check=True)

    @modal.method()
    def infer(self, workflow_path: str = "/root/workflow_api.json"):
        cmd = f"comfy run --workflow {workflow_path} --wait --timeout 1200 --verbose"
        subprocess.run(cmd, shell=True, check=True)

        output_dir = "/root/comfy/ComfyUI/output"
        file_prefix = "ComfyUI"

        for f in Path(output_dir).iterdir():
            if f.name.startswith(file_prefix):
                return f.read_bytes(), f.suffix

@app.local_entrypoint()
def main():
    output_bytes, suffix = ComfyUI().infer.remote()
    date_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file_path = f"{file_path}/{file_name}_{date_time}{suffix}"
    with open(output_file_path, "wb") as f:
        f.write(output_bytes)
    print(f"Output saved to {output_file_path}")