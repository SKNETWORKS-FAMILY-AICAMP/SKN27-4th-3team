const RESULT_COPY = {
  win: {
    kicker: "봉인 성공",
    title: "CLEAR",
    outcome: "승리",
    summary: "진명은 완성되었고, 거울 속의 손님은 봉인된 문장 안에 갇혔다.",
    style: "핵심 단서를 모아 봉인 조건을 완성한 플레이입니다."
  },
  lose: {
    sanity: {
      kicker: "이성 붕괴",
      title: "GAME OVER",
      outcome: "패배",
      summary: "진명은 끝내 완성되지 못했고, 거울은 또 하나의 얼굴을 가져갔다.",
      style: "이성 손실을 감수하며 의식을 진행한 플레이입니다."
    },
    curse: {
      kicker: "저주 잠식",
      title: "GAME OVER",
      outcome: "패배",
      summary: "저주의 흔적이 한계를 넘었고, 마지막 기록은 오염된 채 닫혔다.",
      style: "강한 행동의 대가가 누적된 플레이입니다."
    },
    turns: {
      kicker: "턴 종료",
      title: "GAME OVER",
      outcome: "패배",
      summary: "정해진 턴 안에 봉인을 완성하지 못했다.",
      style: "탐색과 방어에 시간이 많이 쓰인 플레이입니다."
    },
    unknown: {
      kicker: "사건 종료",
      title: "GAME OVER",
      outcome: "패배",
      summary: "사건 파일은 미완의 기록으로 닫혔다.",
      style: "결과 원인을 확인할 수 없는 프로토타입 기록입니다."
    }
  }
};

const params = new URLSearchParams(window.location.search);
const outcome = params.get("outcome") || "lose";
const reason = params.get("reason") || "unknown";
const copy = outcome === "win"
  ? RESULT_COPY.win
  : (RESULT_COPY.lose[reason] || RESULT_COPY.lose.unknown);

const llmResultSummary = params.get("result_summary");
const llmStyleSummary = params.get("style_summary");

function setText(selector, value) {
  const target = document.querySelector(selector);
  if (target) target.textContent = value || "--";
}

const page = document.querySelector("[data-result-page]");
if (page) page.dataset.outcome = outcome === "win" ? "win" : "lose";

setText("[data-result-kicker]", copy.kicker);
setText("[data-result-title]", copy.title);
setText("[data-result-summary]", llmResultSummary || copy.summary);
setText("[data-result-outcome]", copy.outcome);
setText("[data-result-turn]", params.get("turn"));
setText("[data-result-sanity]", params.get("sanity"));
setText("[data-result-curse]", params.get("curse"));
setText("[data-result-truth]", params.get("truth"));
setText("[data-result-log]", params.get("log") || "프로토타입 공개 로그가 아직 저장되지 않았습니다.");
setText("[data-result-style]", llmStyleSummary || copy.style);
