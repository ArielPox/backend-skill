from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ProgrammingError

from settings import DATABASE_URL


demo_database = "p29_lab_rollback_demo"
demo_url = make_url(DATABASE_URL).set(database=demo_database)
engine = create_engine(demo_url)

# 使用独立的实验表，重复运行时重新准备本次实验数据。
with engine.begin() as connection:
    connection.execute(text("DROP TABLE IF EXISTS lab_migration_conflict"))
    connection.execute(text("""
        CREATE TABLE lab_migration_conflict (
            id INTEGER PRIMARY KEY,
            code TEXT NOT NULL
        )
    """))
    connection.execute(text("""
        INSERT INTO lab_migration_conflict (id, code)
        VALUES (1, 'sensor-demo')
    """))

# 模拟甲分支，成功离开事务块后提交。
with engine.begin() as connection:
    connection.execute(text("""
        ALTER TABLE lab_migration_conflict
        ADD COLUMN location TEXT
    """))
    connection.execute(text("""
        UPDATE lab_migration_conflict
        SET location = '实验室 A 区'
        WHERE id = 1
    """))

print("甲事务已提交")

try:
    # 模拟乙分支，两个操作在同一个事务中。
    with engine.begin() as connection:
        connection.execute(text("""
            ALTER TABLE lab_migration_conflict
            ADD COLUMN branch_b_marker TEXT
        """))
        print("乙事务已添加标记列，尚未提交")

        # 与甲已经提交的列发生名称冲突。
        connection.execute(text("""
            ALTER TABLE lab_migration_conflict
            ADD COLUMN location TEXT
        """))

except ProgrammingError as error:
    # PostgreSQL 42701 表示重复列。
    if getattr(error.orig, "sqlstate", None) != "42701":
        raise

    # 异常已退出事务块，此时乙事务已经回滚。
    print("乙事务遇到重复列错误，已回滚")
    print(error.orig)
else:
    raise AssertionError("预期出现重复列错误，实际操作却成功了")

# 重新查询表结构，检查两个事务分别留下什么结果。
columns = {
    column["name"]
    for column in inspect(engine).get_columns("lab_migration_conflict")
}

assert "location" in columns, "甲事务创建的列缺失"
assert "branch_b_marker" not in columns, "乙事务的标记列未回滚"

with engine.connect() as connection:
    location = connection.execute(text("""
        SELECT location
        FROM lab_migration_conflict
        WHERE id = 1
    """)).scalar_one()

assert location == "实验室 A 区"

print(f"甲提交的位置仍然存在：{location}")
print("乙事务添加的标记列已撤销")
print("迁移冲突与事务边界验收通过")

engine.dispose()