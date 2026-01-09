# 使用官方Python镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装uv包管理器
RUN pip install --no-cache-dir uv

# 复制项目文件
COPY pyproject.toml ./
COPY main.py ./
COPY server.py ./
COPY clients/ ./clients/
COPY agent/ ./agent/

# 使用uv安装依赖
RUN uv pip install --system --no-cache -r pyproject.toml

# 暴露端口
EXPOSE 8000

# 健康检查端点需要在server.py中添加
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# 运行应用
CMD ["python", "main.py"]
