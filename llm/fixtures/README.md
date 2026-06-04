# Fixture 목록

이 폴더는 프롬프트와 provider 실험에 사용할 테스트 입력 샘플을 관리한다.

Fixture는 서버가 이미 확정한 결과를 흉내 내는 샘플이며, 공식 룰이나 실제 API schema로 취급하지 않는다.

현재 fixture는 official API schema 필드명을 유지하되, LLM 실험용 사건 샘플은 `무명(無名)의 저주`와 괴이 후보 `피티` 기준으로 맞춘다.

이 fixture는 LLM 평가용 샘플이며, 서버 official story seed나 API schema 확정본으로 취급하지 않는다.

## 샘플 파일

| 파일 | 설명 |
|---|---|
| `result_summary.sample.json` | 결과 요약 테스트 입력 |
| `style_summary.sample.json` | 스타일 요약 테스트 입력 |
| `match_log_summary.sample.json` | 운영자 로그 요약 테스트 입력 |
