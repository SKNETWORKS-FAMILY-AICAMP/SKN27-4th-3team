# 무료/저비용 LLM Provider 후보

이 문서는 OpenAI 유료 API를 사용하지 않는 방향에서 검토할 provider 후보를 정리한다.

## 후보

| provider | 장점 | 확인 필요 |
|---|---|---|
| Hugging Face | 무료 모델 선택지가 많고 모델 교체가 쉽다. | 무료 quota, 응답 속도, 한국어 품질 |
| Groq | 빠른 추론 속도가 장점이다. | 무료 quota, 사용 가능한 모델, API 정책 |
| 기타 무료 API | 비용 부담이 낮다. | 안정성, 개인정보 처리, rate limit |

## 선택 기준

- 무료 또는 저비용으로 MVP 실험이 가능하다.
- API key와 model id를 환경 변수로 주입할 수 있다.
- 한국어 요약 품질이 MVP 결과 화면에 사용할 수 있는 수준이다.
- 장애 시 fallback 문장으로 자연스럽게 대체할 수 있다.
- 게임 판정 로직과 분리해서 사용할 수 있다.

## 보류 사항

- 최종 provider
- 기본 model id
- generation log 보존 기간
- LLM 결과를 백엔드에 저장할 schema
