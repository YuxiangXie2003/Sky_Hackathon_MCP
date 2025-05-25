import base64
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
INVOKE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

if not NVIDIA_API_KEY:
    raise ValueError("❌ NVIDIA_API_KEY 未设置或为空，请检查 .env 文件或代码配置。")

async def audio_to_text(audio_file_path: str) -> str:
    """
    将指定音频文件转为文本（调用 NVIDIA API）。

    Args:
        audio_file_path (str): 本地音频文件路径。

    Returns:
        str: 转录文本或错误信息。
    """
    try:
        with open(audio_file_path, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode()

        if len(audio_b64) >= 1_800_000:
            return "Error: 音频文件过大（应小于 1.8MB）"

        headers = {
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Accept": "application/json"
        }

        payload = {
            "model": 'microsoft/phi-4-multimodal-instruct',
            "messages": [
                {
                    "role": "user",
                    "content": f'Transcribe the spoken content.<audio src="data:audio/wav;base64,{audio_b64}" />'
                }
            ],
            "max_tokens": 512,
            "temperature": 0.10,
            "top_p": 0.70,
            "stream": False
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(INVOKE_URL, headers=headers, json=payload)
            response.raise_for_status()

        result = response.json()
        if (
            "choices" in result and len(result["choices"]) > 0 and
            "message" in result["choices"][0] and "content" in result["choices"][0]["message"]
        ):
            return result["choices"][0]["message"]["content"]
        else:
            return f"Error: 无法从响应中提取文本，响应内容: {result}"

    except FileNotFoundError:
        return f"Error: 文件不存在：{audio_file_path}"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP 错误 {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"Error: 未知错误: {str(e)}"
