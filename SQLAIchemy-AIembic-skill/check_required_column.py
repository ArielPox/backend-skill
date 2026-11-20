from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from settings import DATABASE_URL


engine = create_engine(DATABASE_URL)

with engine.begin() as connection:
    # 创建临时实验表，在本次事务结束时自动清理。
    connection.execute(
        text("""
        CREATE TEMP TABLE lab_devices (
            id INTEGER PRIMARY KEY,
            code TEXT NOT NULL
        ) ON COMMIT DROP
    """)
    )

    connection.execute(
        text("""
        INSERT INTO lab_devices (id, code)
        VALUES (1, 'sensor-01'), (2, 'sensor-02')
    """)
    )

    try:
        # 保存点用于撤销失败的添加操作，便于随后检查实验表。
        with connection.begin_nested():
            connection.execute(
                text("""
                ALTER TABLE lab_devices
                ADD COLUMN registration_source TEXT NOT NULL
            """)
            )

    except IntegrityError as error:
        # 只将预期的非空约束错误作为本次实验结果。
        if getattr(error.orig, "sqlstate", None) != "23502":
            raise
        print("捕获到预期错误")
        print(error.orig)
    else:
        raise AssertionError("预期添加失败，但操作成功了")

    rows = connection.execute(
        text("""
        SELECT id, code
        FROM lab_devices
        ORDER BY id
    """)
    ).all()

    print(f"失败后原有记录数：{len(rows)}")
    for row in rows:
        print(f"设备 {row.id}，编码 {row.code}")

    assert len(rows) == 2
    print("非空列失败对照验收通过")

    # 第一步允许旧记录暂时保留空值，完成新增列。
    connection.execute(
        text("""
        ALTER TABLE lab_devices
        ADD COLUMN registration_source TEXT
    """)
    )
    print("已添加可空列")

    # 本实验已知这两条记录都来自旧系统导入。
    connection.execute(
        text("""
        UPDATE lab_devices
        SET registration_source = 'legacy_import'
        WHERE registration_source IS NULL
    """)
    )
    print("已完成来源回填")

    # 收紧约束前检查数据，存在空值时停止操作。
    null_count = connection.execute(
        text("""
        SELECT COUNT(*)
        FROM lab_devices
        WHERE registration_source IS NULL
    """)
    ).scalar_one()

    print(f"剩余空值数量：{null_count}")
    if null_count != 0:
        raise RuntimeError("仍有设备缺少登记来源，请先补齐")

    connection.execute(
        text("""
        ALTER TABLE lab_devices
        ALTER COLUMN registration_source SET NOT NULL
    """)
    )
    print("已设置非空约束")

    # 查询最终数据。
    rows = connection.execute(
        text("""
        SELECT id, code, registration_source
        FROM lab_devices
        ORDER BY id
    """)
    ).all()

    for row in rows:
        print(f"设备 {row.id}，来源：{row.registration_source}")

    # 实际尝试写入空值，验证数据库确实执行了新约束。
    try:
        with connection.begin_nested():
            connection.execute(
                text("""
                INSERT INTO lab_devices (id, code, registration_source)
                VALUES (3, 'sensor-03', NULL)
            """)
            )
    except IntegrityError as error:
        if getattr(error.orig, "sqlstate", None) != "23502":
            raise
        print("写入空来源被拒绝，非空约束验收通过")
    else:
        raise AssertionError("数据库接受了空来源，验收失败")
