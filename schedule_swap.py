from __future__ import annotations

import argparse
import csv
import io
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Tuple

DAYS = ["월", "화", "수", "목", "금"]


@dataclass
class Lesson:
    teacher: str
    day: str
    period: int
    class_name: str
    subject: str


class Timetable:
    """교사별 주간 시간표를 관리한다.

    CSV 형식:
    teacher,day,period,class,subject
    김진욱,월,1,3-3,로인
    """

    def __init__(self, lessons: List[Lesson]):
        self.lessons = lessons
        self.by_slot: Dict[Tuple[str, int], List[Lesson]] = defaultdict(list)
        self.by_teacher_slot: Dict[Tuple[str, str, int], Lesson] = {}
        self.by_teacher: Dict[str, List[Lesson]] = defaultdict(list)

        for lesson in lessons:
            slot = (lesson.day, lesson.period)
            self.by_slot[slot].append(lesson)
            self.by_teacher_slot[(lesson.teacher, lesson.day, lesson.period)] = lesson
            self.by_teacher[lesson.teacher].append(lesson)

    @classmethod
    def from_csv_obj(cls, csv_obj: io.StringIO) -> "Timetable":
        lessons: List[Lesson] = []
        reader = csv.DictReader(csv_obj)
        required = {"teacher", "day", "period", "class", "subject"}
        if not required.issubset(reader.fieldnames or set()):
            raise ValueError(
                "CSV 헤더는 teacher,day,period,class,subject 를 포함해야 합니다."
            )
        for row in reader:
            day = row["day"].strip()
            if day not in DAYS:
                raise ValueError(f"지원하지 않는 요일: {day}")
            lessons.append(
                Lesson(
                    teacher=row["teacher"].strip(),
                    day=day,
                    period=int(row["period"]),
                    class_name=row["class"].strip(),
                    subject=row["subject"].strip(),
                )
            )
        return cls(lessons)

    @classmethod
    def from_csv(cls, path: str) -> "Timetable":
        with open(path, newline="", encoding="utf-8") as f:
            return cls.from_csv_obj(io.StringIO(f.read()))


class SwapEngine:
    """출장 교사 수업의 대체 교사를 추천한다.

    추천 점수(낮을수록 우선):
    1) 동일 과목을 가르치는 교사 우선
    2) 이미 같은 날 대체가 많은 교사는 후순위
    """

    def __init__(self, timetable: Timetable):
        self.timetable = timetable

    def find_absent_lessons(
        self, absent_teachers: List[str], day: str, periods: List[int]
    ) -> List[Lesson]:
        missing: List[Lesson] = []
        for teacher in absent_teachers:
            for period in periods:
                lesson = self.timetable.by_teacher_slot.get((teacher, day, period))
                if lesson:
                    missing.append(lesson)
        return missing

    def available_teachers(self, day: str, period: int) -> List[str]:
        busy = {lesson.teacher for lesson in self.timetable.by_slot.get((day, period), [])}
        return sorted(set(self.timetable.by_teacher) - busy)

    def suggest_swaps(
        self, absent_teachers: List[str], day: str, periods: List[int]
    ) -> List[Dict[str, str]]:
        absent_lessons = self.find_absent_lessons(absent_teachers, day, periods)
        substitute_load: Dict[str, int] = defaultdict(int)
        suggestions: List[Dict[str, str]] = []

        for missing in sorted(absent_lessons, key=lambda x: x.period):
            candidates = self.available_teachers(missing.day, missing.period)
            scored: List[Tuple[int, str]] = []

            for teacher in candidates:
                subject_match = 1
                for lesson in self.timetable.by_teacher[teacher]:
                    if lesson.subject == missing.subject:
                        subject_match = 0
                        break
                score = (subject_match * 10) + substitute_load[teacher]
                scored.append((score, teacher))

            if not scored:
                substitute = "대체교사 없음"
            else:
                scored.sort(key=lambda x: (x[0], x[1]))
                substitute = scored[0][1]
                substitute_load[substitute] += 1

            suggestions.append(
                {
                    "day": missing.day,
                    "period": str(missing.period),
                    "class": missing.class_name,
                    "subject": missing.subject,
                    "absent_teacher": missing.teacher,
                    "substitute_teacher": substitute,
                }
            )

        return suggestions


def render_table(rows: List[Dict[str, str]]) -> str:
    if not rows:
        return "대체가 필요한 수업이 없습니다."
    headers = ["요일", "교시", "학급", "과목", "출장교사", "대체교사"]
    keys = ["day", "period", "class", "subject", "absent_teacher", "substitute_teacher"]

    widths = [len(h) for h in headers]
    for row in rows:
        for i, key in enumerate(keys):
            widths[i] = max(widths[i], len(row[key]))

    def line(values: List[str]) -> str:
        return " | ".join(v.ljust(widths[i]) for i, v in enumerate(values))

    out = [line(headers), "-+-".join("-" * w for w in widths)]
    for row in rows:
        out.append(line([row[k] for k in keys]))
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description="출장 교사 수업교체 추천 프로그램")
    parser.add_argument("--csv", required=True, help="시간표 CSV 파일 경로")
    parser.add_argument("--day", required=True, choices=DAYS, help="요일 (월~금)")
    parser.add_argument(
        "--periods",
        required=True,
        help="출장 교시 목록 (예: 1,2,3)",
    )
    parser.add_argument(
        "--absent",
        required=True,
        help="출장 교사 이름 목록 (예: 김진욱,김주혁)",
    )

    args = parser.parse_args()

    periods = [int(p.strip()) for p in args.periods.split(",") if p.strip()]
    absent_teachers = [t.strip() for t in args.absent.split(",") if t.strip()]

    timetable = Timetable.from_csv(args.csv)
    engine = SwapEngine(timetable)
    rows = engine.suggest_swaps(absent_teachers, args.day, periods)
    print(render_table(rows))


if __name__ == "__main__":
    main()
