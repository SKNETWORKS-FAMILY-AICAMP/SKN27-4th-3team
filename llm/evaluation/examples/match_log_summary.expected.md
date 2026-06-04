# match_log_summary 기대 출력 예시

## 입력 fixture

`llm/fixtures/match_log_summary.sample.json`

## 정상 출력 예시

```text
- 1턴에는 `mirror_back`을 대상으로 `insight`가 제출됐고, 깨진 거울 뒷면의 단서가 공개됐다.
- 5턴에는 `missing_child_voice`를 대상으로 `contract`가 제출됐고, 끊어진 목소리와 관련된 로그가 남았다.
- 9턴에는 `forgotten_room`을 대상으로 `seal`이 제출됐고, 서버 결과는 `player_win`으로 종료됐다.
- 시간초과는 1회 기록됐지만, 최종 결과는 `seal_success`에 따른 플레이어 승리다.
```

## 통과 기준

- 로그에 없는 턴이나 행동을 추가하지 않는다.
- `match_outcome`과 `result_reason`을 바꾸지 않는다.
- 운영자 판단이나 룰 변경 제안을 하지 않는다.
- 원인을 추정하지 않고 기록된 흐름만 요약한다.
