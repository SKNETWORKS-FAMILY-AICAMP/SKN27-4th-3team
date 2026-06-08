import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import styles from "./ResultScreen.module.css";

const RESULT_COPY = {
  win: {
    kicker: "사건 종료 기록",
    title: "봉인 성공",
    outcome: "클리어",
    summary: "진명 조각이 맞물렸고, 거울 속의 손님은 더는 이안의 기억을 붙잡지 못했다.",
    style: "단서를 모아 봉인 조건을 완성한 플레이 기록입니다.",
  },
  lose: {
    sanity: {
      kicker: "사건 종료 기록",
      title: "이성 붕괴",
      outcome: "게임 오버",
      summary: "이안의 정신이 버티지 못했고, 거울은 남은 기억을 삼켰다.",
      style: "이성 손실을 감수하며 의식을 밀어붙인 플레이 기록입니다.",
    },
    curse: {
      kicker: "사건 종료 기록",
      title: "저주 잠식",
      outcome: "게임 오버",
      summary: "저주의 흔적이 한계를 넘었고, 마지막 기록은 닫힌 채 남았다.",
      style: "강한 행동의 대가가 누적된 플레이 기록입니다.",
    },
    turns: {
      kicker: "사건 종료 기록",
      title: "시간 초과",
      outcome: "게임 오버",
      summary: "정해진 턴 안에 봉인을 완성하지 못했다.",
      style: "탐색과 방어에 많은 시간을 사용한 플레이 기록입니다.",
    },
    unknown: {
      kicker: "사건 종료 기록",
      title: "의식 실패",
      outcome: "게임 오버",
      summary: "사건 파일은 미완성 기록으로 닫혔다.",
      style: "결과 원인을 확정할 수 없는 프로토타입 기록입니다.",
    },
  },
};

function getCopy(outcome: string, reason: string) {
  if (outcome === "win") return RESULT_COPY.win;
  return RESULT_COPY.lose[reason as keyof typeof RESULT_COPY.lose] ?? RESULT_COPY.lose.unknown;
}

export function ResultScreen() {
  const navigate = useNavigate();
  const { matchId = "prototype-mirror-guest" } = useParams();
  const [searchParams] = useSearchParams();
  const outcome = searchParams.get("outcome") ?? "lose";
  const reason = searchParams.get("reason") ?? "unknown";
  const copy = getCopy(outcome, reason);
  const resultSummary = searchParams.get("result_summary") || copy.summary;
  const styleSummary = searchParams.get("style_summary") || copy.style;
  const publicLog = searchParams.get("log") || "저장된 공개 로그가 없습니다.";

  return (
    <main className={styles.screen} data-outcome={outcome === "win" ? "win" : "lose"}>
      <section className={styles.panel} aria-labelledby="result-title">
        <p className={styles.kicker}>{copy.kicker}</p>
        <h1 id="result-title">{copy.title}</h1>
        <p className={styles.summary}>{resultSummary}</p>

        <dl className={styles.stats} aria-label="최종 상태">
          <div>
            <dt>결과</dt>
            <dd>{copy.outcome}</dd>
          </div>
          <div>
            <dt>턴</dt>
            <dd>{searchParams.get("turn") || "--"}</dd>
          </div>
          <div>
            <dt>이성</dt>
            <dd>{searchParams.get("sanity") || "--"}</dd>
          </div>
          <div>
            <dt>저주</dt>
            <dd>{searchParams.get("curse") || "--"}</dd>
          </div>
          <div>
            <dt>진명</dt>
            <dd>{searchParams.get("truth") || "--"}</dd>
          </div>
        </dl>

        <section className={styles.record} aria-labelledby="public-log-title">
          <h2 id="public-log-title">공개 로그</h2>
          <p>{publicLog}</p>
        </section>

        <section className={styles.record} aria-labelledby="style-title">
          <h2 id="style-title">플레이 요약</h2>
          <p>{styleSummary}</p>
        </section>

        <div className={styles.actions}>
          <button type="button" onClick={() => navigate(`/matches/${matchId}`, { state: { fromPrologueTransition: true } })}>
            다시 의식장으로
          </button>
          <button type="button" onClick={() => navigate("/lobby")}>
            로비로 돌아가기
          </button>
        </div>
      </section>
    </main>
  );
}
