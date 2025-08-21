#!/usr/bin/env python3
import shutil
from pathlib import Path

def clear_test_results():
    base = Path(__file__).parent / "test_results"
    if not base.exists():
        print(f"{base} does not exist. Nothing to clear.")
        return

    cleared = 0
    for item in base.iterdir():
        try:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
            cleared += 1
        except Exception as e:
            print(f"Failed to remove {item}: {e}")

    # Recreate expected subfolders
    (base / "json_results").mkdir(parents=True, exist_ok=True)
    (base / "report_results").mkdir(parents=True, exist_ok=True)
    (base / "csv_results").mkdir(parents=True, exist_ok=True)

    print(f"Cleared {cleared} items in {base}. Recreated json_results/, report_results/, and csv_results/.")

if __name__ == "__main__":
    clear_test_results()