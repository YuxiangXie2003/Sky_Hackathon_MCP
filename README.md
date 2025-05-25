# 🛫 旅行规划MCP

## 项目描述

本项目是一个用于旅行规划的智能体，用户可以……

## 项目亮点

- jetson
- 模块化，方便扩展
- 网页采用markdown，可扩展性强
- ……

## 配置教程

克隆本仓库后，执行下述指令安装所需要的依赖：

```bash
conda create -n mcp python=3.12
conda activate mcp
pip install -r requirements.txt
pip install streamlit streamlit-audiorecorder
```

然后运行部署脚本：

```bash
sh setup.sh
```

通过下述指令启动服务：

```bash
streamlit run mcp_main.py
```

通过`http://localhost:8501`可以访问网页

## 功能说明

支持语音输入或者文本输入
