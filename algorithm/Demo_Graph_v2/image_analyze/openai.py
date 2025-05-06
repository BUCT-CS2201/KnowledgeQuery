import requests
from image_analyze.util import encode_image
from config import openai_config

def analyze_image(image, text):
    """图像分析

    image: streamlit UploadedFile 格式
    text: 文本
    """
    print("image_path:", image)
    
    # 获取图片类型
    image_type = image.type
    base64_image = encode_image(image)  # 进行图片编码
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_config.OPENAI_API_KEY}"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": text},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{image_type};base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }

    try:
        response = requests.post(f"{openai_config.base_url}/chat/completions", headers=headers, json=payload)
        response.raise_for_status()  # 如果响应有错误, 会抛出异常
        result = response.json()
        if 'choices' in result:
            return result['choices'][0]['message']['content']
        else:
            return "No result found."
    except requests.exceptions.RequestException as e:
        return f"Request failed: {e}"

if __name__ == '__main__':
    image = 'path_to_image'  # 替换为实际的图像文件路径
    text = 'What is this image about?'
    analyze_image(image, text)
