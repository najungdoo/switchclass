from __future__ import annotations

import io
from pathlib import Path
from typing import List

from flask import Flask, render_template, request

from schedule_swap import DAYS, SwapEngine, Timetable

app = Flask(__name__)
DEFAULT_TIMETABLE_PATH = Path("2026_1_timetable.csv")


def _parse_periods(raw: str) -> List[int]:
    return [int(p.strip()) for p in raw.split(",") if p.strip()]


def _parse_absent(raw: str) -> List[str]:
    return [t.strip() for t in raw.split(",") if t.strip()]


def _load_timetable_from_request(file_storage) -> Timetable:
    """업로드 파일이 있으면 우선 사용하고, 없으면 기본 파일을 읽는다."""
    if file_storage and file_storage.filename:
        content = file_storage.read().decode("utf-8")
        return Timetable.from_csv_obj(io.StringIO(content))

    if DEFAULT_TIMETABLE_PATH.exists():
        return Timetable.from_csv(str(DEFAULT_TIMETABLE_PATH))

    raise ValueError(
        "시간표 파일이 없습니다. 2026_1_timetable.csv를 프로젝트 루트에 두거나 파일을 업로드해주세요."
    )


@app.route("/", methods=["GET", "POST"])
def index():
    rows = []
    error = ""
    form = {
        "day": "월",
        "periods": "1,2,3",
        "absent": "",
    }
    default_file_exists = DEFAULT_TIMETABLE_PATH.exists()

    if request.method == "POST":
        form["day"] = request.form.get("day", "월")
        form["periods"] = request.form.get("periods", "")
        form["absent"] = request.form.get("absent", "")
        file = request.files.get("timetable")

        try:
            timetable = _load_timetable_from_request(file)
            engine = SwapEngine(timetable)

            periods = _parse_periods(form["periods"])
            absent_teachers = _parse_absent(form["absent"])
            rows = engine.suggest_swaps(absent_teachers, form["day"], periods)
        except Exception as exc:
            error = str(exc)

    return render_template(
        "index.html",
        days=DAYS,
        rows=rows,
        error=error,
        form=form,
        default_timetable=str(DEFAULT_TIMETABLE_PATH),
        default_file_exists=default_file_exists,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
