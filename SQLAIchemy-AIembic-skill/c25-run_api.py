import uvicorn

from api import app


if __name__ == "__main__":
    # 直接加载项目的 FastAPI 应用。
    # 本机浏览器通过 127.0.0.1:8000 访问。
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
    )