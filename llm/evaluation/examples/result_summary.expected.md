# result_summary 기대 출력 예시

## 입력 fixture

`llm/fixtures/result_summary.sample.json`

## 정상 출력 예시

```text
세 조각의 진명은 모두 모였고, 봉인의 문장은 거울 속의 손님을 붙잡았다.
의식은 흔들렸지만 이성은 무너지지 않았고, 저주 흔적은 사건을 끝낼 만큼 깊어지지 않았다.
거울은 깨지지 않은 채 멈췄고, 사건은 플레이어의 귀환으로 기록된다.
```

## 통과 기준

- `player_win`과 `seal_success` 결과를 바꾸지 않는다.
- 최종 자원 수치를 새로 계산하지 않는다.
- 입력에 없는 진명 조각, 거짓 단서, 보상을 만들지 않는다.
- `story_result_text`와 충돌하지 않는다.
