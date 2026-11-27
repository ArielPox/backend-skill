from uuid import uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from import_devices import import_project
from models import Device, Project
from settings import DATABASE_URL


# 每次生成不同的项目编码，方便重复运行验证。
project_code = f"COMPAT-{uuid4().hex[:8]}"

# 沿用原来的导入函数，调用时只传项目编码和设备编码。
import_project(project_code, ["sensor-01"])

engine = create_engine(DATABASE_URL)

# 用新的 Session 查询，确认刚才的事务已经提交。
with Session(engine) as session:
    device = session.scalars(
        select(Device)
        .join(Project, Device.project_id == Project.id)
        .where(
            Project.code == project_code,
            Device.code == "sensor-01",
        )
    ).one()

    print(f"项目：{project_code}")
    print(f"设备：{device.code}")
    print(f"最后上报时间：{device.last_seen_at}")

    assert device.last_seen_at is None
    print("验收通过：原有导入流程可用，新字段为空。")
