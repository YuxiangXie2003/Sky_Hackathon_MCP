"""
streamlit_llm_travel_app.py
"""
import streamlit as st
from audiorecorder import audiorecorder
from io import BytesIO
import os, asyncio, logging
from pydub import AudioSegment
import streamlit.components.v1 as components
from dotenv import load_dotenv

# 你的音频转文字函数
from mcp_module import audio_to_text

# =========  LLM Bridge  ========= #
from mcp import StdioServerParameters
from mcp_llm_bridge.config import BridgeConfig, LLMConfig
from mcp_llm_bridge.bridge import BridgeManager

# ---------- Bridge 初始化（一次就够，放到 session_state 保持长连） ---------- #
def init_bridge():
    load_dotenv()                                     # 读取 .env 环境变量
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(project_root, "test.db")   # 如果用得到

    cfg = BridgeConfig(
        mcp_server_params=StdioServerParameters(
            command="python",
            args=["tool_hub.py"],
            env=None
        ),
        llm_config=LLMConfig(
            api_key = os.getenv("NVIDIA_API_KEY"),
            model="nvidia/llama-3.1-nemotron-ultra-253b-v1",
            base_url="https://integrate.api.nvidia.com/v1"
        ),
        # system_prompt=(
        #     "你是一个中文智能旅行助手，可以为用户提供城市出行攻略，包括：天气预报、"
        #     "景点推荐和地图定位。请根据用户输入的城市名，依次调用："
        #     "1. weather_search(city)  2. generate_static_map(city)。"
        #     "输出贴近小红书风格，按 Day1/Day2 的格式路线规划，并附地图提示。"
        # )
        system_prompt=(
            "你是一个中文智能旅行助手，可以为用户提供城市出行攻略，包括：天气预报、景点推荐和地图定位。"
            "请根据用户输入的城市名，依次调用以下工具："
            "1. `weather_search(city)`：查询该城市未来几天天气，并提取每日天气、气温、风力信息，整理成亲切自然的语气。"
            "2. `generate_static_map(city)`：查询该城市的著名景点，并生成地图"
            "输出要求："
            "- 使用中文，风格贴近“小红书”或微信公众号旅游博主文案，亲切有温度。"
            "- 每天的天气用 emoji 表示（如 ☀️、🌧️），换行展示，注意不要重复说“天气如下”等。"
            "- 将函数返回的景点分组，合理规划为每一天路线，结合城市特色安排顺序。注意不要添加函数返回的景点之外的景点"
            "- 添加贴心小贴士，如建议交通方式、雨具准备、游玩节奏。"
            "- 最后附上地图生成提示，例如：“🗺️地图已生成，在下方查看所有景点位置”。"
            "你不需要说明工具的使用过程，只输出整理后的内容即可，直接回复给用户。"
        )
    )
    return BridgeManager(cfg)

if "bridge" not in st.session_state:
    st.session_state.bridge = init_bridge()

# 同步包装：向 LLM 发送 user_input，拿到 response
def llm_chat_sync(user_input: str) -> str:
    async def _chat(prompt: str) -> str:
        async with st.session_state.bridge as bridge:
            return await bridge.process_message(prompt)
    return asyncio.run(_chat(user_input))

# =========  Streamlit UI  ========= #
st.set_page_config(page_title="旅图通——你的旅游规划智能体")
st.title("旅图通——你的旅游规划智能体")

# 大标题
st.markdown("## 选择输入方式")  # ‘##’ = H2 级标题，可根据需要改成 ###、#### …

# 把 radio 自带的 label 隐藏
input_method = st.radio(
    label="placeholder",              # 随便写
    options=["语音输入", "上传文件", "文本输入"],
    label_visibility="collapsed"      # 关键参数：隐藏标签
)

result_text, model_output = None, None

# 🎙️ 语音输入
if input_method == "语音输入":
    st.subheader("🎙️ 录音输入")
    audio_file_path = "audio/input.wav"
    os.makedirs("audio", exist_ok=True)
    if os.path.exists(audio_file_path):
        os.remove(audio_file_path)

    audio = audiorecorder("点击开始录音", "点击停止")
    if audio:
        # st.write(f"录音时长: {audio.duration_seconds:.2f} 秒")
        # st.write(f"最大音量: {audio.max_dBFS:.2f} dBFS")

        wav_io = BytesIO()
        audio.export(wav_io, format="wav"); wav_io.seek(0)
        st.audio(wav_io, format="audio/wav")

        audio.export(audio_file_path, format="wav")
        st.success("音频已保存")

        with st.spinner("🎤 正在识别..."):
            result_text = asyncio.run(audio_to_text(audio_file_path))

# 📁 文件上传
elif input_method == "上传文件":
    st.subheader("📁 上传音频文件")
    uploaded = st.file_uploader("上传 WAV 文件", type=["wav"])
    if uploaded:
        audio_file_path = "audio/uploaded.wav"
        with open(audio_file_path, "wb") as f:
            f.write(uploaded.read())
        st.audio(audio_file_path, format="audio/wav")
        if st.button("处理文件"):
            with st.spinner("🎤 正在识别..."):
                result_text = asyncio.run(audio_to_text(audio_file_path))
    else:
        st.button("请先上传文件", disabled=True)

# ✍️ 文本输入
else:
    st.subheader("✍️ 文本输入")
    text_input = st.text_area("请输入内容：", "上海")
    if st.button("处理文本"):
        if text_input.strip():
            result_text = text_input.strip()
        else:
            st.warning("文本不能为空")

# 🧠 LLM 处理与展示
if result_text:
    st.markdown("#### 🎧 你输入的内容是：")
    st.info(result_text)
    st.markdown("---")
    st.subheader("⏳ 正在生成旅行攻略 ...")
    with st.spinner("LLM 思考中..."):
        try:
            model_output = llm_chat_sync(result_text)
        except Exception as e:
            st.error(f"调用 LLM 出错：{e}")
            model_output = None

# ✅ 展示结果
if model_output:
    st.success("LLM 已生成👇")
    st.markdown(model_output)

    # 如果地图文件存在就展示
    if os.path.exists("landmarks_map.png"):
        st.image("landmarks_map.png", caption="🗺️ 旅行地图", use_container_width=True)

    # 自动朗读
    components.html(f"""
        <script>
            const msg = new SpeechSynthesisUtterance("{model_output}");
            window.speechSynthesis.speak(msg);
        </script>
    """, height=0)
