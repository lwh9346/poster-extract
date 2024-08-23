import gradio as gr
from dashscope import MultiModalConversation
import dashscope
import re
import os
import time


def extract_document_info(image):
    """Extract structured information from the document image."""
    messages = [
        {
            "role": "user",
            "content": [
                {"image": image},
                {
                    "text": "请你提取文档中的如下信息：1. Title 2. Bio 3. Abstract 4. location 5. date 6. authors\n时间的格式为2006-01-02T15:04:05+08:00，北京时间\n结果每一行为单独的一个属性，以冒号开头，中间不得换行，以下是一个例子：\nTitle: Example Title\nBio: Example Bio\nAbstract: Example Abstract\nlocation: Example location\ndate: Example date\nauthors: Example author1, Example author2, Example author3\n"
                },
            ],
        }
    ]
    responses = MultiModalConversation.call(
        model="qwen-vl-max", messages=messages, stream=True
    )
    result = ""
    for response in responses:
        result = response.get("output", {})["choices"][0]["message"]["content"][0][
            "text"
        ]
        yield None, process_result(result)
    yield render_hugo_template(result), process_result(result)



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
    try:
        os.makedirs("output", exist_ok=True)
    except Exception as e:
        print(e)
    filename = f"output/{time.strftime('%Y-%m-%d-%H-%M-%S',time.localtime(time.time()))}.md"
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
        if len(value) > 30:
            value = value[:15] + "..." + value[-15:]
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
        dashscope.api_key = file.read().strip()
    gradio_interface()
