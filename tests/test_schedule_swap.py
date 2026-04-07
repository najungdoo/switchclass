import io
import unittest

from schedule_swap import Timetable, SwapEngine


CSV_TEXT = """teacher,day,period,class,subject
김진욱,월,1,3-3,로인
김주혁,월,1,2-5,영어
송치용,월,2,1-1,세무회계
김은진,월,2,한알,음악
강서영,월,3,1-2,정보
"""


class ScheduleSwapTests(unittest.TestCase):
    def test_parse_csv_and_find_absent_lessons(self):
        timetable = Timetable.from_csv_obj(io.StringIO(CSV_TEXT))
        engine = SwapEngine(timetable)

        missing = engine.find_absent_lessons(["김진욱", "김주혁"], "월", [1, 2])
        self.assertEqual(len(missing), 2)
        self.assertEqual({m.teacher for m in missing}, {"김진욱", "김주혁"})

    def test_suggest_swaps_returns_substitute(self):
        timetable = Timetable.from_csv_obj(io.StringIO(CSV_TEXT))
        engine = SwapEngine(timetable)

        rows = engine.suggest_swaps(["김진욱"], "월", [1])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["absent_teacher"], "김진욱")
        self.assertIn("substitute_teacher", rows[0])
        self.assertNotEqual(rows[0]["substitute_teacher"], "대체교사 없음")

    def test_invalid_day_raises_error(self):
        with self.assertRaises(ValueError):
            Timetable.from_csv_obj(
                io.StringIO(
                    "teacher,day,period,class,subject\n김진욱,토,1,3-3,로인\n"
                )
            )


if __name__ == "__main__":
    unittest.main()
