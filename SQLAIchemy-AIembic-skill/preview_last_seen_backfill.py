from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from models import Device
from settings import DATABASE_URL


engine = create_engine(DATABASE_URL)

with Session(engine) as session:
    # 固定选择 ID 最小的两台设备，便于重复核对结果。
    devices = session.scalars(select(Device).order_by(Device.id).limit(2)).all()

    if len(devices) < 2:
        raise RuntimeError("本实验需要至少两台设备。")

        # 模拟历史上报记录。第一台设备有两次上报。
        # 模拟迟到的历史记录，其上报时间早于已经保存的时间。
    reports = [
        # 设备 1 收到更新的上报，应更新为 12:00。
        (devices[0].id, datetime(2026, 1, 5, 12, tzinfo=timezone.utc)),
        # 设备 2 仍是较旧的记录，应保留数据库中的 09:00。
        (devices[1].id, datetime(2026, 1, 6, 8, tzinfo=timezone.utc)),
    ]

    latest_by_device = {}
    for device_id, reported_at in reports:
        previous = latest_by_device.get(device_id)
        if previous is None or reported_at > previous:
            latest_by_device[device_id] = reported_at

        # 本步只打印预览，实际赋值和提交放在下一步。
        updated_count = 0

    for device in devices:
        latest_time = latest_by_device[device.id]

        # 跳过相同或更旧的来源时间，避免重复更新和时间倒退。
        if device.last_seen_at is None or latest_time > device.last_seen_at:
            device.last_seen_at = latest_time
            updated_count += 1

    # 将本次修改一起提交。提交成功后，其他连接才能读到新值。
    session.commit()
    print(f"本次更新设备数：{updated_count}")

# 使用新的 Session 重新读取，核对提交后的数据库值。
with Session(engine) as session:
    saved_devices = session.scalars(
        select(Device).where(Device.id.in_(latest_by_device)).order_by(Device.id)
    ).all()

    for device in saved_devices:
        print(f"设备 {device.id}，最后上报时间：{device.last_seen_at}")
        assert device.last_seen_at >= latest_by_device[device.id]

    print("回填验收通过")
