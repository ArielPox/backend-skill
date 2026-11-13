import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models import Device, Project


def import_project(project_code: str, device_codes: list[str]) -> None:
    engine = create_engine(os.environ["DATABASE_URL"])

    with Session(engine) as session, session.begin():
        project = Project(code=project_code, name=project_code)
        session.add(project)
        session.flush()

        session.add_all(
            [
                Device(project_id=project.id, code=code, name=code)
                for code in device_codes
            ]
        )


if __name__ == "__main__":
    import_project("TX-OK", ["sensor-01", "sensor-02"])
    print("Import committed.")