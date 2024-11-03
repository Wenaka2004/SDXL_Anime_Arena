# SDXL模型盲测竞技场
基于Gradio的SDXL模型盲测对比平台，用户可以通过界面生成不同模型的图像，对比并选择更优的模型，系统将根据用户的选择更新模型的评分，并展示模型的排行。

## 功能

- **历史对比**：从历史记录中抽取生成的图像，供用户再次对比选择。
  ![image](https://github.com/user-attachments/assets/22ca6ed6-2b8a-47bc-b38b-e283460983e1)
- - **模型对比**：随机选择两个模型，生成同一提示词的图像，供用户对比选择。可选图片生成方向与尺寸。
  ![a68776ca0af223cadb5c65b2325de8d1](https://github.com/user-attachments/assets/5cceb1c7-2786-4782-8aa9-b821f23dc04b)
- **角色ELO**：根据用户的选择，更新模型的ELO排名，展示当前模型的排行情况。
 ![71df7713d24c3d48623de4e7f709ffec](https://github.com/user-attachments/assets/9e7b69b4-3d0e-4f92-90a4-6be86499caae)
- **排行榜**：根据用户累计打分对模型进行排名，基于sqlite3。
- ![image](https://github.com/user-attachments/assets/3bc4b235-2125-437b-a37b-3a634b24c214)
- **安全措施**：防止恶意用户刷分刷榜/浪费算力，限制每三秒/二十秒获取/生成一次图像，必须进行打分后才能进行下次评分

## 安装与运行

### 依赖环境
- Python 3.x
- Gradio
- Requests
- PIL
- OpenCV
- SQLite3
- 其他详见 `requirements.txt`

### 安装步骤

1. 克隆本项目代码，安装依赖库：

   ```bash
   pip install -r requirements.txt
   ```

4. 确保已安装并配置好Stable Diffusion WebUI，并能够通过API访问。

## 使用方法

**配置**：
![83e685be6c913da5dd55541f631a188e](https://github.com/user-attachments/assets/2b30f9bd-8828-4517-8962-0f7f32e52c0b)
在main.py中将此处修改为你的webui地址

![ca711e660aaf26fcfa2bb2f7f9384b4c](https://github.com/user-attachments/assets/37f3aeaf-64e6-492c-b5d2-8dda3757a24a)
在generate_image_webui.py中将此处修改为参与评测的模型的列表


1. 运行 

main.py

   ```bash
   python main.py
   ```

2. 在浏览器中打开提供的Gradio链接，进入SDXL模型盲测竞技场界面。

3. 选择相应的标签页：

   - **历史对比**：对历史生成的图像进行对比。
   - **生成模式**：实时生成新的图像进行对比。
   - **角色ELO排行榜**：查看模型的评分排行。
   - **查看当前评分排行**：查看模型的得分情况。

4. 根据界面提示，选择角色，查看参考图像，生成并对比图像，选择您认为更好的模型，系统将自动记录并更新模型的评分。



## 注意事项

- 运行此项目需要搭建好的Stable Diffusion WebUI，并确保API可用。
- 请确保网络环境能够访问Danbooru API，以获取参考图像。
- **在WebUI中配置此项可大幅减少切换模型加载时间，但占用更多显存**
- ![image](https://github.com/user-attachments/assets/7aca44a7-b89a-4c32-a731-57b6cc715816)

