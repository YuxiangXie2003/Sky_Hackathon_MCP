from typing import List, Dict, Any
import httpx
from mcp.server.fastmcp import FastMCP
import os
import requests
import json
import pathlib

# 初始化 FastMCP 服务器
mcp = FastMCP("travel_tools")
GAODE_API_KEY = os.getenv("AMAP_API_KEY", "05e0edda24d162d5d17551c630fd4755")

json_path = pathlib.Path("landmarks.json")

# @mcp.tool()
# async def amap_search(city: str, keyword: str, key: str = None) -> List[Dict[str, Any]]:
    # """
    # 使用高德地图API查询某城市的地点信息。

    # 参数:
    # - city: 城市名，如 "北京"
    # - keyword: 查询关键词，如 "博物馆"、"著名景点"
    # - key: 可选，自定义高德地图 API 密钥，默认使用系统内置值

    # 返回:
    # - 景点信息列表，每项包括:
    #   {
    #     "name": "景点名称",
    #     "address": "地址",
    #     "location": "经纬度字符串，如 '116.397128,39.916527'"
    #   }

    # 示例调用:
    #     amap_search("北京", "著名景点")
    # """
#     if key is None:
#         key = GAODE_API_KEY
#     url = "https://restapi.amap.com/v3/place/text"
#     params = {
#         "key": key,
#         "keywords": keyword,
#         "city": city,
#         "citylimit": "true",
#         "extensions": "all",
#         "offset": 10,
#         "page": 1
#     }
#     async with httpx.AsyncClient() as client:
#         try:
#             resp = await client.get(url, params=params, timeout=10)
#             resp.raise_for_status()
#             data = resp.json()
#             if data.get("status") == "1" and data.get("info") == "OK":
#                 pois = data.get("pois", [])
#                 result = [
#                     {
#                         "name": poi.get("name"),
#                         "address": poi.get("address"),
#                         "location": poi.get("location")
#                     }
#                     for poi in pois if poi.get("location")
#                 ]
#                 with open(json_path, "w", encoding="utf-8") as f:
#                     json.dump(result, f, ensure_ascii=False, indent=2)
#                 return result
#             else:
#                 return []
#         except Exception:
#             return []

# def get_center(landmarks):
#     """计算所有景点的经纬度平均值作为地图中心点"""
#     lons, lats = zip(*(map(float, lm['location'].split(',')) for lm in landmarks))
#     return f"{sum(lons)/len(lons):.6f},{sum(lats)/len(lats):.6f}"

# @mcp.tool()
# def generate_static_map(landmarks: List[Dict[str, Any]], api_key: str = None) -> str:
#     """
#     生成一张带有景点标注的静态地图图片。

#     参数:
#     - landmarks: 景点信息列表（必须包含 'name' 和 'location'），可以是从 amap_search 得到的返回值（最多10个）。
#     - api_key: 可选，传入自定义高德地图 API 密钥。

#     返回:
#     - 成功时，返回图片保存信息字符串，例如 "地图图片已保存为 landmarks_map.png"
#     - 失败时，返回错误提示信息。

#     示例调用:
#         generate_static_map([{ "name": "故宫", "location": "116.397128,39.916527" }])
#     """
#     # 兼容字符串输入
#     if isinstance(landmarks, str):
#         try:
#             landmarks = json.loads(landmarks)
#         except Exception:
#             # 尝试读取本地缓存
#             if json_path.exists():
#                 try:
#                     with open(json_path, "r", encoding="utf-8") as f:
#                         landmarks = json.load(f)
#                 except Exception:
#                     return "landmarks参数格式错误，且读取缓存失败。"
#             else:
#                 return "landmarks参数格式错误，且找不到缓存。"
#     if api_key is None:
#         api_key = GAODE_API_KEY
#     if not landmarks or not isinstance(landmarks, list):
#         return "未获取到景点信息，无法生成地图。"
#     markers = '|'.join([f"mid,,{chr(65+i)}:{lm['location']}" for i, lm in enumerate(landmarks)])
#     labels = '|'.join([f"{lm['name']},0,1,12,0xFF0000,0xFFFFFF:{lm['location']}" for lm in landmarks])
#     # 用所有景点的平均经纬度作为地图中心
#     center = get_center(landmarks)
#     params = {
#         'location': center,
#         'zoom': '12',
#         'size': '1024*768',
#         'markers': markers,
#         'labels': labels,
#         'key': api_key
#     }
#     response = requests.get('https://restapi.amap.com/v3/staticmap', params=params)
#     if response.status_code == 200:
#         filename = 'landmarks_map.png'
#         with open(filename, 'wb') as f:
#             f.write(response.content)
#         return f"地图图片已保存为 {filename}"
#     else:
#         return f"请求失败，状态码：{response.status_code}, 响应内容：{response.text}"


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
        return {
            "landmarks": landmarks,
            "map_path": filename,
            "message": f"🗺️地图已生成（{filename}），包含 {city} 的主要景点位置"
        }
    else:
        return {
            "landmarks": [],
            "map_path": None,
            "message": f"地图请求失败，状态码：{response.status_code}，内容：{response.text}"
        }
    

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

# @mcp.tool()
# async def travel_plan(city: str) -> str: #最多标注10个景点
#     """
#     一站式旅行助手：查询天气，推荐并查询景点，生成地图
#     """
#     # 1. 查询天气
#     weather = await weather_search(city)
#     # 2. 推荐景点关键词（可根据天气自定义，这里简单用“著名景点”）
#     keyword = "著名景点"
#     # 3. 查询景点详细信息
#     landmarks = await amap_search(city, keyword)
#     if not landmarks:
#         return f"{weather}\n未找到相关景点信息。"
#     # 4. 生成地图
#     map_result = generate_static_map(landmarks)
#     # 5. 汇总返回
#     result = f"{weather}\n为您推荐的景点有：\n"
#     for lm in landmarks:
#         result += f"- {lm['name']}（地址：{lm['address']}，坐标：{lm['location']}）\n"
#     result += f"\n{map_result}"
#     return result

if __name__ == "__main__":
    mcp.run(transport='stdio')