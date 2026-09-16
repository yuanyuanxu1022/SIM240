from mcp.server.mcpserver import MCPServer
from pathlib import Path

server = MCPServer("SIM240 Assistant")
PROJECT_DIR = Path("/home/dell/yuanyuanxu/SIM240")


@server.tool()
def read_sim240_context():
    """
    读取 SIM240 项目当前状态说明
    """

    file = PROJECT_DIR / "SIM240_AI_CONTEXT.md"

    if not file.exists():
        return "没有找到 SIM240_AI_CONTEXT.md"

    return file.read_text(
        encoding="utf-8",
        errors="ignore"
    )
    """
    生成SIM240 CASE Markdown比较表
    """
    
    """
    读取 SIM240 项目当前状态说明
    """

    file = PROJECT_DIR / "SIM240_AI_CONTEXT.md"

    if not file.exists():
        return "SIM240_AI_CONTEXT.md 不存在"

    return file.read_text(
        encoding="utf-8"
    )


@server.tool()
def read_latest_log():
    """
    读取 SIM240 最近一次运行日志
    """
@server.tool()
def search_sim240_error(keyword: str):
    """
    在SIM240结果文件中搜索关键词
    """
@server.tool()
def read_diagnostics():
    """
    读取最近一次SIM240 diagnostics.csv
    """
@server.tool()
def list_project_files():
    """
    查看SIM240项目主要目录结构
    """

    dirs = [
        "CASE",
        "SIM240",
        "grooveDNS",
        "output",
        "ZJ",
        "tmp"
    ]

    result = []

    for d in dirs:
        path = PROJECT_DIR / d

        if path.exists():
            result.append(f"[存在] {d}/")
        else:
            result.append(f"[缺失] {d}/")

    return "\n".join(result)
    results_dir = PROJECT_DIR / "CASE/Case01-R2/results"

    files = list(results_dir.rglob("diagnostics.csv"))

    if not files:
        return "没有找到diagnostics.csv"

    latest = max(
        files,
        key=lambda x: x.stat().st_mtime
    )

    text = latest.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    lines = text.splitlines()

    # 返回最后20行，观察最终收敛状态
    tail = "\n".join(lines[-20:])

    return f"文件:{latest}\n\n{tail}"
    search_dir = PROJECT_DIR / "CASE/Case01-R2/results"

    if not search_dir.exists():
        return "results目录不存在"

    matches = []

    for file in search_dir.rglob("*"):
        if file.is_file():
            try:
                text = file.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )

                if keyword.lower() in text.lower():
                    matches.append(
                        str(file)
                    )

            except Exception:
                pass

    if not matches:
        return f"没有找到关键词: {keyword}"

    return "\n".join(matches[:20])
    results_dir = PROJECT_DIR / "CASE/Case01-R2/results"

    if not results_dir.exists():
        return "results目录不存在"

    logs = list(results_dir.rglob("run.log"))

    if not logs:
        return "没有找到run.log"

    latest = max(
        logs,
        key=lambda x: x.stat().st_mtime
    )

    text = latest.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    return f"文件:{latest}\n\n{text[-5000:]}"
@server.tool()
def diagnose_case_status():
    """
    自动诊断CASE01-R2状态
    """

    result_files = list(
        (PROJECT_DIR / "CASE/Case01-R2/results").rglob("result.txt")
    )

    if not result_files:
        return "没有找到result.txt"

    latest = max(
        result_files,
        key=lambda x: x.stat().st_mtime
    )

    data = {}

    for line in latest.read_text(
        encoding="utf-8",
        errors="ignore"
    ).splitlines():

        if "=" in line:
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip()


    report = []

    report.append("SIM240 CASE01-R2 状态诊断")
    report.append("")


    # 收敛
    if data.get("converged") == "true":
        report.append("✓ 稳态收敛")
    else:
        report.append("✗ 未收敛")


    # Mach
    try:
        mach = float(data.get("max_Mach", "999"))

        if mach < 0.1:
            report.append(
                f"✓ Mach满足要求 ({mach:.3e})"
            )
        else:
            report.append(
                f"⚠ Mach偏高 ({mach:.3e})"
            )

    except:
        pass


    # 质量守恒
    if data.get("max_mass_abs_relative") == "0":
        report.append(
            "✓ 质量守恒通过"
        )
    else:
        report.append(
            "⚠ 存在质量误差"
        )


    # Jy误差
    try:
        jy_error = abs(
            float(data.get("Jy_relative_error", "999"))
        )

        if jy_error < 0.02:
            report.append(
                f"✓ Jy误差低于2% ({jy_error:.3%})"
            )
        else:
            report.append(
                f"⚠ Jy误差较大 ({jy_error:.3%})"
            )

    except:
        pass


    report.append("")


    # PASS分析
    if data.get("PASS") == "false":

        report.append(
            "⚠ 最终PASS未通过"
        )

        if data.get("geometry_PASS") == "false":
            report.append(
                "- 原因: geometry_PASS=false"
            )

        if data.get("normal_exit_planned") == "false":
            report.append(
                "- 原因: normal_exit_planned=false"
            )

    else:
        report.append(
            "✓ PASS通过"
        )


    return "\n".join(report)

if __name__ == "__main__":
    server.run()
@server.tool()
def analyze_case_result():
    """
    自动总结最新CASE01-R2计算结果
    """
@server.tool()
def generate_validation_report():
    """
    生成SIM240论文级验证报告
    """

    result_files = list(
        (PROJECT_DIR / "CASE/Case01-R2/results").rglob("result.txt")
    )

    if not result_files:
        return "没有找到result.txt"

    latest = max(
        result_files,
        key=lambda x: x.stat().st_mtime
    )

    data = {}

    for line in latest.read_text(
        encoding="utf-8",
        errors="ignore"
    ).splitlines():

        if "=" in line:
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip()


    report = f"""
# SIM240 CASE01-R2 Validation Report


## 1. Simulation setup

Run:
{data.get('run_scope')}

Lattice model:
{data.get('descriptor')}

Collision:
{data.get('collision')}

Boundary:
{data.get('wall_boundary')}

Grid spacing:
{data.get('dx_m')} m


## 2. Numerical stability

Converged:
{data.get('converged')}

Steps:
{data.get('steps_completed')}

Maximum Mach:
{data.get('max_Mach')}


## 3. Conservation check

Maximum mass error:
{data.get('max_mass_abs_relative')}

Density deviation:
{data.get('max_density_deviation')}

Flux difference:
{data.get('section_flux_relative_difference')}


## 4. Analytical validation

Computed Jy:
{data.get('Jy_m2_s')}

Analytical Jy:
{data.get('analytic_Jy_m2_s')}

Relative error:
{data.get('Jy_relative_error')}


Computed RJ:
{data.get('RJ_Pa_s_per_m3')}

Analytical RJ:
{data.get('analytic_RJ_Pa_s_per_m3')}

Relative error:
{data.get('RJ_relative_error')}


Velocity profile L2 error:
{data.get('velocity_profile_L2_relative_error')}


## 5. Final assessment

PASS:
{data.get('PASS')}

"""

    return report
    result_files = list(
        (PROJECT_DIR / "CASE/Case01-R2/results").rglob("result.txt")
    )

    if not result_files:
        return "没有找到result.txt"

    latest = max(
        result_files,
        key=lambda x: x.stat().st_mtime
    )

    data = {}

    for line in latest.read_text(
        encoding="utf-8",
        errors="ignore"
    ).splitlines():

        if "=" in line:
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip()


    report = f"""
SIM240 CASE01-R2 自动分析

运行:
{data.get('run_scope')}

收敛状态:
{data.get('converged')}

停止原因:
{data.get('stop_reason')}

计算步数:
{data.get('steps_completed')}


边界:
{data.get('wall_boundary')}

质量误差:
{data.get('max_mass_abs_relative')}

最大Mach:
{data.get('max_Mach')}

数值通量 Jy:
{data.get('Jy_m2_s')}

理论 Jy:
{data.get('analytic_Jy_m2_s')}

Jy相对误差:
{data.get('Jy_relative_error')}

RJ相对误差:
{data.get('RJ_relative_error')}

速度场L2误差:
{data.get('velocity_profile_L2_relative_error')}

最终PASS:
{data.get('PASS')}
"""

    return report
@server.tool()
def git_status():
    """
    查看SIM240当前Git状态
    """
@server.tool()
def git_diff():
    """
    查看SIM240代码修改内容
    """

    import subprocess

    try:
        result = subprocess.run(
            ["git", "diff"],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True
        )

        if result.stdout:
            return result.stdout[:8000]

        return "没有代码差异"

    except Exception as e:
        return f"Git错误: {e}"
    import subprocess

    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True
        )

        if result.stdout:
            return result.stdout[:5000]

        return "Git工作区干净"

    except Exception as e:
        return f"Git错误: {e}"
@server.tool()
def compare_cases():
    """
    比较所有CASE结果
    """

    files = list(
        (PROJECT_DIR / "CASE").rglob("result.txt")
    )
    files = [
    f for f in files
    if (
        "Jy_m2_s" in f.read_text(
            encoding="utf-8",
            errors="ignore"
        )
        and
        "analytic_Jy_m2_s" in f.read_text(
            encoding="utf-8",
            errors="ignore"
        )
    )
]
    if not files:
        return "没有找到CASE结果"


    rows=[]

    for f in files:

        data={}

        for line in f.read_text(
            encoding="utf-8",
            errors="ignore"
        ).splitlines():

            if "=" in line:
                k,v=line.split("=",1)
                data[k.strip()]=v.strip()


        rows.append(
            {
                "case": data.get(
                    "run_scope",
                    f.parent.name
                ),
                "Jy": data.get(
                    "Jy_m2_s",
                    "-"
                ),
                "Error": (
                   f"{float(data.get('Jy_relative_error',0))*100:.3f}%"
                   if "Jy_relative_error" in data
                   else "-"
                  ),
                "Mach": data.get(
                    "max_Mach",
                    "-"
                ),
                "PASS": data.get(
                    "PASS",
                    "-"
                )
            }
        )


    report="SIM240 CASE比较\n\n"

    for r in rows:
        report += (
            f"{r['case']}\n"
            f" Jy={r['Jy']}\n"
            f" error={r['error']}\n"
            f" Mach={r['Mach']}\n"
            f" PASS={r['PASS']}\n\n"
        )

    return report


@server.tool()
def compare_cases_table():
    """
    生成SIM240 CASE Markdown比较表
    """

    files = list(
        (PROJECT_DIR / "CASE").rglob("result.txt")
    )

    rows = []

    for f in files:
        text = f.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        if "Jy_m2_s" not in text:
            continue
        if "formal_simulation=true" not in text:
            continue
 
        data = {}
        for line in text.splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                data[k.strip()] = v.strip()

        rows.append(
            {
                "Case": data.get("run_scope", f.parent.name),
                "Jy": data.get("Jy_m2_s", "-"),
                "Error": data.get("Jy_relative_error", "-"),
                "Mach": data.get("max_Mach", "-"),
                "PASS": data.get("PASS", "-"),
            }
        )

    table = [
        "| Case | Jy | Error | Mach | PASS |",
        "|---|---|---|---|---|"
    ]

    for r in rows:
        table.append(
            f"| {r['Case']} | {r['Jy']} | "
            f"{r['Error']} | {r['Mach']} | {r['PASS']} |"
        )

    return "\n".join(table)

@server.tool()
def rank_cases():
    """
    按 Jy_relative_error 对 SIM240 CASE 排名
    """

    files = list(
        (PROJECT_DIR / "CASE").rglob("result.txt")
    )

    cases = []

    for f in files:

        text = f.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        if "Jy_relative_error" not in text:
            continue

        data = {}

        for line in text.splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                data[k.strip()] = v.strip()

        try:
            error = float(
                data["Jy_relative_error"]
            )
        except:
            continue

        cases.append(
            {
                "Case": data.get(
                    "run_scope",
                    f.parent.name
                ),
                "Error": error,
                "PASS": data.get(
                    "PASS",
                    "-"
                )
            }
        )


    cases.sort(
        key=lambda x: x["Error"]
    )


    output = [
        "SIM240 CASE Ranking",
        ""
    ]


    for i, c in enumerate(
        cases,
        start=1
    ):
        output.append(
            f"{i}. {c['Case']}"
        )

        output.append(
            f"   Jy error = {c['Error']:.3%}"
        )

        output.append(
            f"   PASS = {c['PASS']}"
        )

        output.append("")


    return "\n".join(output)
@server.tool()
def generate_case_summary_md():
    """
    自动生成 SIM240 CASE 状态汇总文件
    """

    table = compare_cases_table()

    content = f"""# SIM240 CASE Status

自动生成的 CASE 验证状态。

## CASE Summary

{table}

"""

    output = PROJECT_DIR / "SIM240_CASE_STATUS.md"

    output.write_text(
        content,
        encoding="utf-8"
    )

    return f"Generated: {output}"
