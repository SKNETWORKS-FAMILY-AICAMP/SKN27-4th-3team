# 프롬프트 목록

이 폴더는 LLM purpose별 프롬프트 초안을 관리한다.

프롬프트는 서버 판정 결과를 바꾸지 않고, 이미 확정된 결과를 읽기 쉬운 문장으로 정리하는 데만 사용한다.

실제 Groq 호출에 사용되는 실행 프롬프트는 `prompt_templates.py`에서 조립한다.

`*.md` 파일은 팀원 검토와 설계 설명용 문서다.

fixture 또는 서버 결과를 prompt로 조립하는 규칙은 `prompt_assembly.md`를 따른다.

## purpose 초안

| purpose | 설명 | 파일 |
|---|---|---|
| `result_summary` | 결과 화면용 서사 요약 | `result_summary.md` |
| `style_summary` | 플레이 스타일 요약 문장 | `style_summary.md` |
| `match_log_summary` | 운영자용 매치 로그 요약 | `match_log_summary.md` |
| `turn_flavor_text` | 단일 턴 화면 연출 문구 | `turn_flavor_text.md` |

## 실행 프롬프트 코드

| 파일 | 역할 |
|---|---|
| `prompt_templates.py` | 실제 adapter가 import하는 프롬프트 조립 코드 |
