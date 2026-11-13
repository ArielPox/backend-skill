import os
from fastapi import FastAPI, HTTPException, status
from psycopg.errors import UniqueViolation
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from import_devices import import_project
from sqlalchemy import create_engine, select,func
from sqlalchemy.orm import Session, selectinload

from import_devices import import_project
from models import Project
from fastapi import Query
from models import Device, Project

app = FastAPI()
engine = create_engine(os.environ["DATABASE_URL"])


class ProjectImport(BaseModel):
    project_code: str
    device_codes: list[str]


@app.post("/projects/import", status_code=status.HTTP_201_CREATED)
def import_project_endpoint(payload: ProjectImport):
    try:
        import_project(payload.project_code, payload.device_codes)
    except IntegrityError as exc:
        error = exc.orig
        if (
            isinstance(error, UniqueViolation)
            and error.diag.constraint_name == "uq_devices_project_id_code"
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Device codes must be unique within a project.",
            ) from exc
        raise

    return {"project_code": payload.project_code}

@app.get("/projects/tree")
def project_tree():
    stmt = (
        select(Project)
        .options(selectinload(Project.devices))
        .order_by(Project.id)
    )

    with Session(engine) as session:
        projects = session.scalars(stmt).all()
        return [
            {
                "code": project.code,
                "devices": [
                    {"code": device.code}
                    for device in sorted(project.devices, key=lambda device: device.id)
                ],
            }
            for project in projects
        ]

@app.get("/api/v1/projects/{project_id}/devices")
def list_project_devices(
    project_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),    q: str | None = Query(default=None, max_length=50),
):
    with Session(engine) as session:
        if session.get(Project, project_id) is None:
            raise HTTPException(status_code=404, detail="Project not found.")
        filters = [Device.project_id == project_id]
        keyword = q.strip() if q else ""
        if keyword:
            filters.append(Device.code.icontains(keyword, autoescape=True))
        total = session.scalar(
            select(func.count()).select_from(Device).where(*filters)
        )

        stmt = (
            select(Device)
            .where(*filters)
            .order_by(Device.created_at.desc(), Device.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        devices = session.scalars(stmt).all()
        return {
            "total": total,
            "items": [
                {"id": device.id, "code": device.code, "created_at": device.created_at}
                for device in devices
            ],
        }