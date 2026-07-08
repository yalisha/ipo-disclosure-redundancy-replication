#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
DATE_TAG = "20260708"
SHARDS = [1, 2, 3, 4, 5]


def main() -> None:
    logs = ROOT / "logs"
    logs.mkdir(exist_ok=True)
    script = ROOT / "scripts/run_siliconflow_glm4_32b_pilot5_20260707.py"
    for shard in SHARDS:
        source = f"glm4_dewrap_join_glm_next100_after200_table2_shard{shard}_{DATE_TAG}"
        run = f"siliconflow_glm4_32b_table2_next100_after200_shard{shard}_{DATE_TAG}"
        log_path = logs / f"{run}.log"
        cmd = [
            sys.executable,
            str(script),
            "--source-run-name",
            source,
            "--run-name",
            run,
            "--doc-name",
            f"{run}.md",
            "--doc-label",
            f"Table2 next100 after GLM200 shard{shard}",
            "--batch-size",
            "1",
            "--sleep",
            "3.0",
            "--retries",
            "8",
            "--rate-limit-sleep",
            "65",
        ]
        print(f"[{datetime.now().isoformat(timespec='seconds')}] start shard={shard} run={run}", flush=True)
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"\n\n===== start {datetime.now().isoformat(timespec='seconds')} =====\n")
            log.write(" ".join(cmd) + "\n")
            log.flush()
            proc = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, text=True)
        print(
            f"[{datetime.now().isoformat(timespec='seconds')}] done shard={shard} returncode={proc.returncode} log={log_path}",
            flush=True,
        )
        if proc.returncode != 0:
            raise SystemExit(proc.returncode)


if __name__ == "__main__":
    main()
