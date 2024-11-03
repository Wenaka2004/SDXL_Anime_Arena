import gradio as gr
import random
import sqlite3
import os
import time
from PIL import Image
from PIL.PngImagePlugin import PngImageFile
from generate_image_webui import generate_image_webui
from database import init_database
from dan_api import search_images
import json
import requests
import io

webui_url="http://192.168.31.142:7860"

init_database()

with open('character_list.json', 'r', encoding='utf-8') as f:
    character_data = json.load(f)

character_list,character_string_list = [],[]
for character in character_data:
    character_list.append(character['character_tag'])
    character_string_list.append(character['character_str_tag'])

models = [name for name in os.listdir('images') if os.path.isdir(os.path.join('images', name))]

# 提取图像中的 prompt
def get_png_parameters(file_path):
    with Image.open(file_path) as img:
        if not isinstance(img, PngImageFile):
            raise ValueError("文件不是 PNG 格式")
        metadata = img.info
        parameters = metadata.get('parameters', None)
        if parameters:
            prompt = parameters.split('Negative prompt:')[0].strip()
            return prompt
        else:
            return None

def generate_images(prompt, width, height):
    selected_models = random.sample(models, 2)
    model1, model2 = selected_models[0], selected_models[1]
    image1 = generate_image_webui(webui_url, prompt, model1, width=width, height=height)
    image2 = generate_image_webui(webui_url, prompt, model2, width=width, height=height)
    return image1, image2, model1, model2

def select_images_from_history(model1, model2):
    image_folder1 = os.path.join('images', model1)
    image_folder2 = os.path.join('images', model2)
    filenames1 = set(f for f in os.listdir(image_folder1) if os.path.isfile(os.path.join(image_folder1, f)))
    filenames2 = set(f for f in os.listdir(image_folder2) if os.path.isfile(os.path.join(image_folder2, f)))
    common_filenames = filenames1.intersection(filenames2)
    if not common_filenames:
        return None, None, None, None, "没有找到可供比较的历史图像，请生成更多图像。", None
    filename = random.choice(list(common_filenames))
    image1_path = os.path.join('images', model1, filename)
    image2_path = os.path.join('images', model2, filename)
    image1 = Image.open(image1_path)
    image2 = Image.open(image2_path)
    prompt = get_png_parameters(image1_path)
    return image1, image2, model1, model2, "", prompt

def update_database(choice, model1, model2):
    conn = sqlite3.connect('models.db')
    cursor = conn.cursor()
    if choice == "模型 1":
        cursor.execute('UPDATE models SET draw_count = draw_count + 1, win_count = win_count + 1 WHERE name = ?', (model1,))
        cursor.execute('UPDATE models SET draw_count = draw_count + 1 WHERE name = ?', (model2,))
    elif choice == "模型 2":
        cursor.execute('UPDATE models SET draw_count = draw_count + 1, win_count = win_count + 1 WHERE name = ?', (model2,))
        cursor.execute('UPDATE models SET draw_count = draw_count + 1 WHERE name = ?', (model1,))
    elif choice == "平局":
        cursor.execute('UPDATE models SET draw_count = draw_count + 1, tie_count = tie_count + 1 WHERE name = ?', (model1,))
        cursor.execute('UPDATE models SET draw_count = draw_count + 1, tie_count = tie_count + 1 WHERE name = ?', (model2,))
    elif choice == "两个都很烂":
        cursor.execute('UPDATE models SET draw_count = draw_count + 1 WHERE name = ?', (model1,))
        cursor.execute('UPDATE models SET draw_count = draw_count + 1 WHERE name = ?', (model2,))
    conn.commit()
    conn.close()
    if choice == "模型 1":
        return f"您选择了{model1}生成的图像，另一张图像由{model2}生成。结果已记录，谢谢您的参与！"
    elif choice == "模型 2":
        return f"您选择了{model2}生成的图像，另一张图像由{model1}生成。结果已记录，谢谢您的参与！"
    elif choice == "平局":
        return f"您认为这两张图像都不错。他们分别由{model1}和{model2}生成。他们将都得到小幅加分。结果已记录，谢谢您的参与！"
    elif choice == "两个都很烂":
        return f"您认为这两张图像都很烂。他们分别由{model1}和{model2}生成。他们不会得到加分。结果已记录，谢谢您的参与！"

def get_rankings():
    conn = sqlite3.connect('models.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, draw_count, win_count, tie_count FROM models ORDER BY win_count DESC')
    data = cursor.fetchall()
    conn.close()
    return data

# 添加新函数处理角色选择
def on_character_select(selected_character):
    if not selected_character:
        return [None, None, None, "请选择一个角色"]
    
    # 使用Danbooru API获取参考图片
    ref_images_urls = search_images(selected_character, limit=3)
    if not ref_images_urls or len(ref_images_urls) < 3:
        return [None, None, None, "无法获取参考图片"]

    return [ref_images_urls[0], ref_images_urls[1], ref_images_urls[2], ""]

# 创建 Gradio 界面
with gr.Blocks() as demo:
    gr.Markdown("# SDXL 模型盲测竞技场")

    with gr.Tab("历史对比"):
        with gr.Column():
            refresh_btn = gr.Button("刷新图像")
            prompt_display = gr.Markdown(value="", visible=True)
            with gr.Row():
                image_output1_hist = gr.Image(label="模型 1", height=350, width=250)
                image_output2_hist = gr.Image(label="模型 2", height=350, width=250)
            result_hist = gr.Textbox(label="提示信息", interactive=False)
            with gr.Row():
                choice_btn1_hist = gr.Button("我更喜欢模型 1")
                choice_btn2_hist = gr.Button("我更喜欢模型 2")
                tie_btn_hist = gr.Button("两个都不错")
                bad_btn_hist = gr.Button("两个都很烂")  # 新增按钮

            # 用于保存模型名称，供更新数据库时使用
            model1_name_hist = gr.State()
            model2_name_hist = gr.State()
            rated_hist = gr.State(True)  # 初始为 True，允许首次刷新
            last_refresh_hist = gr.State(0)  # 记录上次刷新时间

        # 修改后的 on_refresh 函数
        def on_refresh(rated, last_refresh, model1, model2):
            current_time = time.time()
            if (current_time - last_refresh) < 3:
                return [gr.update(), gr.update(), gr.update(), gr.update(), 
                        "刷新过于频繁，只允许每三秒刷新一次。", gr.update(), last_refresh, rated]
            if not rated:
                return [gr.update(), gr.update(), gr.update(), gr.update(), 
                        "请先对当前图像进行评分。", gr.update(), last_refresh, rated]
            
            # 每次刷新时随机选择两个新的模型
            selected_models = random.sample(models, 2)
            model1, model2 = selected_models[0], selected_models[1]
    
            img1, img2, model1_new, model2_new, msg, prompt = select_images_from_history(model1, model2)
            if prompt:
                prompt_display_value = f"**提示词（Prompt）：** {prompt}"
            else:
                prompt_display_value = "**未在元数据中找到有效提示词**"
            return [img1, img2, model1_new, model2_new, msg, prompt_display_value, current_time, False]  # 将 rated_hist 重置为 False

        # 修改 refresh_btn.click 的输出列表，添加 rated_hist
        refresh_btn.click(
            fn=on_refresh,
            inputs=[rated_hist, last_refresh_hist, model1_name_hist, model2_name_hist],
            outputs=[image_output1_hist, image_output2_hist, model1_name_hist, model2_name_hist, result_hist, prompt_display, last_refresh_hist, rated_hist]
        )

        # 确保“生成模式”中的类似逻辑正确
        # on_generate 函数已经正确设置 rated_gen 为 False，确保 on_choice_gen 正确设置为 True

        # 如果需要对“生成模式”中的状态进行类似的检查，也可以进行相应的修改

        def on_choice(choice, model1, model2, already_rated):
            if already_rated:
                return "您已对当前图像进行评分，重复评分无效。", already_rated
            msg = update_database(choice, model1, model2)
            return msg, True  # 设置 rated 状态为 True

        choice_btn1_hist.click(
            fn=lambda m1, m2, ar: on_choice("模型 1", m1, m2, ar),
            inputs=[model1_name_hist, model2_name_hist, rated_hist],
            outputs=[result_hist, rated_hist]
        )

        choice_btn2_hist.click(
            fn=lambda m1, m2, ar: on_choice("模型 2", m1, m2, ar),
            inputs=[model1_name_hist, model2_name_hist, rated_hist],
            outputs=[result_hist, rated_hist]
        )

        tie_btn_hist.click(
            fn=lambda m1, m2, ar: on_choice("平局", m1, m2, ar),
            inputs=[model1_name_hist, model2_name_hist, rated_hist],
            outputs=[result_hist, rated_hist]
        )

        bad_btn_hist.click(
            fn=lambda m1, m2, ar: on_choice("两个都很烂", m1, m2, ar),
            inputs=[model1_name_hist, model2_name_hist, rated_hist],
            outputs=[result_hist, rated_hist]
        )

    with gr.Tab("生成模式"):
        with gr.Row():
            prompt_input = gr.Textbox(label="请输入提示词", scale=4)
            with gr.Column(scale=1):
                submit_btn = gr.Button("生成图像", size="sm", variant="primary")
                with gr.Row():
                    resolution = gr.Radio(
                        choices=["832x1216", "1024x1536"],
                        value="832x1216",
                        label="分辨率",
                        interactive=True
                    )
                    orientation = gr.Radio(
                        choices=["竖图", "横图"],
                        value="竖图",
                        label="图像方向",
                        interactive=True
                    )

        with gr.Row():
            image_output1_gen = gr.Image(label="模型 1", height=350, width=250)
            image_output2_gen = gr.Image(label="模型 2", height=350, width=250)

        result_gen = gr.Textbox(label="提示信息", interactive=False)

        with gr.Row():
            choice_btn1_gen = gr.Button("我更喜欢模型 1")
            choice_btn2_gen = gr.Button("我更喜欢模型 2")
            tie_btn_gen = gr.Button("两个都不错")
            bad_btn_gen = gr.Button("两个都很烂")  # 新增按钮

        # 用于保存模型名称，供更新数据库时使用
        model1_name_gen = gr.State()
        model2_name_gen = gr.State()
        rated_gen = gr.State(True)  # 初始为 True，允许首次生成
        last_generate_gen = gr.State(0)  # 记录上次生成时间

        def on_generate(prompt, resolution, orientation, rated, last_generate):
            current_time = time.time()
            if current_time - last_generate < 20:
                return [
                    gr.update(), gr.update(), gr.update(), gr.update(),
                    "生成过于频繁，只允许每20秒生成一次。",
                    rated, last_generate
                ]
            if not rated:
                return [
                    gr.update(), gr.update(), gr.update(), gr.update(),
                    "请先对当前图像进行评分。",
                    rated, last_generate
                ]
            width, height = map(int, resolution.split('x'))
            if orientation == "横图":
                width, height = height, width
            img1, img2, model1, model2 = generate_images(prompt, width, height)
            return [
                img1, img2, model1, model2,
                "", False, current_time  # 重置 rated 状态为 False
            ]

        def on_choice_gen(choice, model1, model2, already_rated):
            if already_rated:
                return "您已对当前图像进行评分，重复评分无效。", already_rated
            msg = update_database(choice, model1, model2)
            return msg, True  # 设置 rated 状态为 True

        submit_btn.click(
            fn=on_generate,
            inputs=[prompt_input, resolution, orientation, rated_gen, last_generate_gen],
            outputs=[
                image_output1_gen, image_output2_gen,
                model1_name_gen, model2_name_gen,
                result_gen, rated_gen, last_generate_gen
            ]
        )

        choice_btn1_gen.click(
            fn=lambda m1, m2, ar: on_choice_gen("模型 1", m1, m2, ar),
            inputs=[model1_name_gen, model2_name_gen, rated_gen],
            outputs=[result_gen, rated_gen]
        )

        choice_btn2_gen.click(
            fn=lambda m1, m2, ar: on_choice_gen("模型 2", m1, m2, ar),
            inputs=[model1_name_gen, model2_name_gen, rated_gen],
            outputs=[result_gen, rated_gen]
        )

        tie_btn_gen.click(
            fn=lambda m1, m2, ar: on_choice_gen("平局", m1, m2, ar),
            inputs=[model1_name_gen, model2_name_gen, rated_gen],
            outputs=[result_gen, rated_gen]
        )

        bad_btn_gen.click(
            fn=lambda m1, m2, ar: on_choice_gen("两个都很烂", m1, m2, ar),
            inputs=[model1_name_gen, model2_name_gen, rated_gen],
            outputs=[result_gen, rated_gen]
        )

    with gr.Tab("角色elo排行榜"):
        # 创建角色ELO排名区域
        with gr.Column():
            with gr.Row():
                # 角色下拉菜单（可搜索）
                character_dropdown = gr.Dropdown(character_list, label="选择角色", interactive=True, multiselect=False, type="value")
                # 添加“是否带上发色瞳色等细节”选项
                include_details_radio = gr.Radio(choices=['否', '是'], value='否', label='是否带上发色瞳色等细节', interactive=True)
            with gr.Row():
                # 展示参考图片
                ref_image1 = gr.Image(label="参考图1", height=200)
                ref_image2 = gr.Image(label="参考图2", height=200)
                ref_image3 = gr.Image(label="参考图3", height=200)
            with gr.Row():
                # AI生成的图片
                char_image1 = gr.Image(label="模型1生成", height=350)
                char_image2 = gr.Image(label="模型2生成", height=350)
            result_char = gr.Textbox(label="评分结果", interactive=False)
            with gr.Row():
                char_btn1 = gr.Button("模型1更准确")
                char_btn2 = gr.Button("模型2更准确")
                char_tie_btn = gr.Button("难分伯仲")
                char_bad_btn = gr.Button("都不准确")
            # 存储当前比较的模型信息
            char_model1 = gr.State()
            char_model2 = gr.State()
            char_rated = gr.State(True)
            char_last_gen = gr.State(0)

            # 生成按钮
            char_generate_btn = gr.Button("生成图像")

            def on_char_generate(selected_character, include_details, rated, last_gen):
                if not selected_character:
                    return [None, None, "请先选择一个角色", None, None, last_gen, rated]
                if not rated:
                    return [None, None, "请对当前生成结果进行评分", None, None, last_gen, rated]

                current_time = time.time()
                if current_time - last_gen < 20:
                    return [None, None, "请等待20秒后再次生成", None, None, last_gen, rated]

                # 获取角色索引
                try:
                    char_index = character_list.index(selected_character)
                except ValueError:
                    return [None, None, "所选角色无效", None, None, last_gen, rated]
                
                # 根据是否带上细节生成prompt
                if include_details == '是':
                    character_prompt = character_string_list[char_index]
                else:
                    character_prompt = selected_character

                # 随机选择两个模型
                selected_models = random.sample(models, 2)

                # 生成prompt
                prompt = f"masterpiece, best quality, newest, absurdres, highres, {character_prompt}"

                # 使用随机模型生成图像
                image1 = generate_image_webui('http://192.168.31.142:7860', prompt, selected_models[0])
                image2 = generate_image_webui('http://192.168.31.142:7860', prompt, selected_models[1])

                last_gen = current_time
                rated = False

                return [image1, image2, "", selected_models[0], selected_models[1], last_gen, rated]

            char_generate_btn.click(
                fn=on_char_generate,
                inputs=[character_dropdown, include_details_radio, char_rated, char_last_gen],
                outputs=[char_image1, char_image2, result_char, char_model1, char_model2, char_last_gen, char_rated]
            )

            def on_char_choice(choice, model1, model2, already_rated):
                if already_rated:
                    return "您已对当前生成结果进行评分", already_rated
                msg = update_database(choice, model1, model2)
                return msg, True

            char_btn1.click(
                fn=lambda m1, m2, ar: on_char_choice("模型 1", m1, m2, ar),
                inputs=[char_model1, char_model2, char_rated],
                outputs=[result_char, char_rated]
            )

            char_btn2.click(
                fn=lambda m1, m2, ar: on_char_choice("模型 2", m1, m2, ar),
                inputs=[char_model1, char_model2, char_rated],
                outputs=[result_char, char_rated]
            )

            char_tie_btn.click(
                fn=lambda m1, m2, ar: on_char_choice("平局", m1, m2, ar),
                inputs=[char_model1, char_model2, char_rated],
                outputs=[result_char, char_rated]
            )

            char_bad_btn.click(
                fn=lambda m1, m2, ar: on_char_choice("两个都很烂", m1, m2, ar),
                inputs=[char_model1, char_model2, char_rated],
                outputs=[result_char, char_rated]
            )

            # 在UI代码中添加角色选择的事件处理
            character_dropdown.change(
                fn=on_character_select,
                inputs=[character_dropdown],
                outputs=[ref_image1, ref_image2, ref_image3, result_char]
            )

    
    
    with gr.Tab("查看当前评分排行"):
        rankingsData = get_rankings()
        rankings = gr.Dataframe(value=rankingsData, headers=["模型名称", "对战次数", "胜利次数", "平局次数"], interactive=False)

        def refresh_rankings():
            data = get_rankings()
            return data

        refresh_btn_rank = gr.Button("刷新排行")
        refresh_btn_rank.click(fn=refresh_rankings, outputs=rankings)

    demo.launch(server_name="0.0.0.0", server_port=7860,share=True)