# AI-Alpha-Trader Dockerfile
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p data/agent_data logs

# 设置权限
RUN chmod +x agent_tools/*.py || true

# 暴露MCP服务端口
EXPOSE 8000 8001 8002 8003

# 默认命令
CMD ["python", "main.py"]
