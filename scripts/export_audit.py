"""Export a presentable JSON audit report; never reads or copies audio."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from faro.audit import AuditStore


def export_audit(database: str | Path, output: str | Path) -> int:
    records = AuditStore(database).list_records()
    report = {
        "simulation_only": True,
        "audio_included": False,
        "record_count": len(records),
        "records": records,
    }
    Path(output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(records)


def main() -> int:
    parser = argparse.ArgumentParser(description="Exporta auditoría ficticia sin audio.")
    parser.add_argument("database", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    count = export_audit(args.database, args.output)
    print(f"Exportados {count} registros ficticios; audio_included=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
