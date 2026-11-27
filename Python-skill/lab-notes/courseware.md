# Python 工程实战课件

对应 [课程计划](../course-plan.md)。在 VS Code 打开 `D:\myskills\Python-skill`，使用集成 PowerShell 终端。课堂互动时按课程计划约定，每次“继续”只推进下面的一个可验证步骤。每课完成后，在本目录另存实际操作笔记，记录真实输出、报错和自测回答。

## 项目全局

设备 CSV → 读取行 → 校验和转换 → 记录拒绝原因 → 写入 JSON → 命令行汇总。

输入文件保存在 `data`，工具代码保存在 `device_tool.py`，输出文件保存在 `output`。所有路径以运行命令时所在的课程目录为基准。六课逐步扩展同一个工具。

## 第 1 课｜建立可复现的环境

**目标与验收**　创建项目虚拟环境，从该环境运行 Python。新开一个 VS Code 终端后，仍能用明确的解释器路径运行脚本。

**先知道**　虚拟环境保存项目依赖。终端中的 `python` 可能指向系统解释器，执行 `python -m pip` 可以让 pip 与所选解释器一致。

1. 在 VS Code 集成 PowerShell 中确认目录和解释器。

   ```powershell
   Set-Location 'D:\myskills\Python-skill'
   Get-Location
   py -3 --version
   ```

   预期工作目录为 `D:\myskills\Python-skill`，Python 版本为项目支持的 3.x。若 `py` 不可用，先在 VS Code 中选择已安装的 Python，再用其实际路径创建环境。

2. 创建环境并核对解释器和 pip。

   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\python.exe -c "import sys; print(sys.executable)"
   .\.venv\Scripts\python.exe -m pip --version
   ```

   两条输出都应指向本课程的 `.venv`。在 VS Code 中选择同一个解释器。

3. 在编辑器中新建 `hello.py`，内容为 `print('device tool ready')`，然后运行。

   ```powershell
   .\.venv\Scripts\python.exe .\hello.py
   ```

   预期输出 `device tool ready`。若 VS Code 运行按钮使用另一解释器，比较终端的 `sys.executable` 和 VS Code 状态栏解释器路径。

**自测**　为什么直接执行 `pip install` 可能把包安装到与运行脚本不同的 Python？先回答，再对照上面的两条路径。

**笔记**　记录 Python 版本、解释器路径、pip 路径、运行命令与实际输出。

## 第 2 课｜清洗一条设备记录

**目标与验收**　把字符串形式的设备编码、状态、UTC 时间和数值转成统一字典。有效数据通过，缺字段、空编码和非法数值给出可定位的原因。

**先知道**　输入来自文件时通常都是字符串。先验证必填值，再做类型转换。带时区时间使用 `datetime.fromisoformat` 解析，并明确要求 `tzinfo` 存在。

1. 在编辑器中新建 `device_tool.py`，写入单行转换函数。

   ```python
   from datetime import datetime
   from math import isfinite


   def clean_record(row: dict[str, str | None]) -> dict[str, object]:
       values = {}
       for name in ("device_code", "status", "reported_at", "value"):
           raw = row.get(name)
           if raw is None:
               raise ValueError(f"{name} 缺失")
           values[name] = raw.strip()

       code = values["device_code"]
       if not code:
           raise ValueError("device_code 为空")

       status = values["status"].lower()
       if status not in {"online", "offline"}:
           raise ValueError("status 无效")

       reported_at = datetime.fromisoformat(values["reported_at"])
       if reported_at.tzinfo is None:
           raise ValueError("reported_at 缺少时区")

       value = float(values["value"])
       if not isfinite(value):
           raise ValueError("value 必须为有限数值")
       return {
           "device_code": code,
           "status": status,
           "reported_at": reported_at.isoformat(),
           "value": value,
       }
   ```

2. 在课程目录的集成 PowerShell 运行一条有效数据。

   ```powershell
   .\.venv\Scripts\python.exe -c "from device_tool import clean_record; print(clean_record({'device_code':' sensor-01 ','status':'ONLINE','reported_at':'2026-01-01T08:00:00+08:00','value':'12.5'}))"
   ```

   预期编码去掉空格，状态为 `online`，数值为 `12.5`，时间保留时区信息。

3. 把 `value` 改成 `abc`、把编码改成空格，分别观察 `ValueError`。缺少 `device_code` 时也得到明确的 `ValueError`。下一课的文件读取层会把这些错误附上行号。

**自测**　`2026-01-01T08:00:00` 与 `2026-01-01T08:00:00+08:00` 在这段校验中有什么差异？

**笔记**　保存四组输入、输出或异常，以及你选定的字段约束。

## 第 3 课｜读取 CSV 并写入 JSON

**目标与验收**　逐行读取 CSV，保留有效记录，记录坏行的行号和原因，输出 UTF-8 JSON。文件不存在和表头缺列时明确失败。

**先知道**　`csv.DictReader` 把表头映射为字典键。`pathlib.Path` 表示路径。`with` 保证文件及时关闭。`enumerate(..., start=2)` 对应第一条数据在 CSV 的第 2 行。

1. 在 VS Code 中创建 `data/devices.csv`，保存为 UTF-8。

   ```csv
   device_code,status,reported_at,value
   sensor-01,online,2026-01-01T08:00:00+08:00,12.5
   ,offline,2026-01-01T09:00:00+08:00,10
   sensor-02,offline,2026-01-01T10:00:00+08:00,abc
   ```

2. 在 `device_tool.py` 中追加读取函数。

   ```python
   import csv
   import json
   from pathlib import Path

   REQUIRED_COLUMNS = {"device_code", "status", "reported_at", "value"}


   def read_devices(input_path: Path) -> tuple[list[dict[str, object]], list[str]]:
       valid = []
       rejected = []
       with input_path.open("r", encoding="utf-8-sig", newline="") as source:
           reader = csv.DictReader(source)
           if not reader.fieldnames or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
               raise ValueError("CSV 表头缺少必需列")
           for line_number, row in enumerate(reader, start=2):
               try:
                   valid.append(clean_record(row))
               except (KeyError, TypeError, ValueError) as error:
                   rejected.append(f"第 {line_number} 行：{error}")
       return valid, rejected


   def write_devices(output_path: Path, records: list[dict[str, object]]) -> None:
       output_path.parent.mkdir(parents=True, exist_ok=True)
       with output_path.open("w", encoding="utf-8") as target:
           json.dump(records, target, ensure_ascii=False, indent=2)
   ```

3. 在集成 PowerShell 验证读取与写入。

   ```powershell
   .\.venv\Scripts\python.exe -c "from pathlib import Path; from device_tool import read_devices,write_devices; rows,errors=read_devices(Path('data/devices.csv')); write_devices(Path('output/devices.json'),rows); print(len(rows),errors)"
   Get-Content .\output\devices.json -Encoding utf8
   ```

   预期有效记录 1 条，拒绝原因对应第 3、4 行，JSON 中包含 `sensor-01`。

**自测**　如果表头缺少 `reported_at`，为什么不宜把文件中每一行都记成坏行后继续？

**笔记**　记录输入样本、有效条数、拒绝行号及输出文件内容。

## 第 4 课｜形成命令行入口

**目标与验收**　用输入和输出参数运行同一工具，换文件不改源码。非法参数显示帮助并以非零状态退出。

**先知道**　`argparse` 处理参数解析和用法提示。入口函数把读取、转换、写入串起来，业务函数仍可单独测试或由 FastAPI 调用。

1. 在 `device_tool.py` 中追加入口。

   ```python
   import argparse


   def main() -> int:
       parser = argparse.ArgumentParser(description="清洗设备 CSV")
       parser.add_argument("--input", type=Path, required=True)
       parser.add_argument("--output", type=Path, required=True)
       args = parser.parse_args()
       records, rejected = read_devices(args.input)
       write_devices(args.output, records)
       for reason in rejected:
           print(reason)
       print(f"有效 {len(records)} 条，拒绝 {len(rejected)} 条")
       return 0


   if __name__ == "__main__":
       raise SystemExit(main())
   ```

2. 在课程目录运行。

   ```powershell
   .\.venv\Scripts\python.exe .\device_tool.py --input .\data\devices.csv --output .\output\devices.json
   .\.venv\Scripts\python.exe .\device_tool.py --help
   ```

   预期显示 `有效 1 条，拒绝 2 条`，帮助列出两个必填参数。省略 `--input` 再运行，观察参数错误和 `$LASTEXITCODE` 非零。

**自测**　为什么读文件和校验记录仍保留独立函数，而由 `main()` 调用？

**笔记**　保存正常运行与非法参数两次命令及退出码。

## 第 5 课｜异常、日志与配置边界

**目标与验收**　坏行继续处理，输入整体不可用或输出失败时命令返回非零状态。错误信息指出失败阶段。

**先知道**　一行字段值无效属于行级错误。文件不存在、表头缺列和输出失败影响整个任务。异常类型应在最了解上下文的层处理，避免把半份输出当成成功。

1. 将 `main()` 中调用 `read_devices` 和 `write_devices` 的部分改为下面的异常边界。

   ```python
   try:
       records, rejected = read_devices(args.input)
       write_devices(args.output, records)
   except (OSError, ValueError) as error:
       parser.exit(1, f"处理失败：{error}\n")
   ```

   保留原来打印拒绝原因、汇总和 `return 0` 的代码。

2. 用不存在的输入文件验证失败，再恢复正常输入。

   ```powershell
   .\.venv\Scripts\python.exe .\device_tool.py --input .\data\missing.csv --output .\output\devices.json
   $LASTEXITCODE
   .\.venv\Scripts\python.exe .\device_tool.py --input .\data\devices.csv --output .\output\devices.json
   $LASTEXITCODE
   ```

   第一轮预期失败且退出码为 1，第二轮可跳过两条坏行并退出 0。输出目录不可写的实验应使用专门的受控目录，验证失败后不要把旧输出文件误当成新结果。

**自测**　CSV 第 8 行数值无效与输出目录不可写，哪一个可以跳过，哪一个必须终止整次命令？

**笔记**　记录行级与任务级故障各一例，包括退出码和输出文件状态。

## 第 6 课｜测试与交接

**目标与验收**　测试校验函数、坏行和命令行失败。另一台开发机能照着依赖和运行说明复现。

**先知道**　单元测试检验转换规则，命令行测试检验退出码与文件结果。测试输入使用临时目录，避免覆盖学习数据。

1. 在项目虚拟环境安装 pytest。

   ```powershell
   .\.venv\Scripts\python.exe -m pip install pytest
   .\.venv\Scripts\python.exe -m pytest --version
   ```

2. 在 `tests/test_device_tool.py` 写入最小测试。

   ```python
   import pytest
   from device_tool import clean_record, read_devices


   def test_clean_record_normalizes_values():
       result = clean_record({
           "device_code": " sensor-01 ",
           "status": "ONLINE",
           "reported_at": "2026-01-01T00:00:00+00:00",
           "value": "12.5",
       })
       assert result["device_code"] == "sensor-01"
       assert result["value"] == 12.5


   def test_read_devices_rejects_bad_row(tmp_path):
       source = tmp_path / "devices.csv"
       source.write_text(
           "device_code,status,reported_at,value\n"
           "sensor-01,online,2026-01-01T00:00:00+00:00,1\n"
           ",online,2026-01-01T00:00:00+00:00,1\n",
           encoding="utf-8",
       )
       valid, rejected = read_devices(source)
       assert len(valid) == 1
       assert len(rejected) == 1
       assert "第 3 行" in rejected[0]


   def test_time_requires_timezone():
       with pytest.raises(ValueError, match="时区"):
           clean_record({
               "device_code": "sensor-01", "status": "online",
               "reported_at": "2026-01-01T00:00:00", "value": "1",
           })
   ```

3. 在集成 PowerShell 运行测试和样例命令。

   ```powershell
   .\.venv\Scripts\python.exe -m pytest -q
   .\.venv\Scripts\python.exe .\device_tool.py --input .\data\devices.csv --output .\output\devices.json
   ```

   预期测试全部通过，样例输出有效 1 条、拒绝 2 条。把 Python 版本、pytest 安装方式、输入列名、运行命令和预期输出记入课程实验笔记。

**自测**　测试失败提示缺少 `device_tool` 模块时，应先核对运行目录、解释器还是 CSV 内容？说明判断依据。

**结课验收**　在一套新虚拟环境复现第 6 课的测试和命令。检查正常数据、坏行、表头错误、缺文件和输出失败五类结果。实验笔记记录实际结果与本课预期的差异。
