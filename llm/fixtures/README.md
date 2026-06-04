# Fixture 목록

이 폴더는 프롬프트와 provider 실험에 사용할 테스트 입력 샘플을 관리한다.

Fixture는 서버가 이미 확정한 결과를 흉내 내는 샘플이며, 공식 룰이나 실제 API schema로 취급하지 않는다.

현재 fixture는 official API schema 필드명과 기존 `거울 속의 손님` 기준을 맞춘 샘플이다.

`llm/docs/demo_story_reference.md`의 데모 스토리는 아직 fixture 기준을 대체하지 않는다.

데모 스토리 반영 fixture는 스토리 확정 후 별도로 작성한다.

## 샘플 파일

| 파일 | 설명 |
|---|---|
| `result_summary.sample.json` | 결과 요약 테스트 입력 |
| `style_summary.sample.json` | 스타일 요약 테스트 입력 |
| `match_log_summary.sample.json` | 운영자 로그 요약 테스트 입력 |
