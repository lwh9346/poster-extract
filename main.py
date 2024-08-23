import gradio as gr
from dashscope import MultiModalConversation
import dashscope
import re


def extract_document_info(image):
    """Extract structured information from the document image."""
    messages = [
        {
            "role": "user",
            "content": [
                {"image": image},
                {
                    "text": "请你提取文档中的如下信息：1. Bio 2. Abstract 3. 主讲人 4. 主办方 5. 会议时间（YYYY-MM-DD HH:MM，24小时制） 6. 会议地点"
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
        yield process_result(result)
    return process_result(result)



def process_result(text):
    info_dict = {}

    # 提取Bio信息
    bio_match = re.search(r"Bio:([^\n]*)", text, re.DOTALL)
    info_dict["Bio"] = bio_match.group(1).strip() if bio_match else None

    # 提取Abstract信息
    abstract_match = re.search(r"Abstract:([^\n]*)", text, re.DOTALL)
    info_dict["Abstract"] = abstract_match.group(1).strip() if abstract_match else None

    # 提取主讲人信息
    speaker_match = re.search(r"主讲人:([^\n]*)", text, re.DOTALL)
    info_dict["主讲人"] = speaker_match.group(1).strip() if speaker_match else None

    # 提取主办方信息
    organizer_match = re.search(r"主办方:([^\n]*)", text, re.DOTALL)
    info_dict["主办方"] = organizer_match.group(1).strip() if organizer_match else None

    # 提取会议时间信息
    time_match = re.search(r"会议时间:([^\n]*)", text, re.DOTALL)
    info_dict["会议时间"] = time_match.group(1).strip() if time_match else None

    # 提取会议地点信息
    location_match = re.search(r"会议地点:([^\n]*)", text, re.DOTALL)
    info_dict["会议地点"] = location_match.group(1).strip() if location_match else None

    markdown_text = ""
    for key, value in info_dict.items():
        if value is not None:
            markdown_text += f"### {key}\n{value}\n"
        else:
            markdown_text += f"### {key}\n等待中……\n"
    return markdown_text



def gradio_interface():
    """Create a Gradio interface for the document extraction tool."""
    inputs = gr.Image(type="filepath", label="上传文档图片")
    outputs = gr.Markdown(label="提取的信息")

    interface = gr.Interface(
        fn=extract_document_info,
        inputs=inputs,
        outputs=outputs,
        title="文档结构化信息提取工具",
        description="上传文档图片，提取以下信息：1. Bio 2. Abstract 3. 主讲人 4. 主办方 5. 会议时间（YYYY-MM-DD HH:MM，24小时制） 6. 会议地点",
    )
    interface.launch()

if __name__ == "__main__":
    with open("API_KEY.txt", "r") as file:
        dashscope.api_key = file.read().strip()
    gradio_interface()