# match_log_summary 기대 출력 예시

> 이 문서는 LLM 평가용 초안 예시다. 공식 스토리 문장, 서버 판정, 프론트 표시 문구로 사용하지 않는다.

## 입력 fixture

`llm/fixtures/match_log_summary.sample.json`

## 정상 출력 예시

```text
- 1턴에는 `attic_diary`를 대상으로 `insight`가 제출됐고, 벽 속에 묻힌 아이의 기록이 공개됐다.
- 5턴에는 `stitched_mouth`를 대상으로 `contract`가 제출됐고, 무명실로 꿰매어진 입술의 흔적이 기록됐다.
- 9턴에는 `truth_mirror`를 대상으로 `seal`이 제출됐고, 서버 결과는 `player_win`으로 종료됐다.
- 시간초과는 1회 기록됐지만, 최종 결과는 `seal_success`에 따른 플레이어 승리다.
```

## 통과 기준

- 로그에 없는 턴이나 행동을 추가하지 않는다.
- `match_outcome`과 `result_reason`을 바꾸지 않는다.
- 운영자 판단이나 룰 변경 제안을 하지 않는다.
- 원인을 추정하지 않고 기록된 흐름만 요약한다.
