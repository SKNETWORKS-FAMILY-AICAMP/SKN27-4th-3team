const ENDING_COPY = {
  win: {
    kicker: "진명 선언 완료",
    title: "엘리자베스가 해방되었다",
    summary: "이안이 이름을 부르는 순간, 검은 실은 재처럼 풀리고 진실의 거울은 산산조각 났다. 창밖으로 밝은 아침이 스며들고, 유리 파편 속에는 온전한 이안의 얼굴만 남았다."
  },
  lose: {
    sanity: {
      kicker: "이성 붕괴",
      title: "이안의 목소리가 바뀌었다",
      summary: "마지막 빈칸은 끝내 채워지지 않았다. 거울 속 미소가 이안의 얼굴 위에 남았고, 안쪽의 것은 다시 그의 손을 빌려 밤을 걷기 시작했다."
    },
    curse: {
      kicker: "저주 잠식",
      title: "검은 실이 손목을 넘었다",
      summary: "저주 흔적은 손목에서 멈추지 않았다. 검은 실은 기억과 의지를 함께 묶었고, 거울은 더 이상 온전한 얼굴을 비추지 않았다."
    },
    turns: {
      kicker: "자정 종료",
      title: "마지막 빈칸을 채우지 못했다",
      summary: "열두 번째 턴이 끝났지만 기록은 완성되지 않았다. 다락방의 일기장은 다시 닫혔고, 안쪽의 것은 이안의 안에서 조용히 눈을 떴다."
    },
    unknown: {
      kicker: "사건 종료",
      title: "기록이 흐려졌다",
      summary: "마지막 기록은 번졌고, 의식장에 남은 단서들은 끝내 하나의 이름으로 이어지지 못했다."
    }
  }
};

const params = new URLSearchParams(window.location.search);
const outcome = params.get("outcome") || "unfinished";
const reason = params.get("reason") || "unknown";
const copy = outcome === "win"
  ? ENDING_COPY.win
  : (ENDING_COPY.lose[reason] || ENDING_COPY.lose.unknown);

const frame = document.querySelector("[data-ending-frame]");
const kicker = document.querySelector("[data-ending-kicker]");
const title = document.querySelector("[data-ending-title]");
const summary = document.querySelector("[data-ending-summary]");

if (frame) frame.dataset.outcome = outcome === "win" ? "win" : "lose";
if (kicker) kicker.textContent = copy.kicker;
if (title) title.textContent = copy.title;
if (summary) summary.textContent = copy.summary;

function setText(selector, value) {
  const target = document.querySelector(selector);
  if (target) target.textContent = value || "--";
}

setText("[data-ending-turn]", params.get("turn"));
setText("[data-ending-truth]", params.get("truth"));
setText("[data-ending-sanity]", params.get("sanity"));
setText("[data-ending-curse]", params.get("curse"));
