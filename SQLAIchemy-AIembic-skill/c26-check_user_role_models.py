from sqlalchemy.orm import configure_mappers

from models import Base, Role, User


# 检查两个模型的双向关系能否正确建立。
configure_mappers()

assert "roles" in Base.metadata.tables
assert "users" in Base.metadata.tables
assert Role.__table__.c.code.unique
assert User.__table__.c.username.unique
assert not User.__table__.c.role_id.nullable

foreign_key = next(iter(User.__table__.c.role_id.foreign_keys))
assert foreign_key.target_fullname == "roles.id"

print(f"角色表字段：{list(Role.__table__.columns.keys())}")
print(f"用户表字段：{list(User.__table__.columns.keys())}")
print(f"用户角色外键：{foreign_key.target_fullname}")
print("用户与角色模型验收通过")