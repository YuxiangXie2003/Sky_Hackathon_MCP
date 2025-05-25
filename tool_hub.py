from typing import List, Dict, Any
import httpx
from mcp.server.fastmcp import FastMCP
import os
import requests
import json
import pathlib
from dotenv import load_dotenv

load_dotenv() 

# 初始化 FastMCP 服务器
mcp = FastMCP("travel_tools")
GAODE_API_KEY = os.getenv("AMAP_API_KEY")
if not GAODE_API_KEY:
    raise RuntimeError("未找到 AMAP_API_KEY！请在 .env 文件中添加，如：\nAMAP_API_KEY=xxxxxxxxxxxxxxxx")

json_path = pathlib.Path("landmarks.json")


async def fetch_landmarks(city: str, keyword: str = "著名景点", key: str = None) -> List[Dict[str, Any]]:
    if key is None:
        key = GAODE_API_KEY
    url = "https://restapi.amap.com/v3/place/text"
    params = {
        "key": key,
        "keywords": keyword,
        "city": city,
        "citylimit": "true",
        "extensions": "all",
        "offset": 10,
        "page": 1
    }
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") == "1" and data.get("info") == "OK":
                pois = data.get("pois", [])
                result = [
                    {
                        "name": poi.get("name"),
                        "address": poi.get("address"),
                        "location": poi.get("location")
                    }
                    for poi in pois if poi.get("location")
                ]
                json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
                return result
            return []
        except Exception:
            return []

# 计算中心点
def get_center(landmarks):
    lons, lats = zip(*(map(float, lm['location'].split(',')) for lm in landmarks))
    return f"{sum(lons)/len(lons):.6f},{sum(lats)/len(lats):.6f}"

@mcp.tool()
async def generate_static_map(city: str = "北京", keyword: str = "著名景点", api_key: str = None) -> str:
    """
    使用高德地图 API，自动搜索指定城市的景点并生成静态地图。

    参数:
    - city: 城市名，如 "北京"
    - keyword: 查询关键词，如 "著名景点"
    - api_key: 可选，API 密钥

    返回:
    - 地图生成结果，如 "地图图片已保存为 landmarks_map.png"
    """
    if api_key is None:
        api_key = GAODE_API_KEY

    landmarks = await fetch_landmarks(city, keyword)
    if not landmarks:
        return f"{city} 未找到有效景点信息，地图生成失败。"

    landmarks = landmarks[:10]  # 限制10个
    markers = '|'.join([f"mid,,{chr(65+i)}:{lm['location']}" for i, lm in enumerate(landmarks)])
    labels = '|'.join([f"{lm['name']},0,1,12,0xFF0000,0xFFFFFF:{lm['location']}" for lm in landmarks])
    center = get_center(landmarks)

    params = {
        'location': center,
        'zoom': '12',
        'size': '1024*768',
        'markers': markers,
        'labels': labels,
        'key': api_key
    }

    response = requests.get('https://restapi.amap.com/v3/staticmap', params=params)
    if response.status_code == 200:
        filename = 'landmarks_map.png'
        with open(filename, 'wb') as f:
            f.write(response.content)
        return f"🗺️地图已生成（{filename}），包含 {city} 的主要景点位置"
    else:
        return f"地图请求失败，状态码：{response.status_code}，内容：{response.text}"
    
@mcp.tool()
async def weather_search(city: str) -> str:
    """
    查询指定城市的未来几天天气预报。

    参数:
    - city: 城市名称，例如 "上海"

    返回:
    - 一段格式化好的天气信息字符串，包含日期、天气、风力等。
    
    示例调用:
        weather_search("上海")
    """
    url = "https://restapi.amap.com/v3/weather/weatherInfo"
    params = {
        "key": GAODE_API_KEY,
        "city": city,
        "extensions": "all",
        "output": "JSON"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        data = resp.json()
    if data.get("status") == "1" and "forecasts" in data:
        forecasts = data["forecasts"][0]
        city_name = forecasts["city"]
        report_time = forecasts["reporttime"]
        daily = forecasts["casts"]
        result = f"{city_name} 天气预报（{report_time}）:\n"
        for day in daily:
            result += (
                f"{day['date']} {day['week']} 白天:{day['dayweather']}({day['daytemp']}℃) "
                f"夜间:{day['nightweather']}({day['nighttemp']}℃) 风力:{day['daywind']}级\n"
            )
        return result
    else:
        return f"查询失败: {data.get('info', '未知错误')}"


if __name__ == "__main__":
    mcp.run(transport='stdio')