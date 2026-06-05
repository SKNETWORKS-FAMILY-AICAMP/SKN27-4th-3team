/*
  LLM EDIT GUIDE
  - Change GAME_RULES for numbers such as max turn, sanity, soulfire, and timer.
  - Change ACTION_CARDS when replacing ritual actions or tool art.
  - Replace resolveTurnResult() only when wiring a real turn-result provider.
  - Keep enemy action hidden until the turn result has returned.
  - Keep result text split into reveal, judgment, state, changes, and flavor sections.
*/

const GAME_RULES = {
  maxTurn: 12,
  timerSeconds: 25,
  maxSanity: 12,
  maxSoulfire: 5,
  maxCurseTrace: 5,
  maxFalseClues: 3,
  startingSanity: 12,
  startingSoulfire: 5,
  startingCurse: 0,
  sealRequiredTrueNamePieces: 3
};

const ENDING_SCREEN = {
  href: "ending.html",
  delayMs: 3600
};

const ACTION_CARDS = {
  silence: {
    title: "침묵",
    kicker: "검은 초",
    cost: 0,
    type: "방해",
    symbol: "초",
    image: "assets/action-card-silence.png",
    desc: "거울 안쪽의 속삭임을 끊고 다음 턴 의식력을 1 회복한다.",
    playerLine: "말하지 마. 네 목소리도, 내 안의 목소리도.",
    briefing: "검은 초가 낮게 타오른다. 거울 안쪽에서 번지던 속삭임이 잠시 멀어지고, 이안은 자신의 숨소리를 되찾는다."
  },
  guard: {
    title: "수호",
    kicker: "소금 접시",
    cost: 1,
    type: "방어",
    symbol: "소금",
    image: "assets/salt-dish.png",
    desc: "저주 피해를 줄이고 보호막을 얻는다.",
    playerLine: "여기서 멈춰. 이 몸은 네 것이 아니야.",
    briefing: "소금의 선이 탁자 위에 번진다. 은도금 거울 가장자리에서 서늘한 균열이 잠시 멈춘다."
  },
  curse: {
    title: "저주",
    kicker: "녹슨 못",
    cost: 2,
    type: "공격",
    symbol: "못",
    image: "assets/action-card-curse.png",
    desc: "거울 안쪽의 힘을 밀어내지만 저주 흔적이 깊어질 수 있다.",
    playerLine: "이 고통을 다시 누군가에게 박아 넣게 두지 않겠어.",
    briefing: "녹슨 못이 탁자에 박히자 거울 속 형상이 뒤틀린다. 소리 없는 파문이 은빛 표면을 흔든다."
  },
  contract: {
    title: "계약",
    kicker: "피 묻은 서약서",
    cost: 3,
    type: "정보",
    symbol: "서약",
    image: "assets/action-card-contract.png",
    desc: "대가를 걸고 기록의 빈칸을 열어 진명 조각을 찾는다.",
    playerLine: "대가가 필요하다면 치르겠어. 대신 빈칸 하나는 열어야 해.",
    briefing: "피 묻은 서약서 위로 낡은 인장이 눌린다. 오래 닫혀 있던 문장 일부가 검은 잉크처럼 다시 떠오른다."
  },
  insight: {
    title: "간파",
    kicker: "깨진 유리 조각",
    cost: 1,
    type: "정보",
    symbol: "눈",
    image: "assets/action-card-insight.png",
    desc: "단서의 진위 또는 괴이의 공개된 반응 징후를 확인한다.",
    playerLine: "거울이 비추는 게 내 얼굴이 아니라면, 그 안의 진짜를 보겠어.",
    briefing: "깨진 유리 조각이 차갑게 빛난다. 이안의 얼굴 뒤편으로 설명할 수 없는 그림자가 겹쳐진다."
  },
  deceive: {
    title: "속임수",
    kicker: "위조 메모",
    cost: 1,
    type: "교란",
    symbol: "잉크",
    image: "assets/action-card-deceive.png",
    desc: "뒤틀린 문장과 위조 단서로 거울 안쪽의 간파를 흐린다.",
    playerLine: "문장은 믿을 수 없어. 지금은 틀린 길을 먼저 보이게 해야 해.",
    briefing: "잉크 번진 메모들이 탁자 위에서 어긋난 순서로 겹친다. 거울 안쪽의 시선이 잠시 잘못된 문장에 묶인다."
  },
  seal: {
    title: "봉인",
    kicker: "진명 선언",
    cost: 2,
    type: "조건부",
    symbol: "명",
    image: "assets/seal-card.png",
    desc: "진명 조각 3개가 모였을 때 마지막 이름을 선언한다.",
    playerLine: "엘리자베스. 이제 거울 안쪽에서 나오지 않아도 돼.",
    briefing: "이름이 거울 앞에 떨어진다. 검은 실이 재처럼 풀리고, 은빛 표면 전체에 거미줄 같은 금이 번진다."
  }
};

const ENEMY_ACTIONS = [
  { key: "deceive", label: "속임수", action: "괴이 행동: 속임수", line: "넌 이미 알고 있어. 모르는 척할 뿐이지." },
  { key: "silence", label: "침묵", action: "괴이 행동: 침묵", line: "보지 마." },
  { key: "contract", label: "계약", action: "괴이 행동: 계약", line: "빈칸은 네 안에 있어." },
  { key: "insight", label: "간파", action: "괴이 행동: 간파", line: "네 손이 먼저 기억할 거야." },
  { key: "curse", label: "저주", action: "괴이 행동: 저주", line: "잘했어. 계속해." },
  { key: "guard", label: "수호", action: "괴이 행동: 수호", line: "닫힌 곳은 조용해." }
];

const CARD_VISUAL_COPY = {
  silence: {
    card: {
      title: "침묵",
      kicker: "날개 달린 사슴",
      symbol: "날개",
      desc: "침묵 카드. 검은 날개를 펼친 사슴 형상이 거울의 목소리를 잠시 덮어 다음 턴 혼불을 1 회복한다.",
      playerLine: "침묵을 고른다. 검은 날개가 접히는 동안, 거울 안쪽의 숨소리도 잠시 멎는다.",
      briefing: "침묵의 그림, 검은 날개가 카드 위에서 천천히 접힌다. 그 그림자가 거울 면을 스치자 안쪽의 속삭임이 한 박자 늦어지고, 남은 혼불이 다시 살아난다."
    },
    enemy: {
      label: "침묵 / 검은 날개",
      action: "괴이 행동: 침묵 / 검은 날개",
      line: "날개 아래에 숨으면 네 목소리도 보이지 않겠지."
    }
  },
  curse: {
    card: {
      title: "저주",
      kicker: "마른 가지의 형틀",
      symbol: "십자가",
      desc: "저주 카드. 가시처럼 뻗은 십자가가 거울 속 형상을 찌르지만, 저주의 흔적도 함께 깊어진다.",
      playerLine: "저주를 건다. 가시 십자가가 선다. 네가 숨은 곳을 찢어 보이게 하겠다.",
      briefing: "저주의 그림, 가시 십자가가 카드 중앙에 솟는다. 그 끝이 거울 면을 긁자 안쪽의 형상이 비틀리지만, 손목을 감은 저주도 더 세게 조인다."
    },
    enemy: {
      label: "저주 / 가시 십자가",
      action: "괴이 행동: 저주 / 가시 십자가",
      line: "그 십자가는 나보다 먼저 너를 찌를 거야."
    }
  },
  contract: {
    card: {
      title: "계약",
      kicker: "달 아래 선 후드",
      symbol: "후드",
      desc: "계약 카드. 달 아래 멈춰 선 순례자의 그림자가 기록을 들추어 진명 조각을 찾는다.",
      playerLine: "계약을 맺는다. 달의 순례자가 걷는다. 그 발자국 끝에서 이름의 조각을 찾겠다.",
      briefing: "계약의 그림, 달의 순례자가 달빛 속에서 한 걸음 앞으로 나온다. 검은 옷자락이 펼쳐질 때마다 오래 닫힌 기록의 문장이 다시 떠오른다."
    },
    enemy: {
      label: "계약 / 달의 순례자",
      action: "괴이 행동: 계약 / 달의 순례자",
      line: "달빛 아래 걷는 건 너야. 나는 네 그림자일 뿐."
    }
  },
  insight: {
    card: {
      title: "간파",
      kicker: "사슴뿔의 군주",
      symbol: "뿔",
      desc: "간파 카드. 뿔의 왕이 거울 안쪽을 정면으로 응시해 다음 징후와 거짓 단서를 가른다.",
      playerLine: "간파한다. 뿔의 왕이 고개를 든다. 네가 숨긴 진짜 징후를 보겠다.",
      briefing: "간파의 그림, 뿔의 왕이 달을 가른다. 왕관처럼 솟은 뿔 사이로 거울의 표면이 얇아지고, 흐릿했던 징후가 하나씩 윤곽을 얻는다."
    },
    enemy: {
      label: "간파 / 뿔의 왕",
      action: "괴이 행동: 간파 / 뿔의 왕",
      line: "왕관을 쓴 것은 나일까, 네 두려움일까."
    }
  },
  deceive: {
    card: {
      title: "기만",
      kicker: "달을 삼킨 나무",
      symbol: "고목",
      desc: "기만 카드. 뒤틀린 고목의 그림자가 거울의 시선을 흐려, 거짓 문장으로 괴이의 판단을 흔든다.",
      playerLine: "기만을 펼친다. 뒤틀린 고목이 달을 가린다. 이번에는 네가 잘못된 길을 보게 될 거다.",
      briefing: "기만의 그림, 뒤틀린 고목이 달빛을 갈라 먹는다. 카드 속 고목의 그림자가 책상 위로 번지자 거울 안쪽의 시선이 엉뚱한 문장을 따라 흔들린다."
    },
    enemy: {
      label: "기만 / 뒤틀린 고목",
      action: "괴이 행동: 기만 / 뒤틀린 고목",
      line: "나무가 휘어진 게 아니야. 네 기억이 휘어진 거지."
    }
  }
};

Object.entries(CARD_VISUAL_COPY).forEach(([key, copy]) => {
  if (ACTION_CARDS[key]) Object.assign(ACTION_CARDS[key], copy.card);
  const enemyAction = ENEMY_ACTIONS.find((action) => action.key === key);
  if (enemyAction) Object.assign(enemyAction, copy.enemy);
});

const ACTION_RULE_NOTES = {
  curse: "비용 2. 상대 이성 2 감소.",
  guard: "비용 1. 저주 피해 2 감소, 보호막 1 획득.",
  insight: "비용 1. 단서 판별 또는 상대 행동 성향 일부 확인.",
  deceive: "비용 1. 거짓 단서 생성, 간파 방해.",
  silence: "비용 0. 정보 공개 차단, 다음 턴 의식력 +1.",
  contract: "비용 3. 성공 시 진명 조각 또는 비밀 노출도 +1."
};

Object.entries(ACTION_RULE_NOTES).forEach(([key, note]) => {
  if (!ACTION_CARDS[key]) return;
  ACTION_CARDS[key].desc = note;
});

const FALSE_CLUE_RULES = [
  {
    id: "burn_teddy",
    text: "곰 인형을 태우면 저주는 사라진다.",
    targets: ["bloodied_teddy", "attic_diary"]
  },
  {
    id: "break_mirror",
    text: "거울을 깨면 더는 보지 않아도 된다.",
    targets: ["truth_mirror"]
  },
  {
    id: "revenge_justice",
    text: "그들이 사라져야 네가 조용해진다.",
    targets: ["stitched_mouth", "ian_reflection"],
    requiresTrueNamePieces: 2
  }
];

const INFO_TARGETS = [
  { key: "attic_diary", label: "다락방의 낡은 일기장" },
  { key: "truth_mirror", label: "안방의 은도금 거울" },
  { key: "stitched_mouth", label: "닫힌 입가의 형상" },
  { key: "bloodied_teddy", label: "피 묻은 곰 인형" },
  { key: "ian_reflection", label: "이안의 일그러진 반사" }
];

const OFFICIAL_ENDING_TEXT = {
  win: "사건 종료 기록.\n이안은 거울 앞에서 감춰진 이름을 불렀다. 엘리자베스를 붙잡던 검은 실은 재가 되어 흩어졌고, 진실의 거울은 산산조각 나며 저주를 놓아주었다.",
  loseSanity: "사건 종료 기록.\n이안은 끝내 자신의 목소리를 지키지 못했다. 거울 속 미소가 현실의 얼굴이 되었고, 안쪽의 것은 다시 이안의 손을 빌려 움직이기 시작했다.",
  loseCurse: "사건 종료 기록.\n저주 흔적이 손목을 넘어 온몸으로 번졌다. 검은 실은 이안의 의지를 묶었고, 거울은 더 이상 인간의 얼굴을 비추지 않았다.",
  loseTurns: "사건 종료 기록.\n자정이 지나도록 마지막 빈칸은 채워지지 못했다. 다락방의 기록은 다시 닫혔고, 안쪽의 것은 이안의 안에서 조용히 눈을 떴다."
};

const TRUTH_PIECES = [
  {
    id: "attic_diary",
    title: "다락방 기록의 첫 번째 공백",
    source: "attic_diary",
    reveal: "일기장은 오래 숨겨진 가족사의 공백을 가리킨다. 아직 누구의 이야기인지는 분명하지 않다."
  },
  {
    id: "truth_mirror",
    title: "거짓 얼굴을 벗기는 은도금 거울",
    source: "truth_mirror",
    reveal: "자정의 거울은 사람의 얼굴 뒤에 붙은 거짓된 표정을 억지로 벗긴다."
  },
  {
    id: "stitched_mouth",
    title: "닫힌 입가와 마지막 빈칸",
    source: "stitched_mouth",
    reveal: "닫힌 입가에는 말하지 못한 흔적이 남아 있다. 마지막 빈칸은 선언의 순간에만 입 밖으로 낼 수 있다."
  }
];

function getInfoTargetLabel(key) {
  return INFO_TARGETS.find((target) => target.key === key)?.label || key || "없음";
}

const dom = {
  frame: document.querySelector(".game-frame"),
  clock: document.querySelector("[data-clock]"),
  clockHand: document.querySelector(".clock-hand"),
  actionCard: document.querySelector("[data-action-card]"),
  ritualTools: [...document.querySelectorAll(".ritual-tool[data-action]")],
  ritualEffect: document.querySelector("[data-ritual-effect]"),
  sealInvocation: document.querySelector(".seal-invocation"),
  sealReason: document.querySelector("[data-seal-reason]"),
  sealInterference: document.querySelector("[data-seal-interference]"),
  sealInterferenceValue: document.querySelector("[data-seal-interference-value]"),
  playerLog: document.querySelector("[data-player-log]"),
  playerLogText: document.querySelector("[data-player-log-text]"),
  protagonistLogStack: document.querySelector("[data-protagonist-log-stack]"),
  systemLogStack: document.querySelector("[data-system-log-stack]"),
  spiritLogStack: document.querySelector("[data-spirit-log-stack]"),
  turnEndCue: document.querySelector("[data-turn-end-cue]"),
  dialogueArchiveToggle: document.querySelector("[data-dialogue-archive-toggle]"),
  dialogueArchivePanel: document.querySelector("[data-dialogue-archive-panel]"),
  dialogueArchiveClose: document.querySelector("[data-dialogue-archive-close]"),
  dialogueArchiveList: document.querySelector("[data-dialogue-archive-list]"),
  enemyVoice: document.querySelector("[data-enemy-voice]"),
  enemyAction: document.querySelector("[data-enemy-action]"),
  enemyText: document.querySelector("[data-enemy-voice-text]"),
  turnState: document.querySelector("[data-turn-state-label]"),
  turnCount: document.querySelector("[data-turn-count]"),
  soulfireToken: document.querySelector(".soulfire-token"),
  sanityToken: document.querySelector(".sanity-token"),
  curseToken: document.querySelector(".curse-token"),
  lanternSlots: [...document.querySelectorAll("[data-lantern-slot]")],
  sanityFill: document.querySelector("[data-sanity-fill]"),
  journal: document.querySelector("[data-clue-journal]"),
  journalToggle: document.querySelector("[data-journal-toggle]"),
  journalPanel: document.querySelector("#journal-panel"),
  journalClose: document.querySelector("[data-journal-close]"),
  journalCount: document.querySelector("[data-journal-count]"),
  truthProgress: document.querySelector("[data-truth-progress]"),
  truthList: document.querySelector("[data-truth-list]"),
  acquiredClues: document.querySelector("[data-acquired-clues]"),
  suspectClues: document.querySelector("[data-suspect-clues]"),
  falseClues: document.querySelector("[data-false-clues]"),
  lastInvestigation: document.querySelector("[data-last-investigation]"),
  shield: document.querySelector("[data-journal-shield]"),
  partial: document.querySelector("[data-journal-partial]"),
  suspicion: document.querySelector("[data-journal-suspicion]"),
  timeoutPolicy: document.querySelector("[data-timeout-policy-note]"),
  turnRecords: document.querySelector("[data-turn-records]"),
  defeatJumpscare: document.querySelector("[data-defeat-jumpscare]"),
  journalBook: document.querySelector(".journal-book"),
  journalSections: [...document.querySelectorAll(".journal-section")],
  sealProgressDots: [...document.querySelectorAll(".seal-progress span")]
};

const state = {
  turn: 1,
  phase: "ready",
  sanity: GAME_RULES.startingSanity,
  soulfire: GAME_RULES.startingSoulfire,
  curse: GAME_RULES.startingCurse,
  shield: 0,
  shieldExpiresOnTurn: 0,
  partialTrueName: 0,
  suspicion: 0,
  trueNamePieces: 0,
  trueNamePieceIds: [],
  acquiredClues: [],
  suspectClues: [],
  falseClues: [],
  revealedFalseClues: [],
  tabooEvents: [],
  turnRecords: [],
  lastInvestigation: "",
  lastInfoTargetKey: "",
  lastDefeatReason: "",
  timeoutCount: 0,
  lastEnemyAction: "",
  selectedAction: "",
  selectedInfoTargetKey: "",
  playerActionHistory: [],
  enemyActionCandidates: null,
  allowedActions: null,
  sealInterferenceLevel: 0,
  activeJournalSection: "0",
  journalPage: 0,
  logAwaitingAdvance: false,
  turnEndAwaitingAdvance: false,
  dialogueArchive: [],
  clockPausedByJournal: false,
  clockWasRunningBeforeHidden: false,
  clockRenderCache: {
    angle: "",
    urgent: false,
    expired: false,
    tooltip: ""
  },
  isSubmitting: false,
  remainingSeconds: GAME_RULES.timerSeconds,
  timerId: 0,
  advanceResolver: null
};

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, Number(value)));
}

function formatTwoDigits(value) {
  return String(value).padStart(2, "0");
}

function setTurnState(text) {
  if (!dom.turnState) return;
  dom.turnState.textContent = text || "";
  dom.turnState.hidden = !text;
}

function getSanityStage() {
  const lost = GAME_RULES.maxSanity - state.sanity;
  return clamp(Math.floor(lost / 3), 0, 4);
}

function setToken(token, current, max) {
  if (!token) return;
  const readout = token.querySelector(".status-copy strong");
  token.dataset.current = String(current);
  token.dataset.max = String(max);
  token.setAttribute("aria-label", `${current}/${max}`);
  if (readout) readout.textContent = `${current}/${max}`;
}

function renderLanternHud() {
  dom.lanternSlots.forEach((slot, index) => {
    const isLit = index < state.soulfire;
    slot.classList.toggle("is-lit", isLit);
    slot.classList.toggle("is-spent", !isLit);
  });
}

function renderSanityGauge() {
  const ratio = clamp(state.sanity / GAME_RULES.maxSanity, 0, 1);
  if (dom.sanityFill) {
    dom.sanityFill.style.width = `${ratio * 100}%`;
  }
  if (dom.sanityToken) {
    dom.sanityToken.style.setProperty("--sanity-ratio", ratio.toFixed(3));
  }
}

function renderHud() {
  state.trueNamePieces = state.trueNamePieceIds.length;
  setToken(dom.soulfireToken, state.soulfire, GAME_RULES.maxSoulfire);
  setToken(dom.sanityToken, state.sanity, GAME_RULES.maxSanity);
  setToken(dom.curseToken, state.curse, 5);
  renderLanternHud();
  renderSanityGauge();

  if (dom.frame) {
    dom.frame.dataset.sanityStage = String(getSanityStage());
    dom.frame.dataset.sealReady = String(state.trueNamePieces >= GAME_RULES.sealRequiredTrueNamePieces);
  }

  if (dom.turnCount) {
    dom.turnCount.textContent = `${formatTwoDigits(state.turn)}/${GAME_RULES.maxTurn}`;
  }
}

function renderSealState() {
  const isReady = state.trueNamePieces >= GAME_RULES.sealRequiredTrueNamePieces;

  if (dom.sealInvocation) {
    dom.sealInvocation.classList.toggle("is-locked", !isReady);
    dom.sealInvocation.setAttribute("aria-disabled", String(!isReady));
  }

  if (dom.sealReason) {
    dom.sealReason.textContent = isReady ? "사용 가능" : `진명 ${state.trueNamePieces}/3`;
  }

  dom.sealProgressDots.forEach((dot, index) => {
    dot.classList.toggle("is-filled", index < state.trueNamePieces);
  });
}

function renderJournal() {
  if (dom.journalCount) dom.journalCount.textContent = `${state.trueNamePieces}/3`;
  if (dom.truthProgress) dom.truthProgress.textContent = `${state.trueNamePieces}/3`;
  if (dom.shield) dom.shield.textContent = `${state.shield}/1`;
  if (dom.partial) dom.partial.textContent = `${state.partialTrueName}/2`;
  if (dom.suspicion) dom.suspicion.textContent = String(state.suspicion);
  if (dom.lastInvestigation) dom.lastInvestigation.textContent = state.lastInvestigation || "없음";

  if (dom.truthList) {
    dom.truthList.innerHTML = TRUTH_PIECES.map((piece) => {
      const found = state.trueNamePieceIds.includes(piece.id);
      return `
        <li class="${found ? "is-found" : ""}">
          <span>${piece.title}</span>
          <small>출처: ${getInfoTargetLabel(piece.source)} · ${found ? `공개: ${piece.reveal}` : "공개 대기"}</small>
          <em>${found ? "획득" : "미확보"}</em>
        </li>
      `;
    }).join("");
  }

  if (dom.acquiredClues) {
    dom.acquiredClues.innerHTML = state.acquiredClues.length
      ? state.acquiredClues.map((clue) => `<li>${clue}</li>`).join("")
      : "<li>아직 확정된 단서가 없다.</li>";
  }

  if (dom.suspectClues) {
    dom.suspectClues.innerHTML = state.suspectClues.length
      ? state.suspectClues.map((clue) => `<li>${clue.text}</li>`).join("")
      : "<li>아직 의심 단서가 없다.</li>";
  }

  if (dom.falseClues) {
    dom.falseClues.innerHTML = state.revealedFalseClues.length
      ? state.revealedFalseClues.map((clue) => `<li>${clue.text}</li>`).join("")
      : "<li>아직 없다.</li>";
  }

  if (dom.timeoutPolicy) {
    const capped = Math.min(state.timeoutCount, 3);
    dom.timeoutPolicy.textContent = `누적 침묵 ${capped}/3. ${state.timeoutCount >= 3 ? "침묵이 습관이 되자 안쪽의 것도 그 틈을 파고들기 시작했다." : "아직은 이안의 망설임으로 기록된다."}`;
  }

  if (dom.turnRecords) {
    dom.turnRecords.innerHTML = state.turnRecords.length
      ? state.turnRecords.slice(-8).map((record) => {
        const target = record.infoTargetKey ? ` <span>${getInfoTargetLabel(record.infoTargetKey)}</span>` : "";
        const taboo = record.tabooViolation ? " <em>금기 흔들림</em>" : "";
        const events = record.events?.length ? `<small>${record.events.join(" / ")}</small>` : "";
        return `<li><strong>${record.turn}턴</strong>${target}${taboo}${events}</li>`;
      }).join("")
      : "<li>아직 기록된 턴이 없다.</li>";
  }
}

function replaceListItems(listElement, items, emptyText = "") {
  if (!listElement || !Array.isArray(items)) return;
  listElement.innerHTML = items.length
    ? items.map((item) => `<li>${typeof item === "string" ? item : item.text || ""}</li>`).join("")
    : `<li>${emptyText}</li>`;
}

function applyJournalRecord(record = {}) {
  /*
    External turn results can replace the prototype diary text through this API.
    Expected fields are optional and section-scoped:
    {
      trueNamePieceIds, acquiredClues, suspectClues, revealedFalseClues,
      turnRecords, shield, partialTrueName, suspicion, lastInvestigation
    }
  */
  if (Array.isArray(record.trueNamePieceIds)) {
    state.trueNamePieceIds = record.trueNamePieceIds.slice(0, GAME_RULES.sealRequiredTrueNamePieces);
    state.trueNamePieces = state.trueNamePieceIds.length;
  }
  if (Array.isArray(record.acquiredClues)) state.acquiredClues = [...record.acquiredClues];
  if (Array.isArray(record.suspectClues)) state.suspectClues = [...record.suspectClues];
  if (Array.isArray(record.revealedFalseClues)) state.revealedFalseClues = [...record.revealedFalseClues];
  if (Array.isArray(record.turnRecords)) state.turnRecords = [...record.turnRecords];
  if (Number.isFinite(record.shield)) state.shield = clamp(record.shield, 0, 1);
  if (Number.isFinite(record.partialTrueName)) state.partialTrueName = clamp(record.partialTrueName, 0, 2);
  if (Number.isFinite(record.suspicion)) state.suspicion = clamp(record.suspicion, 0, 99);
  if (typeof record.lastInvestigation === "string") state.lastInvestigation = record.lastInvestigation;

  renderAll();
}

function renderToolAvailability() {
  dom.ritualTools.forEach((tool) => {
    const action = tool.dataset.action;
    const isLocked = Boolean(state.allowedActions && !state.allowedActions.includes(action));
    tool.classList.toggle("is-locked", isLocked);
    tool.setAttribute("aria-disabled", String(isLocked));
  });
}

function renderAll() {
  renderHud();
  renderSealState();
  renderJournal();
  renderJournalNavigation();
  renderToolAvailability();
}

function getJournalSectionTitle(section, index) {
  return section.querySelector("h2")?.textContent?.trim() || `기록 ${index + 1}`;
}

function getActiveJournalSection() {
  return dom.journalSections.find((section) => section.dataset.journalSection === state.activeJournalSection)
    || dom.journalSections[0];
}

function getJournalPageCount(section) {
  if (!section) return 1;
  const blockCount = [...section.children].filter((child) => child.tagName !== "H2").length;
  const listPageCount = [...section.querySelectorAll("ul, ol")].reduce((max, list) => {
    return Math.max(max, Math.ceil(list.children.length / 6));
  }, 1);
  return Math.max(1, Math.ceil(blockCount / 2), listPageCount);
}

function updateJournalPageContent(section) {
  const page = state.journalPage;
  const pageCount = getJournalPageCount(section);
  const clampedPage = clamp(page, 0, pageCount - 1);
  state.journalPage = clampedPage;

  [...section.children].forEach((child) => {
    if (child.tagName === "H2") return;
    const itemIndex = [...section.children].filter((item) => item.tagName !== "H2").indexOf(child);
    child.hidden = Math.floor(itemIndex / 2) !== clampedPage;
  });

  section.querySelectorAll("ul, ol").forEach((list) => {
    [...list.children].forEach((item, index) => {
      item.hidden = Math.floor(index / 6) !== clampedPage;
    });
    list.hidden = false;
  });

  const pageLabel = dom.journalBook?.querySelector("[data-journal-page-label]");
  const prevButton = dom.journalBook?.querySelector("[data-journal-prev-page]");
  const nextButton = dom.journalBook?.querySelector("[data-journal-next-page]");
  if (pageLabel) pageLabel.textContent = `${clampedPage + 1}/${pageCount}`;
  if (prevButton) prevButton.disabled = clampedPage <= 0;
  if (nextButton) nextButton.disabled = clampedPage >= pageCount - 1;
}

function renderJournalNavigation() {
  if (!dom.journalBook || !dom.journalSections.length) return;

  let nav = dom.journalBook.querySelector("[data-journal-section-nav]");
  if (!nav) {
    nav = document.createElement("nav");
    nav.className = "journal-section-nav";
    nav.dataset.journalSectionNav = "";
    nav.setAttribute("aria-label", "기록서 섹션");

    const controls = document.createElement("div");
    controls.className = "journal-page-controls";
    controls.innerHTML = `
      <button type="button" data-journal-prev-page aria-label="이전 장">‹</button>
      <span data-journal-page-label>1/1</span>
      <button type="button" data-journal-next-page aria-label="다음 장">›</button>
    `;

    dom.journalBook.append(nav, controls);

    controls.querySelector("[data-journal-prev-page]")?.addEventListener("click", () => {
      state.journalPage -= 1;
      renderJournalNavigation();
    });
    controls.querySelector("[data-journal-next-page]")?.addEventListener("click", () => {
      state.journalPage += 1;
      renderJournalNavigation();
    });
  }

  dom.journalBook.classList.add("has-section-nav");
  dom.journalSections.forEach((section, index) => {
    section.dataset.journalSection = String(index);
  });

  if (!dom.journalSections.some((section) => section.dataset.journalSection === state.activeJournalSection)) {
    state.activeJournalSection = "0";
  }

  nav.innerHTML = dom.journalSections.map((section, index) => {
    const id = String(index);
    const title = getJournalSectionTitle(section, index);
    return `<button type="button" class="${id === state.activeJournalSection ? "is-active" : ""}" data-journal-section-button="${id}">${title}</button>`;
  }).join("");

  nav.querySelectorAll("[data-journal-section-button]").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeJournalSection = button.dataset.journalSectionButton || "0";
      state.journalPage = 0;
      renderJournalNavigation();
    });
  });

  [...dom.journalBook.querySelectorAll(".journal-page")].forEach((page) => {
    page.classList.remove("is-active");
  });

  dom.journalSections.forEach((section) => {
    const isActive = section.dataset.journalSection === state.activeJournalSection;
    section.classList.toggle("is-active", isActive);
    section.hidden = !isActive;
    if (isActive) section.closest(".journal-page")?.classList.add("is-active");
  });

  updateJournalPageContent(getActiveJournalSection());
}

function getActionValidation(actionKey) {
  const card = ACTION_CARDS[actionKey];
  if (!card) return { canUse: false, reason: "선택할 수 없는 행동이다." };
  if (state.allowedActions && !state.allowedActions.includes(actionKey)) {
    return { canUse: false, reason: "이전 턴 효과로 이번 행동 후보에서 제외되었다." };
  }
  if (actionKey === "seal" && state.trueNamePieces < GAME_RULES.sealRequiredTrueNamePieces) {
    return { canUse: false, reason: `진명 조각 3/3 필요. 현재 ${state.trueNamePieces}/3.` };
  }
  if (card.cost > state.soulfire) {
    return { canUse: false, reason: `의식력이 부족하다. 필요 ${card.cost}, 현재 ${state.soulfire}.` };
  }
  return { canUse: true, reason: "" };
}

function hideActionCard() {
  if (dom.actionCard) dom.actionCard.hidden = true;
  dom.ritualTools.forEach((tool) => tool.classList.remove("is-selected"));
  if (dom.sealInvocation) dom.sealInvocation.classList.remove("is-selected");
  state.selectedAction = "";
}

function playRitualEffect(actionKey, source = "player") {
  if (!dom.ritualEffect || !actionKey) return;
  dom.ritualEffect.className = `ritual-effect is-active effect-${actionKey} effect-${source}`;
  window.clearTimeout(dom.ritualEffect._effectTimer);
  dom.ritualEffect._effectTimer = window.setTimeout(() => {
    dom.ritualEffect.className = "ritual-effect";
  }, 900);
}

function getCorruptedActionDesc(desc) {
  const stage = getSanityStage();
  if (stage >= 4) return `${desc}\n[연출] 선택지는 처음부터 하나였다.`;
  if (stage >= 3) return `${desc}\n[연출] 네가 고른 게 아니어도 괜찮아.`;
  if (stage >= 2) return `${desc}\n[연출] 보지 말고 선택해.`;
  return desc;
}

function openActionCard(actionKey, sourceElement) {
  if (!dom.actionCard || state.isSubmitting || isLogVisible()) return;

  const card = ACTION_CARDS[actionKey];
  if (!card) return;

  const validation = getActionValidation(actionKey);
  const cardTitle = dom.actionCard.querySelector("[data-card-title]");
  const cardKicker = dom.actionCard.querySelector("[data-card-kicker]");
  const cardDesc = dom.actionCard.querySelector("[data-card-desc]");
  const cardCost = dom.actionCard.querySelector("[data-card-cost]");
  const cardType = dom.actionCard.querySelector("[data-card-type]");
  const cardArt = dom.actionCard.querySelector("[data-card-art]");
  const cardWarning = dom.actionCard.querySelector("[data-card-warning]");
  const infoTargetWrap = dom.actionCard.querySelector("[data-card-info-target-wrap]");
  const infoTargetSelect = dom.actionCard.querySelector("[data-card-info-target]");
  const useButton = dom.actionCard.querySelector("[data-card-use]");
  const needsInfoTarget = actionKey === "insight" || actionKey === "contract";

  dom.ritualTools.forEach((tool) => tool.classList.remove("is-selected"));
  if (dom.sealInvocation) dom.sealInvocation.classList.remove("is-selected");
  sourceElement?.classList.add("is-selected");

  if (cardTitle) cardTitle.textContent = card.title;
  if (cardKicker) cardKicker.textContent = card.kicker;
  if (cardDesc) cardDesc.textContent = getCorruptedActionDesc(card.desc);
  if (cardCost) cardCost.textContent = String(card.cost);
  if (cardType) cardType.textContent = card.type;
  if (cardArt) {
    cardArt.dataset.symbol = card.symbol;
    cardArt.style.setProperty("--card-image", `url("${card.image}")`);
    cardArt.classList.toggle("has-image", Boolean(card.image));
  }
  if (cardWarning) {
    cardWarning.textContent = validation.reason;
    cardWarning.hidden = validation.canUse;
  }
  if (infoTargetWrap && infoTargetSelect) {
    infoTargetWrap.hidden = !needsInfoTarget;
    if (needsInfoTarget) {
      infoTargetSelect.innerHTML = INFO_TARGETS
        .map((target) => `<option value="${target.key}">${target.label}</option>`)
        .join("");
      state.selectedInfoTargetKey = state.selectedInfoTargetKey || getInfoTargetKey(actionKey);
      infoTargetSelect.value = state.selectedInfoTargetKey;
      infoTargetSelect.onchange = () => {
        state.selectedInfoTargetKey = infoTargetSelect.value;
      };
    } else {
      state.selectedInfoTargetKey = "";
      infoTargetSelect.onchange = null;
    }
  }
  if (useButton) useButton.disabled = !validation.canUse;

  state.selectedAction = actionKey;
  dom.actionCard.dataset.selectedAction = actionKey;
  dom.actionCard.hidden = false;
}

function isLogVisible() {
  return Boolean(state.logAwaitingAdvance || state.turnEndAwaitingAdvance);
}

function trimLogText(text) {
  return String(text || "")
    .split("\n")
    .map((line) => line.replace(/^\[[^\]]+\]\s*/, "").trim())
    .filter(Boolean)
    .slice(0, 2)
    .join("\n");
}

function pushDialogueLog(side, speaker, text, mode = "clean") {
  const stack = side === "spirit"
    ? dom.spiritLogStack
    : side === "system"
      ? dom.systemLogStack
      : dom.protagonistLogStack;
  if (!stack) return;

  const cleanText = trimLogText(text);
  stack.replaceChildren();

  const entry = document.createElement("article");
  entry.className = "dialogue-log-entry";
  entry.dataset.logMode = mode;

  const name = document.createElement("strong");
  name.textContent = speaker;

  const body = document.createElement("p");
  body.textContent = cleanText;

  entry.append(name, body);
  stack.append(entry);
  appendDialogueArchive(side, speaker, cleanText);
}

function clearDialogueLogs() {
  dom.protagonistLogStack?.replaceChildren();
  dom.systemLogStack?.replaceChildren();
  dom.spiritLogStack?.replaceChildren();
}

function appendDialogueArchive(side, speaker, text) {
  if (!text) return;
  state.dialogueArchive.push({ turn: state.turn, side, speaker, text });
  if (state.dialogueArchive.length > 60) state.dialogueArchive.shift();
  renderDialogueArchive();
}

function renderDialogueArchive() {
  if (!dom.dialogueArchiveList) return;
  dom.dialogueArchiveList.innerHTML = state.dialogueArchive.length
    ? state.dialogueArchive.map((record) => `
      <li data-side="${record.side}">
        <strong>${record.turn}T · ${record.speaker}</strong>
        <span>${record.text}</span>
      </li>
    `).join("")
    : "<li>아직 남은 로그가 없다.</li>";
}

function setDialogueArchiveOpen(isOpen) {
  if (!dom.dialogueArchivePanel || !dom.dialogueArchiveToggle) return;
  dom.dialogueArchivePanel.hidden = !isOpen;
  dom.dialogueArchiveToggle.setAttribute("aria-expanded", String(isOpen));
}

function showTurnEndCue() {
  if (!dom.turnEndCue) return;
  state.turnEndAwaitingAdvance = true;
  dom.turnEndCue.hidden = false;
  dom.turnEndCue.classList.remove("is-active");
  void dom.turnEndCue.offsetWidth;
  dom.turnEndCue.classList.add("is-active");
}

function hideTurnEndCue() {
  state.turnEndAwaitingAdvance = false;
  if (dom.turnEndCue) {
    dom.turnEndCue.hidden = true;
    dom.turnEndCue.classList.remove("is-active");
  }
}

function showPlayerLog(text, { allowCorruption = true, channel = "protagonist" } = {}) {
  const stage = getSanityStage();
  const corrupted = channel === "protagonist" && allowCorruption && stage >= 3;
  let rendered = text;

  if (corrupted && stage >= 4) {
    rendered += "\n[연출] ...아니, 이건 내가 한 말이 아니다.";
  } else if (corrupted) {
    rendered += "\n[연출] 거울 안쪽에서 같은 문장이 먼저 흔들린다.";
  }

  state.logAwaitingAdvance = true;
  pushDialogueLog(channel, channel === "system" ? "기록" : "나", rendered, corrupted ? "corrupted" : channel);

  if (dom.playerLog && dom.playerLogText) {
    dom.playerLog.dataset.logMode = corrupted ? "corrupted" : "clean";
    dom.playerLogText.textContent = rendered;
    dom.playerLog.hidden = true;
  }
}

function hidePlayerLog() {
  state.logAwaitingAdvance = false;
  if (dom.playerLog) dom.playerLog.hidden = true;
}

function waitForAdvance() {
  return new Promise((resolve) => {
    state.advanceResolver = resolve;
  });
}

function advanceLogSequence() {
  if (state.advanceResolver) {
    const resolve = state.advanceResolver;
    state.advanceResolver = null;
    resolve();
    return true;
  }
  if (isLogVisible()) {
    hidePlayerLog();
    hideEnemyVoice();
    hideTurnEndCue();
    return true;
  }
  return false;
}

function showEnemyVoice(enemy) {
  if (!dom.enemyVoice || !dom.enemyAction || !dom.enemyText) return;
  dom.enemyAction.textContent = enemy.action;
  dom.enemyText.textContent = enemy.line;
  state.logAwaitingAdvance = true;
  pushDialogueLog("spirit", "???", enemy.line, "spirit");
  dom.enemyVoice.hidden = true;
}

function hideEnemyVoice() {
  state.logAwaitingAdvance = false;
  if (dom.enemyVoice) dom.enemyVoice.hidden = true;
}

function showSealInterference(level) {
  if (!dom.sealInterference || !dom.sealInterferenceValue) return;
  dom.sealInterferenceValue.textContent = `${level}/2`;
  dom.sealInterference.hidden = false;
}

function hideSealInterference() {
  if (dom.sealInterference) dom.sealInterference.hidden = true;
}

function triggerDefeatJumpscare() {
  if (!dom.defeatJumpscare) return;
  dom.defeatJumpscare.hidden = false;
  dom.defeatJumpscare.classList.remove("is-active");
  window.setTimeout(() => {
    dom.defeatJumpscare.classList.add("is-active");
  }, 20);
}

function scheduleDefeatJumpscare(delayMs = 1200) {
  window.setTimeout(triggerDefeatJumpscare, delayMs);
}

function openEndingScreen(outcome, reason) {
  const target = new URL(ENDING_SCREEN.href, window.location.href);
  target.searchParams.set("outcome", outcome);
  target.searchParams.set("reason", reason);
  target.searchParams.set("turn", String(Math.min(state.turn, GAME_RULES.maxTurn)));
  target.searchParams.set("truth", `${state.trueNamePieces}/${GAME_RULES.sealRequiredTrueNamePieces}`);
  target.searchParams.set("sanity", `${state.sanity}/${GAME_RULES.maxSanity}`);
  target.searchParams.set("curse", `${state.curse}/${GAME_RULES.maxCurseTrace}`);
  window.location.href = target.toString();
}

function scheduleEndingScreen(outcome, reason) {
  window.setTimeout(() => openEndingScreen(outcome, reason), ENDING_SCREEN.delayMs);
}

function getEndingScreenState(result) {
  if (result?.seal?.success) return { outcome: "win", reason: "seal" };

  const curseDefeat = result?.stateChanges?.defeatFlags?.contractFailedAtMaxCurse
    || result?.stateChanges?.defeatFlags?.hitByCurseAtMaxCurse;

  if (state.sanity <= 0) return { outcome: "lose", reason: "sanity" };
  if (curseDefeat) return { outcome: "lose", reason: "curse" };
  if (state.turn > GAME_RULES.maxTurn) return { outcome: "lose", reason: "turns" };
  return { outcome: "unfinished", reason: "unknown" };
}

function getPreferredEnemyActions(playerAction, isTimeout) {
  const silence = ENEMY_ACTIONS.find((entry) => entry.key === "silence");
  const deceive = ENEMY_ACTIONS.find((entry) => entry.key === "deceive");
  const insight = ENEMY_ACTIONS.find((entry) => entry.key === "insight");

  if (isTimeout && state.timeoutCount >= 3) {
    if (state.lastEnemyAction === "silence" && deceive) return [deceive, silence].filter(Boolean);
    return [silence, deceive].filter(Boolean);
  }

  if (state.turn >= 4) {
    const recent = state.playerActionHistory.slice(-3);
    const repeated = recent.filter((action) => action === playerAction).length;
    if (repeated >= 2) return [insight, deceive].filter(Boolean);
  }

  return [...ENEMY_ACTIONS];
}

function pickPrototypeEnemyAction(playerAction, isTimeout) {
  const limitedCandidates = Array.isArray(state.enemyActionCandidates)
    ? ENEMY_ACTIONS.filter((entry) => state.enemyActionCandidates.includes(entry.key))
    : [];
  const pool = limitedCandidates.length ? limitedCandidates : getPreferredEnemyActions(playerAction, isTimeout);
  state.enemyActionCandidates = null;
  return pool[Math.floor(Math.random() * pool.length)] || ENEMY_ACTIONS[0];
}

function getNextEnemyCandidates(playerAction, enemyAction, isTimeout) {
  const preferred = getPreferredEnemyActions(playerAction, isTimeout)
    .filter((entry) => entry.key !== "seal");
  const unique = [];
  preferred.forEach((entry) => {
    if (!unique.some((item) => item.key === entry.key)) unique.push(entry);
  });
  ENEMY_ACTIONS.forEach((entry) => {
    if (entry.key !== "seal" && !unique.some((item) => item.key === entry.key)) unique.push(entry);
  });
  return unique.slice(0, 2).map((entry) => entry.key);
}

function getInfoTargetKey(playerAction) {
  if ((playerAction === "insight" || playerAction === "contract") && state.selectedInfoTargetKey) {
    return state.selectedInfoTargetKey;
  }

  if (playerAction === "insight") {
    return state.trueNamePieces >= 2 ? "forgotten_room" : "mirror_back";
  }

  if (playerAction === "contract") {
    return state.trueNamePieces >= 2 ? "forgotten_room" : "missing_child_voice";
  }

  if (playerAction === "deceive") {
    if (state.trueNamePieces >= 2) return "forgotten_room";
    return state.lastInfoTargetKey || "mirror_back";
  }

  return "";
}

function getTruthPieceForTarget(targetKey) {
  return TRUTH_PIECES.find((piece) => piece.source === targetKey);
}

function hasTruthPiece(targetKey) {
  const index = TRUTH_PIECES.findIndex((piece) => piece.source === targetKey);
  return index >= 0 && index < state.trueNamePieces;
}

function pickFalseClue(targetKey) {
  return FALSE_CLUE_RULES.find((rule) => {
    const enoughPieces = !rule.requiresTrueNamePieces || state.trueNamePieces >= rule.requiresTrueNamePieces;
    return enoughPieces && rule.targets.includes(targetKey);
  });
}

function addSuspectClue(rule, source) {
  if (!rule || state.suspectClues.length >= GAME_RULES.maxFalseClues) return null;
  if (state.suspectClues.some((clue) => clue.id === rule.id)) return null;
  if (state.revealedFalseClues.some((clue) => clue.id === rule.id)) return null;

  const clue = { id: rule.id, text: rule.text, source };
  state.suspectClues.push(clue);
  return clue;
}

function revealSuspectFalseClue(targetKey) {
  const index = state.suspectClues.findIndex((clue) => {
    const rule = FALSE_CLUE_RULES.find((item) => item.id === clue.id);
    return !targetKey || rule?.targets.includes(targetKey);
  });

  if (index < 0) return null;

  const [clue] = state.suspectClues.splice(index, 1);
  state.revealedFalseClues.push(clue);
  return clue;
}

function resolveTableStateChanges(playerAction, enemy, isTimeout) {
  const card = ACTION_CARDS[playerAction];
  const infoTargetKey = getInfoTargetKey(playerAction);
  const isInfoAction = playerAction === "insight" || playerAction === "contract";
  const tabooViolation = Boolean(infoTargetKey && state.lastInfoTargetKey === infoTargetKey);
  let sanityDelta = 0;
  let soulfireDelta = -card.cost + 1;
  let curseDelta = 0;
  let shieldAfter = state.shield;
  let partialAfter = state.partialTrueName;
  let trueNamePieceIds = [...state.trueNamePieceIds];
  const clues = [];
  const suspectClues = [];
  const revealedFalseClues = [];
  const turnEvents = [];
  const enemyAction = enemy.key;

  const addFalseClueFromRule = (source, target = infoTargetKey || "mirror_back") => {
    const clue = addSuspectClue(pickFalseClue(target), source);
    if (clue) suspectClues.push(clue);
    return clue;
  };

  const addPartialPiece = () => {
    partialAfter = clamp(partialAfter + 1, 0, 2);
    if (partialAfter >= 2 && trueNamePieceIds.length < GAME_RULES.sealRequiredTrueNamePieces) {
      const nextPiece = TRUTH_PIECES.find((piece) => !trueNamePieceIds.includes(piece.id));
      if (nextPiece) {
        trueNamePieceIds.push(nextPiece.id);
        clues.push(nextPiece.reveal);
      }
      partialAfter = 0;
    }
  };

  const revealTruthPiece = () => {
    const piece = getTruthPieceForTarget(infoTargetKey)
      || TRUTH_PIECES.find((item) => !trueNamePieceIds.includes(item.id));
    if (piece && !trueNamePieceIds.includes(piece.id)) {
      trueNamePieceIds.push(piece.id);
      clues.push(piece.reveal);
    }
  };

  const resolveInsightDeceiveCheck = () => {
    const successRate = Math.min(80, 50 + state.suspicion * 10);
    const roll = ((state.turn * 37 + state.suspicion * 11) % 100) + 1;
    state.suspicion = 0;
    if (roll <= successRate) {
      const revealed = revealSuspectFalseClue(infoTargetKey);
      if (revealed) revealedFalseClues.push(revealed);
      turnEvents.push("간파가 속임수의 결을 붙잡았다. 거짓 기척 하나가 힘을 잃었다.");
    } else if (addFalseClueFromRule("insight_failed")) {
      turnEvents.push("간파가 빗나갔다. 거짓 단서 하나가 기록서에 섞였다.");
    }
  };

  let tableSoulfireDelta = -card.cost;
  let sealInterference = 0;
  let shieldGranted = false;
  let shieldConsumed = false;

  if (tabooViolation && (playerAction === "insight" || playerAction === "contract")) {
    if (addFalseClueFromRule("taboo")) {
      turnEvents.push("같은 대상을 연속으로 조사해 금기를 흔들었다. 의심 단서 하나가 남았다.");
    }
  }

  if (isTimeout && state.timeoutCount === 2) {
    curseDelta += 1;
    turnEvents.push("\uBC18\uBCF5\uB41C \uCE68\uBB35\uC774 \uC800\uC8FC \uD754\uC801\uC744 \uD558\uB098 \uB354 \uAE4A\uAC8C \uB0A8\uACBC\uB2E4.");
  }

  switch (playerAction) {
    case "curse":
      if (enemyAction === "curse") {
        const playerRoll = ((state.turn * 3) % 6) + 1;
        const enemyRoll = ((state.turn * 5 + 1) % 6) + 1;
        sanityDelta -= 1;
        if (enemyRoll > playerRoll) sanityDelta -= 1;
        turnEvents.push(`두 저주가 정면으로 부딪혔다. 주사위 ${playerRoll}:${enemyRoll}.`);
      } else if (enemyAction === "deceive") {
        state.suspicion = clamp(state.suspicion + 1, 0, 3);
      }
      break;

    case "guard":
      if (enemyAction === "curse") {
        shieldAfter = 1;
        shieldGranted = true;
      }
      if (enemyAction === "deceive" && addFalseClueFromRule("deceive_vs_guard")) {
        turnEvents.push("수호가 잘못된 위협을 향했다. 의심 단서 하나가 남았다.");
      }
      break;

    case "insight":
      if (enemyAction === "curse") {
        sanityDelta -= 2;
        state.suspicion = clamp(state.suspicion + 1, 0, 3);
      } else if (enemyAction === "insight") {
        state.suspicion = clamp(state.suspicion + 1, 0, 3);
      } else if (enemyAction === "deceive") {
        resolveInsightDeceiveCheck();
      } else if (enemyAction === "contract") {
        addPartialPiece();
        turnEvents.push("\uACC4\uC57D\uC758 \uBE48\uD2C8\uC744 \uC77D\uC5B4 \uBD88\uC644\uC804\uD55C \uC9C4\uBA85 \uC870\uAC01\uC774 \uB0A8\uC558\uB2E4.");
      } else if (enemyAction === "silence") {
        turnEvents.push("침묵은 답을 내놓지 않았다. 대신 다음 의식의 방향이 조금 좁혀졌다.");
      }
      break;

    case "deceive":
      if (enemyAction === "curse") sanityDelta -= 1;
      if (enemyAction === "insight") {
        turnEvents.push("\uAC04\uD30C\uAC00 \uC18D\uC784\uC218\uC758 \uACB0\uC744 \uB354\uB4EC\uC5C8\uB2E4. \uACB0\uACFC\uB294 \uC0C1\uB300\uC758 \uAE30\uB85D\uC5D0\uB9CC \uB0A8\uB294\uB2E4.");
      }
      if (enemyAction === "deceive") state.suspicion = clamp(state.suspicion + 1, 0, 3);
      break;

    case "silence":
      if (enemyAction === "curse") sanityDelta -= 2;
      if (["guard", "deceive", "silence"].includes(enemyAction)) tableSoulfireDelta += 1;
      if (enemyAction === "insight") {
        turnEvents.push("침묵은 단서를 내놓지 않았다. 다음 의식의 방향만 흐릿하게 좁혀졌다.");
      }
      break;

    case "contract":
      if (enemyAction === "curse") sanityDelta -= 2;
      if (enemyAction === "guard") {
        curseDelta += 1;
        addPartialPiece();
      }
      if (enemyAction === "insight") curseDelta += 2;
      if (enemyAction === "deceive") {
        curseDelta += 1;
        if (addFalseClueFromRule("deceive_vs_contract")) {
          turnEvents.push("거짓 조건이 계약을 더럽혔다. 의심 단서 하나가 남았다.");
        }
      }
      if (enemyAction === "silence") revealTruthPiece();
      if (enemyAction === "contract") {
        curseDelta += 1;
        addPartialPiece();
      }
      break;

    case "seal":
      if (enemyAction === "curse") {
        sanityDelta -= 2;
        sealInterference = 1;
      } else if (enemyAction === "guard") {
        sealInterference = 0;
      } else if (enemyAction === "insight" || enemyAction === "silence") {
        sealInterference = 1;
      } else if (enemyAction === "deceive") {
        sealInterference = 2;
        addFalseClueFromRule("deceive_vs_seal");
      } else if (enemyAction === "contract") {
        sealInterference = 2;
      }
      break;
  }

  const nextEnemyCandidates = ((playerAction === "insight" && enemyAction === "silence")
    || (playerAction === "silence" && enemyAction === "insight"))
    ? getNextEnemyCandidates(playerAction, enemyAction, isTimeout)
    : null;

  if (enemyAction === "curse" && state.shield > 0 && sanityDelta < 0) {
    const blocked = Math.min(2, Math.abs(sanityDelta));
    sanityDelta += blocked;
    shieldAfter = shieldGranted ? 1 : 0;
    shieldConsumed = true;
    turnEvents.push("보호막이 저주 피해를 막고 흩어졌다.");
  }

  if (nextEnemyCandidates) {
    turnEvents.push(`다음 징후가 좁혀졌다: ${nextEnemyCandidates.map((key) => ACTION_CARDS[key]?.title || key).join(" / ")}`);
  }

  const tableCurseAfter = clamp(state.curse + curseDelta, 0, GAME_RULES.maxCurseTrace);
  const tableContractFailedAtMaxCurse = playerAction === "contract" && !clues.length && tableCurseAfter >= GAME_RULES.maxCurseTrace;
  const tableHitByCurseAtMaxCurse = enemyAction === "curse" && tableCurseAfter >= GAME_RULES.maxCurseTrace;

  return {
    sanity: {
      before: state.sanity,
      after: clamp(state.sanity + sanityDelta, 0, GAME_RULES.maxSanity),
      delta: sanityDelta
    },
    soulfire: {
      before: state.soulfire,
      after: clamp(state.soulfire + tableSoulfireDelta, 0, GAME_RULES.maxSoulfire),
      delta: tableSoulfireDelta
    },
    curse: {
      before: state.curse,
      after: tableCurseAfter,
      delta: tableCurseAfter - state.curse
    },
    shield: shieldAfter,
    partialTrueName: partialAfter,
    suspicion: state.suspicion,
    trueNamePieceIds,
    trueNamePieces: trueNamePieceIds.length,
    clues,
    suspectClues,
    revealedFalseClues,
    lastInvestigation: infoTargetKey || state.lastInvestigation,
    lastInfoTargetKey: infoTargetKey || state.lastInfoTargetKey,
    tabooViolation,
    turnEvents,
    nextEnemyCandidates,
    shieldGranted,
    shieldConsumed,
    sealInterference,
    defeatFlags: {
      contractFailedAtMaxCurse: tableContractFailedAtMaxCurse,
      hitByCurseAtMaxCurse: tableHitByCurseAtMaxCurse
    }
  };

}


function getPatternHint(playerAction) {
  const recent = state.playerActionHistory.slice(-3);
  const repeated = recent.filter((action) => action === playerAction).length;
  if (state.turn < 4 || repeated < 2) return "";
  return "거울 안쪽의 것은 이안의 반복된 의식에 반응하기 시작했다. 같은 선택의 틈을 기억한다.";
}

function createPrototypeTurnResult(playerAction, { timeout = false } = {}) {
  const enemy = pickPrototypeEnemyAction(playerAction, timeout);
  const card = ACTION_CARDS[playerAction];
  const changes = resolveTableStateChanges(playerAction, enemy, timeout);
  let seal = null;

  if (playerAction === "seal") {
    const interference = Number.isFinite(changes.sealInterference)
      ? changes.sealInterference
      : state.sealInterferenceLevel;
    seal = { interference, success: interference <= 1 };
  }

  return {
    playerAction,
    playerLabel: card.title,
    enemy,
    briefing: seal
      ? (seal.success ? "세 조각의 기록이 맞물리고, 이안은 마침내 감춰진 이름을 부른다." : "거울 안쪽의 저항이 진명 선언을 찢어 놓았다.")
      : card.briefing,
    delta: seal ? (seal.success ? "진명 선언 성공" : "진명 선언 실패") : card.desc,
    stateChanges: changes,
    patternHint: getPatternHint(playerAction),
    seal
  };
}

function requestTurnResult(playerAction, options = {}) {
  // Swap this prototype provider with the Django turn-result API when backend endpoints are ready.
  return new Promise((resolve) => {
    window.setTimeout(() => {
      resolve(createPrototypeTurnResult(playerAction, options));
    }, 650);
  });
}

function resolveTurnResult(playerAction, options = {}) {
  return requestTurnResult(playerAction, options);
}

function applyTurnStateChanges(changes = {}) {
  const applied = {};

  if (changes.sanity) {
    state.sanity = changes.sanity.after;
    applied.sanity = { ...changes.sanity, max: GAME_RULES.maxSanity };
  }
  if (changes.soulfire) state.soulfire = changes.soulfire.after;
  if (changes.curse) state.curse = changes.curse.after;
  if (Number.isFinite(changes.shield)) state.shield = changes.shield;
  if (changes.shieldGranted) state.shieldExpiresOnTurn = state.turn + 1;
  if (changes.shieldConsumed || state.shield === 0) state.shieldExpiresOnTurn = 0;
  if (!changes.shieldGranted && state.shield > 0 && state.shieldExpiresOnTurn <= state.turn) {
    state.shield = 0;
    state.shieldExpiresOnTurn = 0;
  }
  state.enemyActionCandidates = Array.isArray(changes.nextEnemyCandidates)
    ? [...changes.nextEnemyCandidates]
    : null;
  if (Number.isFinite(changes.partialTrueName)) state.partialTrueName = changes.partialTrueName;
  if (Number.isFinite(changes.suspicion)) state.suspicion = changes.suspicion;
  if (Number.isFinite(changes.trueNamePieces)) state.trueNamePieces = changes.trueNamePieces;
  if (Array.isArray(changes.trueNamePieceIds)) {
    state.trueNamePieceIds = changes.trueNamePieceIds;
    state.trueNamePieces = changes.trueNamePieceIds.length;
  }
  if (changes.lastInvestigation !== undefined) state.lastInvestigation = changes.lastInvestigation;
  if (changes.lastInfoTargetKey !== undefined) state.lastInfoTargetKey = changes.lastInfoTargetKey;

  state.acquiredClues.push(...(changes.clues || []));
  (changes.suspectClues || []).forEach((clue) => {
    if (!state.suspectClues.some((item) => item.id === clue.id)) state.suspectClues.push(clue);
  });
  (changes.revealedFalseClues || []).forEach((clue) => {
    if (!state.revealedFalseClues.some((item) => item.id === clue.id)) state.revealedFalseClues.push(clue);
  });
  if (changes.tabooViolation) {
    state.tabooEvents.push({ turn: state.turn, target: changes.lastInfoTargetKey });
  }
  state.turnRecords.push({
    turn: state.turn,
    infoTargetKey: changes.lastInfoTargetKey || "",
    tabooViolation: Boolean(changes.tabooViolation),
    events: changes.turnEvents || []
  });

  renderAll();
  return applied;
}

function formatStateLine(applied) {
  const sanity = applied.sanity;
  if (!sanity) return "[상태] 이성 변화 없음";
  const sign = sanity.delta > 0 ? "+" : "";
  return `[상태] 이성 ${sanity.before}/${sanity.max} -> ${sanity.after}/${sanity.max} (${sign}${sanity.delta})`;
}

function formatTurnBriefing(result, applied) {
  const lines = [
    `[공개] 나: ${result.playerLabel} / 괴이: ${result.enemy.label}`,
    `[판정] ${result.briefing}`,
    formatStateLine(applied),
    `[변화] ${result.delta}`
  ];

  if (result.seal) {
    lines.push(`[진명] 방해 단계 ${result.seal.interference}/2 · ${result.seal.success ? "성공" : "실패"}`);
  }
  (result.stateChanges?.turnEvents || []).forEach((event) => {
    lines.push(`[기록] ${event}`);
  });
  if (result.patternHint) {
    lines.push(`[연출] ${result.patternHint}`);
  }

  return lines.join("\n");
}

function formatResourceChanges(changes = {}) {
  const lines = [];
  if (changes.sanity?.delta) {
    lines.push(`이성 ${changes.sanity.before}->${changes.sanity.after}`);
  }
  if (changes.soulfire?.delta) {
    lines.push(`혼불 ${changes.soulfire.before}->${changes.soulfire.after}`);
  }
  if (changes.curse?.delta) {
    lines.push(`저주 ${changes.curse.before}->${changes.curse.after}`);
  }
  if (Number.isFinite(changes.shield)) {
    lines.push(`보호막 ${changes.shield}`);
  }
  if (Number.isFinite(changes.partialTrueName) && changes.partialTrueName > 0) {
    lines.push(`진명 진척 ${changes.partialTrueName}/2`);
  }
  if (Number.isFinite(changes.trueNamePieces) && changes.trueNamePieces > 0) {
    lines.push(`진명 조각 ${changes.trueNamePieces}/3`);
  }
  return lines.length ? lines.join(" / ") : "변화 없음";
}

function formatTurnBriefing(result) {
  const lines = [
    `[행동] 나: ${result.playerLabel} / 괴이: ${result.enemy.label}`,
    `[결과] ${formatResourceChanges(result.stateChanges)}`
  ];

  if (result.seal) {
    lines.push(`[봉인] 방해 ${result.seal.interference}/2 / ${result.seal.success ? "성공" : "실패"}`);
  }

  return lines.join("\n");
}

function endGameIfNeeded(result) {
  if (result?.seal?.success) {
    setTurnState("\uBD09\uC778 \uC131\uACF5");
    showPlayerLog("[\uC2B9\uB9AC]\n" + OFFICIAL_ENDING_TEXT.win, { allowCorruption: false, channel: "system" });
    stopClock();
    return true;
  }

  if (state.sanity <= 0) {
    setTurnState("\uC774\uC131 \uBD95\uAD34");
    showPlayerLog("[\uD328\uBC30]\n" + OFFICIAL_ENDING_TEXT.loseSanity, { allowCorruption: false, channel: "system" });
    scheduleDefeatJumpscare();
    stopClock();
    return true;
  }

  const curseDefeat = result?.stateChanges?.defeatFlags?.contractFailedAtMaxCurse
    || result?.stateChanges?.defeatFlags?.hitByCurseAtMaxCurse;

  if (curseDefeat) {
    setTurnState("\uC800\uC8FC \uC7A0\uC2DD");
    showPlayerLog("[\uD328\uBC30]\n" + OFFICIAL_ENDING_TEXT.loseCurse, { allowCorruption: false, channel: "system" });
    scheduleDefeatJumpscare();
    stopClock();
    return true;
  }

  if (state.turn > GAME_RULES.maxTurn) {
    setTurnState("12\uD134 \uC885\uB8CC");
    showPlayerLog("[\uD328\uBC30]\n" + OFFICIAL_ENDING_TEXT.loseTurns, { allowCorruption: false, channel: "system" });
    stopClock();
    return true;
  }

  return false;
}

async function runTurnSequence(actionKey, options = {}) {
  const card = ACTION_CARDS[actionKey];
  if (!card || state.isSubmitting) return;

  const validation = getActionValidation(actionKey);
  if (!options.ignoreValidation && !validation.canUse) return;

  state.isSubmitting = true;
  state.phase = "waiting";
  if (options.timeout) state.timeoutCount += 1;
  if (actionKey === "seal") showSealInterference(state.sealInterferenceLevel);
  else hideSealInterference();

  setTurnState(options.timeout ? "침묵 처리" : "결과 대기");
  hideActionCard();
  playRitualEffect(actionKey);
  showPlayerLog(options.timeout ? "시간이 다했다. 검은 초가 먼저 침묵을 선언한다." : card.playerLine, { allowCorruption: !options.timeout });

  await waitForAdvance();
  hidePlayerLog();

  const result = await resolveTurnResult(actionKey, options);
  const applied = applyTurnStateChanges(result.stateChanges);
  state.lastEnemyAction = result.enemy.key;
  playRitualEffect(result.enemy.key, "enemy");
  showEnemyVoice(result.enemy);

  await waitForAdvance();
  hideEnemyVoice();
  hideSealInterference();

  showPlayerLog(formatTurnBriefing(result, applied), { allowCorruption: false, channel: "system" });
  await waitForAdvance();
  hidePlayerLog();

  if (endGameIfNeeded(result)) {
    state.phase = "ready";
    state.isSubmitting = false;
    const ending = getEndingScreenState(result);
    scheduleEndingScreen(ending.outcome, ending.reason);
    return;
  }

  clearDialogueLogs();
  showTurnEndCue();
  await waitForAdvance();
  hideTurnEndCue();

  state.playerActionHistory.push(actionKey);
  state.turn += 1;
  state.soulfire = clamp(state.soulfire + 2, 0, GAME_RULES.maxSoulfire);
  state.phase = "ready";
  state.isSubmitting = false;
  renderAll();
  resetClock();
  setTurnState("");
}

function stopClock() {
  window.clearInterval(state.timerId);
  state.timerId = 0;
}

function renderClockLegacy() {
  if (!dom.clock) return;
  const progress = state.remainingSeconds / GAME_RULES.timerSeconds;
  const angle = (1 - progress) * 360;
  dom.clock.style.setProperty("--clock-hand-angle", `${angle}deg`);
  dom.clock.classList.toggle("is-urgent", state.remainingSeconds <= 5 && state.remainingSeconds > 0);
  dom.clock.classList.toggle("is-expired", state.remainingSeconds <= 0);
  dom.clock.dataset.tooltip = `턴 제한 시간 ${GAME_RULES.timerSeconds}초. 시간이 다하면 침묵이 먼저 선택된다. 누적 침묵 ${Math.min(state.timeoutCount, 3)}/3. 거울 안쪽의 것은 반복된 침묵을 기억한다.`;
}

function resetClock() {
  stopClock();
  state.remainingSeconds = GAME_RULES.timerSeconds;
  renderClock();
  startClock();
}

function renderClock() {
  if (!dom.clock) return;
  const progress = state.remainingSeconds / GAME_RULES.timerSeconds;
  const angle = `${Math.round((1 - progress) * 360)}deg`;
  const urgent = state.remainingSeconds <= 5 && state.remainingSeconds > 0;
  const expired = state.remainingSeconds <= 0;
  const tooltip = `\uC81C\uD55C \uC2DC\uAC04 ${GAME_RULES.timerSeconds}\uCD08. \uC2DC\uAC04\uC774 \uB05D\uB098\uBA74 \uCE68\uBB35\uC774 \uBA3C\uC800 \uC120\uD0DD\uB429\uB2C8\uB2E4. \uB204\uC801 \uCE68\uBB35 ${Math.min(state.timeoutCount, 3)}/3.`;

  if (state.clockRenderCache.angle !== angle) {
    dom.clock.style.setProperty("--clock-hand-angle", angle);
    state.clockRenderCache.angle = angle;
  }
  if (state.clockRenderCache.urgent !== urgent) {
    dom.clock.classList.toggle("is-urgent", urgent);
    state.clockRenderCache.urgent = urgent;
  }
  if (state.clockRenderCache.expired !== expired) {
    dom.clock.classList.toggle("is-expired", expired);
    state.clockRenderCache.expired = expired;
  }
  if (state.clockRenderCache.tooltip !== tooltip) {
    dom.clock.dataset.tooltip = tooltip;
    state.clockRenderCache.tooltip = tooltip;
  }
}

function startClock() {
  if (state.timerId || state.remainingSeconds <= 0 || document.hidden) return;
  state.timerId = window.setInterval(() => {
    if (state.isSubmitting || state.phase !== "ready") return;
    state.remainingSeconds -= 1;
    renderClock();
    if (state.remainingSeconds <= 0) {
      stopClock();
      runTurnSequence("silence", { timeout: true, ignoreValidation: true });
    }
  }, 1000);
}

function handleVisibilityChange() {
  if (document.hidden) {
    state.clockWasRunningBeforeHidden = Boolean(state.timerId);
    stopClock();
    return;
  }

  if (state.clockWasRunningBeforeHidden && state.phase === "ready" && !state.isSubmitting && !state.clockPausedByJournal) {
    startClock();
  }
  state.clockWasRunningBeforeHidden = false;
}

function setJournalOpen(isOpen) {
  if (!dom.journalPanel || !dom.journalToggle || !dom.journal) return;

  if (isOpen && state.timerId && state.phase === "ready") {
    stopClock();
    state.clockPausedByJournal = true;
  }

  dom.journalPanel.hidden = !isOpen;
  dom.journalToggle.setAttribute("aria-expanded", String(isOpen));
  dom.journal.classList.toggle("is-open", isOpen);
  if (isOpen) renderJournalNavigation();

  if (!isOpen && state.clockPausedByJournal) {
    state.clockPausedByJournal = false;
    if (state.phase === "ready" && !state.isSubmitting) startClock();
  }
}

function bindEvents() {
  dom.ritualTools.forEach((tool) => {
    const action = tool.dataset.action;
    tool.addEventListener("click", () => {
      if (!tool.classList.contains("is-locked")) openActionCard(action, tool);
    });
    tool.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        if (!tool.classList.contains("is-locked")) openActionCard(action, tool);
      }
    });
  });

  dom.sealInvocation?.addEventListener("click", () => {
    if (state.trueNamePieces >= GAME_RULES.sealRequiredTrueNamePieces) {
      openActionCard("seal", dom.sealInvocation);
    }
  });

  dom.actionCard?.querySelector("[data-card-cancel]")?.addEventListener("click", hideActionCard);
  dom.actionCard?.querySelector("[data-card-use]")?.addEventListener("click", () => {
    if (state.selectedAction) runTurnSequence(state.selectedAction);
  });

  dom.dialogueArchiveToggle?.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    setDialogueArchiveOpen(dom.dialogueArchivePanel?.hidden);
  });

  dom.dialogueArchiveClose?.addEventListener("click", (event) => {
    event.preventDefault();
    setDialogueArchiveOpen(false);
  });

  dom.dialogueArchivePanel?.addEventListener("click", (event) => {
    event.stopPropagation();
  });

  dom.playerLog?.addEventListener("click", (event) => {
    event.preventDefault();
    advanceLogSequence();
  });

  dom.frame?.addEventListener("click", (event) => {
    if (!state.advanceResolver && !isLogVisible()) return;
    event.preventDefault();
    event.stopPropagation();
    advanceLogSequence();
  }, true);

  window.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && (state.advanceResolver || isLogVisible())) {
      event.preventDefault();
      advanceLogSequence();
    }
    if (event.key === "Escape") {
      hideActionCard();
      setJournalOpen(false);
    }
  });
  document.addEventListener("visibilitychange", handleVisibilityChange);

  dom.journalToggle?.addEventListener("click", () => setJournalOpen(dom.journalPanel?.hidden));
  dom.journalClose?.addEventListener("click", () => setJournalOpen(false));
  dom.journalPanel?.addEventListener("click", (event) => {
    if (event.target === dom.journalPanel) setJournalOpen(false);
  });
  dom.journalBook?.addEventListener("click", (event) => {
    event.stopPropagation();
  });
}

function resetDemoGame() {
  Object.assign(state, {
    turn: 1,
    phase: "ready",
    sanity: GAME_RULES.startingSanity,
    soulfire: GAME_RULES.startingSoulfire,
    curse: GAME_RULES.startingCurse,
    shield: 0,
    shieldExpiresOnTurn: 0,
    partialTrueName: 0,
    suspicion: 0,
    trueNamePieces: 0,
    trueNamePieceIds: [],
    acquiredClues: [],
    suspectClues: [],
    falseClues: [],
    revealedFalseClues: [],
    tabooEvents: [],
    turnRecords: [],
    lastInvestigation: "",
    lastInfoTargetKey: "",
    lastDefeatReason: "",
    timeoutCount: 0,
    lastEnemyAction: "",
    selectedAction: "",
    selectedInfoTargetKey: "",
    playerActionHistory: [],
    enemyActionCandidates: null,
    allowedActions: null,
    sealInterferenceLevel: 0,
    logAwaitingAdvance: false,
    turnEndAwaitingAdvance: false,
    dialogueArchive: [],
    clockPausedByJournal: false,
    clockWasRunningBeforeHidden: false,
    clockRenderCache: {
      angle: "",
      urgent: false,
      expired: false,
      tooltip: ""
    },
    isSubmitting: false,
    remainingSeconds: GAME_RULES.timerSeconds,
    advanceResolver: null
  });
  hideActionCard();
  clearDialogueLogs();
  hideTurnEndCue();
  setDialogueArchiveOpen(false);
  renderDialogueArchive();
  hidePlayerLog();
  hideEnemyVoice();
  hideSealInterference();
  if (dom.defeatJumpscare) {
    dom.defeatJumpscare.hidden = true;
    dom.defeatJumpscare.classList.remove("is-active");
  }
  renderAll();
  resetClock();
  setTurnState("");
}

window.gamePrototypeState = {
  state,
  resetDemoGame,
  setSanity(value) {
    state.sanity = clamp(value, 0, GAME_RULES.maxSanity);
    renderAll();
  },
  setSoulfire(value) {
    state.soulfire = clamp(value, 0, GAME_RULES.maxSoulfire);
    renderAll();
  },
  setTrueNamePieces(value) {
    const count = clamp(value, 0, 3);
    state.trueNamePieceIds = TRUTH_PIECES.slice(0, count).map((piece) => piece.id);
    state.trueNamePieces = state.trueNamePieceIds.length;
    renderAll();
  },
  setAllowedActions(actions) {
    state.allowedActions = Array.isArray(actions) ? actions : null;
    renderToolAvailability();
  },
  setTimeoutCount(value) {
    state.timeoutCount = clamp(value, 0, 99);
    renderJournal();
    renderClock();
  },
  setSealInterference(value) {
    state.sealInterferenceLevel = clamp(value, 0, 2);
  },
  applyJournalRecord,
  applyTurnStateChanges,
  runTurnSequence
};

bindEvents();
resetDemoGame();
