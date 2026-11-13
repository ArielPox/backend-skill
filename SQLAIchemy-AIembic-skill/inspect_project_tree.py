import os

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, selectinload

from models import Project


engine = create_engine(os.environ["DATABASE_URL"], echo=True)

with Session(engine) as session:
    stmt = select(Project).options(selectinload(Project.devices)).order_by(Project.id)
    projects = session.scalars(stmt).all()

    print(f"项目数：{len(projects)}")
    for project in projects:
        print(f"{project.code} -> {[device.code for device in project.devices]}")