from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from settings import DATABASE_URL


demo_url = make_url(DATABASE_URL).set(
    database="p29_lab_rollback_demo"
)
engine = create_engine(demo_url)

# 每次使用独立的项目编码，便于重复运行。
project_code = f"OLD-APP-{uuid4().hex[:8]}"

with engine.begin() as connection:
    # 模拟旧应用创建项目，只提供原有字段。
    project_id = connection.execute(
        text("""
            INSERT INTO projects (code, name)
            VALUES (:code, :name)
            RETURNING id
        """),
        {"code": project_code, "name": "旧应用兼容实验"},
    ).scalar_one()

    # 模拟旧应用创建设备，省略新增的位置和最后上报时间。
    device_id = connection.execute(
        text("""
            INSERT INTO devices (project_id, code, name)
            VALUES (:project_id, :code, :name)
            RETURNING id
        """),
        {
            "project_id": project_id,
            "code": "sensor-old",
            "name": "旧应用设备",
        },
    ).scalar_one()

print("旧应用写入成功，事务已提交")

with engine.connect() as connection:
    # 模拟旧应用读取它认识的字段。
    old_result = connection.execute(
        text("""
            SELECT code, name
            FROM devices
            WHERE id = :device_id
        """),
        {"device_id": device_id},
    ).one()

    assert old_result.code == "sensor-old"
    assert old_result.name == "旧应用设备"
    print("旧应用查询成功")

    # 从新结构的视角检查新增字段。
    new_result = connection.execute(
        text("""
            SELECT p.description, d.location, d.last_seen_at
            FROM projects AS p
            JOIN devices AS d ON d.project_id = p.id
            WHERE d.id = :device_id
        """),
        {"device_id": device_id},
    ).one()

    assert new_result.description is None
    assert new_result.location is None
    assert new_result.last_seen_at is None

    versions = connection.execute(
        text("SELECT version_num FROM alembic_version")
    ).scalars().all()

assert versions == ["c5441c214269"]

print(f"项目描述：{new_result.description}")
print(f"设备位置：{new_result.location}")
print(f"最后上报时间：{new_result.last_seen_at}")
print(f"数据库版本：{versions}")
print("旧字段读写兼容验收通过")

engine.dispose()