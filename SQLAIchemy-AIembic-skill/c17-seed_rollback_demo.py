from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from models import Device, Project
from settings import DATABASE_URL


# 显式选择刚才创建的独立实验库。
demo_database = "p29_lab_rollback_demo"
demo_url = make_url(DATABASE_URL).set(database=demo_database)
engine = create_engine(demo_url)

project_code = "ROLLBACK-DEMO"
device_code = "sensor-demo"

expected_description = "用于验证降级后的数据恢复"
expected_location = "实验室 A 区"

with Session(engine) as session, session.begin():
    # 使用固定业务编码，让重复运行复用同一组样本。
    project = session.scalar(
        select(Project).where(Project.code == project_code)
    )

    if project is None:
        project = Project(
            code=project_code,
            name="降级实验项目",
        )
        session.add(project)
        session.flush()

    project.description = expected_description

    device = session.scalar(
        select(Device).where(
            Device.project_id == project.id,
            Device.code == device_code,
        )
    )

    if device is None:
        device = Device(
            project_id=project.id,
            code=device_code,
            name="降级实验设备",
        )
        session.add(device)

    device.location = expected_location

# 事务提交后，用新的 Session 验证数据库保存的值。
with Session(engine) as session:
    row = session.execute(
        select(
            Project.code,
            Project.description,
            Device.code,
            Device.location,
        )
        .join(Device, Device.project_id == Project.id)
        .where(
            Project.code == project_code,
            Device.code == device_code,
        )
    ).one()

    assert row[1] == expected_description
    assert row[3] == expected_location

    print(f"实验数据库：{demo_database}")
    print(f"项目编码：{row[0]}")
    print(f"项目描述：{row[1]}")
    print(f"设备编码：{row[2]}")
    print(f"设备位置：{row[3]}")

engine.dispose()
print("降级实验样本准备完成")