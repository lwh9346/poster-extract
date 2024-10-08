import gradio as gr
import openai
import os
import time
from PIL import Image
import paddleocr
import json


ocr = paddleocr.PaddleOCR(lang="ch")


def extract_document_info(image):
    """Extract structured information from the document image."""
    prompt = (
        "请你提取文档中的如下信息：1. Title 2. Bio 3. Abstract 4. Location 5. Date 6. Authors(报告人，可能只有一个)\n"
        "时间的格式为2006-01-02T15:04:05+08:00，北京时间\n"
        "结果每一行为单独的一个属性，以英文冒号开头，中间不得换行\n"
        "你应该修复一些可能存在的格式错误，如在英文中使用中文标点等\n"
        "报告的地点可以给出中文，大概率是北京市区内的地点\n"
        "以下是一个例子：\n"
        "Title: Example Title\n"
        "Bio: Example Bio\n"
        "Abstract: Example Abstract\n"
        "Location: Example location\n"
        "Date: Example date\n"
        "Authors: Example author1, Example author2, Example author3\n"
        "下面是文档的OCR结果，请你根据结果提取内容：\n"
        f"{ocr_image(preprocess_image(image))}\n"
    )
    responses = openai.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": "你是一个负责从OCR结果中提取关键信息的AI助手，你除了用户要求的格式内容外，不会输出任何多余语句",
            },
            {"role": "user", "content": prompt},
        ],
        stream=True,
        temperature=0,
    )
    result = ""
    for response in responses:
        result += response.choices[0].delta.content
        yield None, process_result(result)
    yield render_hugo_template(result), process_result(result)


def preprocess_image(image_path):
    """预处理图像，输入为图像的路径，要求在保持长宽比的情况下，将图像缩放到70万像素（不放大），然后拉伸长宽到最近的28的倍数，以上处理均使用bicubic，最后将图像保存到output文件夹里的以时间命名的png文件中，返回该文件路径"""
    img = Image.open(image_path)
    width, height = img.size
    target_pixels = 700000
    ratio = (target_pixels / (width * height)) ** 0.5
    new_width = int(width * ratio)
    new_height = int(height * ratio)
    new_width = new_width // 28 * 28
    new_height = new_height // 28 * 28
    img = img.resize((new_width, new_height), Image.Resampling.BICUBIC)

    output_folder = "output"
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(
        output_folder,
        f"{time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime(time.time()))}.png",
    )
    img.save(output_path)

    return output_path


def ocr_image(image_path):
    result = ocr.ocr(image_path)
    json_result = []
    for line in result[0]:
        json_result.append(
            {
                "text": line[1],
                "bbox": [line[0][0], line[0][2]],
            }
        )
    return json.dumps(json_result, ensure_ascii=False)


def render_hugo_template(text):
    info_dict = {}

    for line in text.split("\n"):
        line = line.strip()
        if line:
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                info_dict[key] = value
    with open("hugo_template.md", "r", encoding="utf-8") as file:
        template = file.read()
    for key, value in info_dict.items():
        template = template.replace("{{" + key.lower() + "}}", value)
    os.makedirs("output", exist_ok=True)
    filename = (
        f"output/{time.strftime('%Y-%m-%d-%H-%M-%S',time.localtime(time.time()))}.md"
    )
    with open(filename, "w", encoding="utf-8") as file:
        file.write(template)
    return filename


def process_result(text):
    info_dict = {}

    for line in text.split("\n"):
        line = line.strip()
        if line:
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                info_dict[key] = value

    markdown_text = "## 提取信息预览\n"
    for key, value in info_dict.items():
        markdown_text += f"### {key}\n{value}\n"
    return markdown_text


def gradio_interface():
    """Create a Gradio interface for the document extraction tool."""
    inputs = gr.Image(type="filepath", label="上传文档图片")
    outputs = [gr.File(label="下载Hugo页面"), gr.Markdown(label="提取的信息")]

    interface = gr.Interface(
        fn=extract_document_info,
        inputs=inputs,
        outputs=outputs,
        title="文档结构化信息提取工具",
        description="上传文档图片，提取信息，自动生成hugo页面",
    )
    interface.launch()


if __name__ == "__main__":
    with open("API_KEY.txt", "r") as file:
        openai.api_key = file.read().strip()
    openai.base_url = "https://api.deepseek.com"
    gradio_interface()
