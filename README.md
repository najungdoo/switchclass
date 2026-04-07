# switchclass

상업계 특성화고 교사 출장 시 수업 교체를 빠르게 추천하는 프로그램입니다.

- `schedule_swap.py`: CLI 버전
- `web_app.py`: 교무실에서 클릭으로 사용할 수 있는 웹 UI 버전

## 1) 입력 파일 만들기

`sample_timetable.csv` 형식을 참고해 CSV 파일을 준비합니다.

필수 헤더:

- `teacher`: 교사명
- `day`: 요일 (`월`,`화`,`수`,`목`,`금`)
- `period`: 교시 숫자
- `class`: 학급
- `subject`: 과목

## 2) CLI 실행 방법

```bash
python3 schedule_swap.py --csv sample_timetable.csv --day 월 --periods 1,2,3 --absent 김진욱,김주혁
```

## 3) 웹 UI 실행 방법

```bash
pip install flask
python3 web_app.py
```

브라우저에서 `http://localhost:5000` 접속 후,

1. 시간표 CSV 업로드
2. 요일 선택
3. 출장 교시 입력(예: `1,2,3`)
4. 출장 교사 입력(예: `김진욱,김주혁`)
5. **대체교사 추천** 버튼 클릭

## 4) 추천 로직

- 동일 교시에 수업이 없는 교사만 후보로 선택
- 결강 과목을 이미 담당하는 교사를 우선 추천
- 같은 날 대체 배정이 많은 교사는 후순위
