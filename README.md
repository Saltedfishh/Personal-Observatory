# Personal Observatory — Solar Cycle Visualization (MVP)

一个最小可运行的 Python 项目，用于计算指定地点全年日出/日落，并输出：

- 年度二维昼夜图（日期 × 当地钟表时间）
- 年度极坐标昼夜图（时间角度 × 日期半径）
- （可选）昼长一阶年度谐波拟合图

本项目是长期“个人睡眠与天文/季节关系研究”的第一步。当前 **不包含** 睡眠记录、数据库、前端或 Web 服务。

## 1. 目录结构

```
personal-observatory/
├─ README.md
├─ requirements.txt
├─ main.py
├─ solar.py
├─ visualization.py
├─ tests/
│  ├─ test_cli_validation.py
│  ├─ test_solar.py
│  └─ test_pipeline.py
└─ outputs/
```

## 2. 环境要求

- Windows 11
- Python 3.12
- VS Code（可选，但推荐）

## 3. 在 Windows 11 + VS Code 里运行

### 3.1 打开项目

在 VS Code 中打开项目目录：

`C:\Users\DELL\Desktop\Personal Observatory`

### 3.2 创建虚拟环境并安装依赖

在 PowerShell 终端执行：

```powershell
cd "C:\Users\DELL\Desktop\Personal Observatory"
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3.3 运行默认 Adelaide 示例

```powershell
python main.py
```

默认参数：

- `latitude = -34.9`
- `longitude = 138.6`
- `timezone = Australia/Adelaide`
- `year = 2026`
- `output = outputs/`

执行后会在 `outputs/` 下生成：

- `solar_2026.csv`
- `solar_2d_2026.png`
- `solar_polar_2026.png`

### 3.4 启用可选谐波拟合图

```powershell
python main.py --harmonic
```

会额外生成：

- `daylight_harmonic_2026.png`

> 该模型是近似拟合：
> `L(d)=a+b*sin(2*pi*d/T)+c*cos(2*pi*d/T)`，不是精确天文公式。

### 3.5 运行测试

```powershell
pytest -q
```

## 4. 命令行参数

```powershell
python main.py \
  --latitude -34.9 \
  --longitude 138.6 \
  --timezone Australia/Adelaide \
  --year 2026 \
  --output outputs \
  --harmonic
```

参数说明：

- `--latitude`: 纬度，范围 `[-90, 90]`
- `--longitude`: 经度，范围 `[-180, 180]`
- `--timezone`: IANA 时区（例如 `Australia/Adelaide`）
- `--year`: 年份（正整数）
- `--output`: 输出目录
- `--harmonic`: 是否生成昼长谐波拟合图

## 5. 输出数据说明

CSV 至少包含以下字段：

- `date`
- `sunrise_local`（完整本地时间 + UTC offset）
- `sunset_local`（完整本地时间 + UTC offset）
- `sunrise_hour`（0–24 小时小数）
- `sunset_hour`（0–24 小时小数）
- `daylight_hours`
- `status`（如 `normal` / `polar_day` / `polar_night` / `invalid_order`）

对于极昼/极夜等无法正常得到日出日落的日期，不会崩溃：

- CSV 写入状态标记；
- 绘图自动跳过缺失值，保证图可生成。

## 6. 两类图表达的含义

- **二维年度昼夜图**：横轴是日期，纵轴是当地时钟时间（00:00–24:00）。
  - 两条曲线分别是日出和日落时刻；
  - 曲线之间填充表示白天长度；
  - 夏令时切换导致的钟表时间跳变会被保留。

- **极坐标图**：角度表示一天时间（顶部 00:00，顺时针方向），半径表示一年日期（从 1 月向 12 月扩张）。
  - 每日白天绘制为对应半径上的弧段；
  - 直观看到全年昼夜节律变化。

## 7. 当前 MVP 局限

- 只做天文时间与可视化，不含睡眠数据采集与对齐。
- 分点/至点日期采用近似日期（3/20, 6/21, 9/22, 12/21），用于可视化标注。
- 谐波拟合仅做一阶周期近似，不替代精确天文计算。
