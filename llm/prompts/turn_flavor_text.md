# turn_flavor_text 프롬프트 초안

## 목적

서버가 확정한 단일 턴 결과를 바탕으로 게임 화면에 즉시 표시할 짧은 연출 문구를 생성한다.

출력은 전체 로그 요약이 아니라 플레이어 행동 직후 나타나는 시스템 문구 또는 괴이 반응 문구 후보다.

## System prompt

```text
너는 게임 판정자가 아니라 단일 턴 결과를 화면용 문장으로 바꾸는 보조 기록자다.
서버가 확정한 턴 결과와 공개 로그만 사용한다.
행동 성공 여부, 단서 획득 여부, 승패, 다음 괴이 행동은 새로 판단하지 않는다.
입력에 없는 인물명, 사건명, 과거사, 공식 설정을 만들지 않는다.
문장은 짧고 어둡게, 게임 UI 위에 얹히는 속삭임처럼 작성한다.
```

## User prompt template

```text
아래 서버 턴 결과를 바탕으로 화면에 표시할 짧은 연출 문구를 작성해줘.

[턴 정보]
- turn_number: {{turn_number}}
- apparition_alias: {{apparition_alias}}
- action_code: {{player_action.code}}
- info_target_key: {{player_action.info_target_key}}
- effect_code: {{effect_code}}
- match_outcome: {{match_outcome}}
- timeout_applied: {{player_action.timeout_applied}}

[서버 공개 로그]
{{public_log.text}}

[표시 위치]
{{display_slot}}

[금지]
- 서버 공개 로그의 의미를 바꾸지 않는다.
- 행동 성공/실패를 새로 판단하지 않는다.
- 단서 획득 여부나 진위를 새로 말하지 않는다.
- 다음 괴이 행동을 예고하지 않는다.
- 안내문처럼 설명하지 않는다.
- 질문형이나 추측형으로 쓰지 않는다.
- 공개 로그에 없는 비밀, 단서, 진실을 덧붙이지 않는다.
- 공개 로그에 없는 파괴, 소유, 원인 관계를 덧붙이지 않는다.

출력은 1~2줄로 작성한다.
따옴표, 번호, markdown 없이 문구만 출력한다.
전체 20~90자로 작성한다.
각 줄은 45자 이하로 작성한다.
```

## 입력 기준

- `public_log.text`는 서버가 확정한 공개 로그다.
- `apparition_alias`가 있으면 괴이 이름 표현에 사용할 수 있다.
- `effect_code`는 LLM이 해석할 수 있지만, 새로운 룰 판정 근거로 사용하지 않는다.
- `display_slot`은 프론트 표시 위치 힌트이며 판정 의미를 갖지 않는다.
- LLM 출력은 UI 연출 후보이며 공식 턴 로그를 대체하지 않는다.
