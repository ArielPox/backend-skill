import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models import Device, Project


engine = create_engine(os.environ["DATABASE_URL"])

with Session(engine) as session:
    with session.begin():
        project = Project(code="TX-SPLIT", name="Split transaction demo")
        session.add(project)
        session.flush()
        project_id = project.id

    print(f"Project committed: {project_id}")

    with session.begin():
        session.add_all(
            [
                Device(project_id=project_id, code="sensor-01", name="Sensor A"),
                Device(project_id=project_id, code="sensor-01", name="Sensor B"),
            ]
        )