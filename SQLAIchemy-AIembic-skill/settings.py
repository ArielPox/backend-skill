import os
from pathlib import Path

from dotenv import load_dotenv


# 按本文件的位置查找配置，支持从 VS Code 的不同工作目录运行。
# 已在终端设置的变量优先，方便临时切换到复现库。
load_dotenv(Path(__file__).resolve().parent / "local.env", override=False)
DATABASE_URL = os.environ["DATABASE_URL"]
