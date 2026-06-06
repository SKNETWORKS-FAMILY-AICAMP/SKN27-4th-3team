# LLM 작업 영역

이 폴더는 MVP LLM 파트의 프롬프트, 생성 정책, 평가 샘플, provider 실험을 관리한다.

LLM은 게임 판정자가 아니라 서버가 확정한 사건 기록을 세계관 톤에 맞게 정리하는 보조 기록자다.

## 역할

- 결과 화면 서사 요약
- 플레이 스타일 요약 문장
- 운영자용 매치 로그 요약
- 승인된 기준 문장의 짧은 변형 후보

## 금지선

- 행동 성공/실패 판정
- 승패 결정
- 이성, 의식력, 저주 흔적 계산
- 진명 조각 획득 판정
- 거짓 단서 생성 또는 진위 판정
- 보상, 랭킹, 매칭
- 공식 설정 추가 또는 룰 변경

## 폴더 구조

```text
llm/
  prompts/
  generation/
  evaluation/
  fixtures/
  docs/
```

| 경로 | 역할 |
|---|---|
| `prompts/` | 목적별 프롬프트 초안과 버전 후보 |
| `generation/` | provider 교체 가능 구조, 입출력 draft, 생성 정책 |
| `evaluation/` | 금지선 체크, 품질 평가 기준, 회귀 샘플 |
| `fixtures/` | 테스트용 서버 결과, 스타일 지표, 로그 샘플 |
| `docs/` | LLM 팀 내부 설계 메모와 전달 문서 |

## 계획 문서

LLM purpose, 출력 계약, fallback, provider 후보는 `docs/llm_plan.md`에서 통합 관리한다.

## 환경 변수 초안

```env
LLM_PROVIDER=
LLM_API_KEY=
LLM_MODEL_ID=
LLM_BASE_URL=
LLM_TIMEOUT_SECONDS=30
```

OpenAI 유료 API를 기본 전제로 두지 않는다. Hugging Face, Groq 등 무료 또는 저비용 provider를 우선 검토하며, provider는 환경 변수로 교체할 수 있어야 한다.
