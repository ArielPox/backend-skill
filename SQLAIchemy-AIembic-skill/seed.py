import os

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from models import Device, Project


engine = create_engine(os.environ["DATABASE_URL"])

seed_data = [
    ("A", "项目 A", [("sensor-01", "温度传感器"), ("sensor-02", "湿度传感器")]),
    ("B", "项目 B", [("sensor-01", "温度传感器")]),
]

with Session(engine) as session, session.begin():
    for project_code, project_name, devices in seed_data:
        project = session.scalar(
            select(Project).where(Project.code == project_code)
        )
        if project is None:
            project = Project(code=project_code, name=project_name)
            session.add(project)
            session.flush()

        for device_code, device_name in devices:
            device = session.scalar(
                select(Device).where(
                    Device.project_id == project.id,
                    Device.code == device_code,
                )
            )
            if device is None:
                session.add(
                    Device(
                        project_id=project.id,
                        code=device_code,
                        name=device_name,
                    )
                )

print("Seed complete.")