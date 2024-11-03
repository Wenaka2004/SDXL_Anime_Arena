import requests
import json
import os
import base64
import io
import cv2
from PIL import Image
import hashlib
from PIL import PngImagePlugin

model_names=["checkpoint-e8_s253312.safetensors","noobaiXLNAIXL_epsilonPred075.safetensors"]

# 自动在images文件夹下生成对应名字的子文件夹
for model_name in model_names:
    model_folder = f'images/{model_name}'
    if not os.path.exists(model_folder):
        os.makedirs(model_folder)

def generate_filename(input_string):
    # 使用 SHA-256 哈希函数
    hash_object = hashlib.sha256(input_string.encode())
    # 获取哈希值的十六进制表示
    hex_dig = hash_object.hexdigest()
    # 截取前 32 个字符作为文件名
    filename = hex_dig[:32]
    return filename
def generate_image_webui(url, prompt, model, steps=20, width=1024, height=1536, clip_skip=1):
    set_model_payload={"sd_model_checkpoint": f"{model}"}
    payload = {
        "prompt": prompt,
        "negative_prompt": "lowres, worst quality, bad quality, bad hands, very displeasing, extra digit, fewer digits, jpeg, pregnant, artifacts, signature, username, reference, mutated, lineup, manga, comic, disembodied, turnaround, 2koma, 4koma, monster, cropped, amputee, text, bad foreshortening, what, guro, logo, bad anatomy, bad perspective, bad proportions, artistic error, anatomical nonsense, amateur, out of frame, multiple views",
        "steps": steps,
        "width": width,
        "height": height,
        "cfg_scale": 7,
        "sampler_index": "Euler a",
        "override_settings": {
            "CLIP_stop_at_last_layers": clip_skip
        }
    }
    #设置模型名称
    newurl=f"{url}/sdapi/v1/options"
    setmodel = requests.post(url=newurl, json=set_model_payload)
    print("模型已设置为", model)
    #生成图像
    filename = generate_filename(prompt)
    newurl = f"{url}/sdapi/v1/txt2img"
    payload["prompt"] = prompt
    print(f"开始生成:{filename}")
    response = requests.post(url=newurl, json=payload)
    
    
    if response.status_code == 200:
        print("Success")
        r = response.json()
        info = json.loads(r['info'])  # 将 info 转换为字典
        print(info['infotexts'][0])
        image_data = base64.b64decode(r['images'][0])
        image = Image.open(io.BytesIO(image_data))
        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add_text("parameters", info['infotexts'][0])
        #如果已经存在同名文件，将新的文件名加上_1,_2等类似后缀
        if os.path.exists(f'images/{model}/{filename}.png'):
            i = 1
            while os.path.exists(f'images/{model}/{filename}_{i}.png'):
                i += 1
            filename = f"{filename}_{i}"
        image.save(f'images/{model}/{filename}.png', pnginfo=pnginfo)
        print("图像文件已保存至", f'images/{model}/{filename}.png')
        return image
    else:
        print(f"Error: {response.status_code}")
        return None


