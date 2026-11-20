from datetime import datetime, timezone

from sqlalchemy import create_engine, or_, update
from sqlalchemy.orm import Session

from models import Device
from settings import DATABASE_URL


engine = create_engine(DATABASE_URL)

reports = [
    (1, datetime(2026, 1, 8, 10, tzinfo=timezone.utc)),
    (2, datetime(2026, 1, 8, 11, tzinfo=timezone.utc)),
]

# 记录运行前的时间，用于验证失败批次是否恢复原值。
with Session(engine) as session:
    before = {}
    for device_id, _ in reports:
        device = session.get(Device, device_id)
        if device is None:
            raise RuntimeError(f"设备 {device_id} 不存在")
        before[device_id] = device.last_seen_at

for batch_number, (device_id, reported_at) in enumerate(reports, start=1):
    try:
        # 本实验每批一台设备，每批使用独立事务。
        with Session(engine) as session, session.begin():
            statement = (
                update(Device)
                .where(
                    Device.id == device_id,
                    or_(
                        Device.last_seen_at.is_(None),
                        Device.last_seen_at < reported_at,
                    ),
                )
                .values(last_seen_at=reported_at)
                .returning(Device.id)
            )
            updated_id = session.execute(statement).scalar_one_or_none()

        count = int(updated_id is not None)
        print(f"第 {batch_number} 批已提交，更新 {count} 台")

    # 异常先离开事务块，触发回滚，再到这里处理。
    except RuntimeError as error:
        print(f"第 {batch_number} 批已回滚，原因：{error}")
        break

# 重新读取数据库，验证第一批提交、第二批回滚的结果。
with Session(engine) as session:
    for device_id, reported_at in reports:
        device = session.get(Device, device_id)
        print(f"设备 {device_id}")
        print(f"  运行前：{before[device_id]}")
        print(f"  运行后：{device.last_seen_at}")

        # 重跑成功后，两台设备都应达到来源记录中的最新时间。
        assert device.last_seen_at is not None
        assert device.last_seen_at >= reported_at

print("分批事务验收通过")
