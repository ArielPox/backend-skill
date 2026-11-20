from settings import DATABASE_URL
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session

from models import Alarm, Device


engine = create_engine(DATABASE_URL)

# 使用固定基准时间，使每次生成的数据范围一致，便于对比执行计划。
base_time = datetime(2026, 1, 1, tzinfo=timezone.utc)

# session.begin() 让删除旧数据和写入新数据处于同一个事务。
# 中途失败时，本次修改会一起回滚。
with Session(engine) as session, session.begin():
    device_ids = session.scalars(select(Device.id).order_by(Device.id)).all()

    if not device_ids:
        raise RuntimeError("No devices found. Run the device seed first.")

    # 清空旧的练习告警，保证脚本重复执行时不会不断增加数据。
    session.execute(delete(Alarm))

    alarms = []

    for device_position, device_id in enumerate(device_ids):
        # 第一台设备作为热点设备，其他设备作为冷数据。
        alarm_count = 20_000 if device_position == 0 else 500

        for index in range(alarm_count):
            alarms.append(
                Alarm(
                    device_id=device_id,
                    # 约 20% 为 open，约 80% 为 closed。
                    # 这样可以观察 status 条件对查询计划的影响。
                    status="open" if index % 10 < 2 else "closed",
                    message=f"Alarm {device_id}-{index}",
                    # 每条告警间隔一分钟，形成稳定且可筛选的时间范围。
                    occurred_at=base_time + timedelta(minutes=index),
                )
            )

    # 统一交给当前事务写入，事务块成功结束时才提交。
    session.add_all(alarms)

print(f"Seeded {len(alarms)} alarms.")
print(f"Target device ID: {device_ids[0]}")
