from __future__ import annotations

import io
from typing import List

from flask import Flask, render_template, request

from schedule_swap import DAYS, SwapEngine, Timetable

app = Flask(__name__)


def _parse_periods(raw: str) -> List[int]:
    return [int(p.strip()) for p in raw.split(",") if p.strip()]


def _parse_absent(raw: str) -> List[str]:
    return [t.strip() for t in raw.split(",") if t.strip()]


@app.route("/", methods=["GET", "POST"])
def index():
    rows = []
    error = ""
    form = {
        "day": "월",
        "periods": "1,2,3",
        "absent": "",
    }

    if request.method == "POST":
        form["day"] = request.form.get("day", "월")
        form["periods"] = request.form.get("periods", "")
        form["absent"] = request.form.get("absent", "")
        file = request.files.get("timetable")

        try:
            if not file or not file.filename:
                raise ValueError("시간표 CSV 파일을 업로드해주세요.")

            content = file.read().decode("utf-8")
            timetable = Timetable.from_csv_obj(io.StringIO(content))
            engine = SwapEngine(timetable)

            periods = _parse_periods(form["periods"])
            absent_teachers = _parse_absent(form["absent"])
            rows = engine.suggest_swaps(absent_teachers, form["day"], periods)
        except Exception as exc:
            error = str(exc)

    return render_template("index.html", days=DAYS, rows=rows, error=error, form=form)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
