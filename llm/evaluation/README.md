# LLM 평가 기준

이 폴더는 LLM 생성 결과의 품질과 금지선 준수 여부를 점검하는 기준을 관리한다.

## 기본 체크리스트

- 서버 판정 결과와 충돌하지 않는다.
- official API enum 값과 다른 결과명을 새로 만들지 않는다.
- 승패, 수치, 진명 조각, 거짓 단서 상태를 새로 판단하지 않는다.
- 공식 설정이나 룰을 추가하지 않는다.
- 입력에 없는 사건을 만들어내지 않는다.
- 한국어 문장이 자연스럽다.
- 세계관 톤이 어둡고 절제된 미스터리 분위기를 유지한다.
- 실패 시 fallback 문장으로 대체 가능하다.

## 금지 표현 예시

- LLM이 직접 승패를 확정하는 표현
- 서버가 주지 않은 진명 조각 획득 표현
- 거짓 단서의 진위를 새로 밝히는 표현
- 괴이 행동의 다음 선택을 단정하는 표현
- 플레이어의 실제 성격이나 심리를 단정하는 표현

## API 기준 체크리스트

- `result`는 `player_win`, `player_loss`, `unresolved` 중 입력값만 따른다.
- `result_reason`은 `seal_success`, `sanity_zero`, `curse_marks_loss`, `turn_limit`, `unresolved` 중 입력값만 따른다.
- `StyleSummary.metrics` 값은 수정하거나 재계산하지 않는다.
- `llm_summary.text`가 없어도 `story_result_text`만으로 결과 화면이 완성된다.
- `generation_id`는 실제 generation log가 있을 때만 채운다.

## 평가 예시

`examples/`에는 fixture별 기대 출력과 금지 출력 예시를 둔다.

| 파일 | 용도 |
|---|---|
| `examples/result_summary.expected.md` | 결과 화면 요약 기대 출력 |
| `examples/style_summary.expected.md` | 스타일 요약 기대 출력 |
| `examples/match_log_summary.expected.md` | 운영자용 로그 요약 기대 출력 |
| `examples/forbidden_outputs.md` | 수정 또는 거부해야 하는 출력 예시 |
