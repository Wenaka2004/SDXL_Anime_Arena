from PIL import Image
from PIL.PngImagePlugin import PngImageFile

def get_png_parameters(file_path):
    # 打开 PNG 文件
    with Image.open(file_path) as img:
        # 确保图像是 PNG 格式
        if not isinstance(img, PngImageFile):
            raise ValueError("文件不是 PNG 格式")
        
        # 获取 PNG 文件的元数据
        metadata = img.info
        
        # 提取并返回 'parameters' 内容
        parameters = metadata.get('parameters', None)
        
        # 只保留 'parameters' 内容
        if parameters:
            parameters = parameters.split('Negative prompt:')[0].strip()
        
        return parameters

# 示例使用
if __name__ == '__main__':
    file_path = 'images/checkpoint-e8_s253312.safetensors/5d8e8e1c.png'
    parameters = get_png_parameters(file_path)
    print(parameters)