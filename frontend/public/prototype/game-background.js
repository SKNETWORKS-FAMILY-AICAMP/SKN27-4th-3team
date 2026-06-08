/*
  LLM EDIT GUIDE
  - Change GAME_RULES for numbers such as max turn, sanity, soulfire, and timer.
  - Change ACTION_CARDS when replacing ritual actions or tool art.
  - Replace resolveTurnResult() only when wiring a real turn-result provider.
  - Keep enemy action hidden until the turn result has returned.
  - Keep result text split into reveal, judgment, state, changes, and flavor sections.
*/

var prototypeScriptRunId = document.currentScript?.dataset.prototypeRunId || "";
var prototypeActiveRunId = window.__mirrorGuestPrototypeActiveRunId || "";
var shouldBootPrototype = !prototypeActiveRunId || !prototypeScriptRunId || prototypeActiveRunId === prototypeScriptRunId;

if (shouldBootPrototype) {
window.__mirrorGuestPrototypeCleanup?.();

const prototypeManagedEvents = [];
const DEFAULT_PLAYER_DISPLAY_NAME = "나";
const MASKED_APPARITION_DISPLAY_NAME = "거울 속 목소리";
const DEFAULT_TRUE_NAME_FRAGMENTS_REQUIRED = 2;

function addPrototypeEvent(target, type, handler, options) {
  if (!target) return;
  target.addEventListener(type, handler, options);
  prototypeManagedEvents.push(() => target.removeEventListener(type, handler, options));
}

window.__mirrorGuestPrototypeCleanup = () => {
  while (prototypeManagedEvents.length) {
    prototypeManagedEvents.pop()?.();
  }

  window.clearInterval(window.gamePrototypeState?.state?.timerId);
  window.clearTimeout(window.gamePrototypeState?.state?.ambientDialogueTimer);
  window.clearTimeout(window.gamePrototypeState?.state?.progressHintTimer);
  delete window.gamePrototypeState;
};

const GAME_RULES = {
  maxTurn: 12,
  timerSeconds: 25,
  maxSanity: 12,
  maxSoulfire: 5,
  maxCurseTrace: 5,
  maxFalseClues: 3,
  startingSanity: 12,
  startingSoulfire: 3,
  startingCurse: 0,
  turnStartSoulfireRecovery: 2,
  sealRequiredTrueNamePieces: DEFAULT_TRUE_NAME_FRAGMENTS_REQUIRED
};

const RESULT_SCENE = {
  clearImage: "assets/clear_.png",
  gameOverImage: "assets/gameover_.png",
  clearDelayMs: 0,
  gameOverDelayMs: 2700
};

const LLM_UI_LIMITS = {
  maxChars: 90,
  maxLines: 2
};

const LLM_DISPLAY_SLOTS = {
  protagonist: "left_system_message",
  spirit: "right_apparition_message",
  system: "center_system_message"
};

const OFFICIAL_ACTION_CODE_BY_UI_ACTION = {
  silence: "silence",
  guard: "guard",
  curse: "curse",
  contract: "contract",
  insight: "insight",
  deceive: "trick",
  seal: "seal"
};

const OFFICIAL_INFO_TARGET_KEY_BY_UI_TARGET = {
  attic_diary: "mirror_back",
  truth_mirror: "truth_mirror",
  stitched_mouth: "missing_child_voice",
  bloodied_teddy: "forgotten_room",
  ian_reflection: "self_reflection",
  family_journal: "family_journal",
  nameless_thread: "nameless_thread",
  basement_wall: "basement_wall",
  mirror_back: "mirror_back",
  mirror_surface: "mirror_surface",
  missing_child_voice: "missing_child_voice",
  forgotten_room: "forgotten_room",
  self_reflection: "self_reflection"
};

const AMBIENT_DIALOGUE_START_DELAY_MS = 1400;
const AMBIENT_DIALOGUE_INTERVAL_MS = 5200;
const AMBIENT_DIALOGUE_END_DELAY_MS = 2600;
const SERVER_WAIT_HINT_DELAY_MS = 2000;
const INTERACTION_CUE_TEXT = "클릭 또는 Enter로 계속";

const AMBIENT_DIALOGUE_LINES = [
  {
    side: "ian",
    speaker: DEFAULT_PLAYER_DISPLAY_NAME,
    text: "여기까지 왔어. 네 이름이 왜 기록에서 지워졌는지 확인하려고."
  },
  {
    side: "spirit",
    speaker: "거울 속 목소리",
    text: "이름은 필요 없어. 문이 닫히면 아무도 더 묻지 않아."
  },
  {
    side: "ian",
    speaker: DEFAULT_PLAYER_DISPLAY_NAME,
    text: "그 문이 널 가둔 거잖아. 나는 깨뜨리러 온 게 아니라 사실을 보러 왔어."
  },
  {
    side: "spirit",
    speaker: "거울 속 목소리",
    text: "사실을 보면 달라져? 죽은 사람은 돌아오지 않아."
  },
  {
    side: "ian",
    speaker: DEFAULT_PLAYER_DISPLAY_NAME,
    text: "그래도 거짓말 위에 널 그대로 둘 수는 없어. 천천히 확인할게."
  },
  {
    side: "spirit",
    speaker: "거울 속 목소리",
    text: "그럼 봐. 네가 잃어버린 밤도 같이 보게 될 테니까."
  }
];

const ACTION_CARDS = {
  silence: {
    title: "침묵",
    kicker: "검은 초",
    cost: 0,
    type: "방해",
    symbol: "초",
    image: "assets/action-card-silence.png",
    desc: "거울 안쪽의 속삭임을 끊고 다음 턴 의식력을 1 회복한다.",
    playerLine: "초를 낮춘다. 먼저 방 안의 소리를 줄여야 한다.",
    briefing: "검은 초가 낮게 타오른다. 거울 안쪽에서 번지던 속삭임이 잠시 멀어지고, 나는 내 숨소리를 되찾는다."
  },
  guard: {
    title: "수호",
    kicker: "방어진을 든 순례자",
    cost: 1,
    type: "방어",
    symbol: "방어진",
    image: "assets/action-card-guard.png",
    desc: "저주 피해를 줄이고 보호막을 얻는다.",
    playerLine: "방어진을 세운다. 지금은 버티는 쪽이 맞다.",
    briefing: "두 손 사이에 낡은 방어진이 떠오른다. 빛은 약하지만, 저주의 길목을 잠시 막아낸다."
  },
  curse: {
    title: "저주",
    kicker: "녹슨 못",
    cost: 2,
    type: "공격",
    symbol: "못",
    image: "assets/action-card-curse.png",
    desc: "거울 안쪽의 힘을 밀어내지만 저주 흔적이 깊어질 수 있다.",
    playerLine: "녹슨 못을 박는다. 거울 안쪽의 힘을 밀어내 본다.",
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
    playerLine: "기록의 빈칸에 대가를 건다. 남은 흔적을 확인해야 한다.",
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
    playerLine: "유리 조각을 들어 균열을 살핀다. 진짜 단서와 거짓을 가른다.",
    briefing: "깨진 유리 조각이 차갑게 빛난다. 비친 얼굴 뒤편으로 설명할 수 없는 그림자가 겹쳐진다."
  },
  deceive: {
    title: "속임수",
    kicker: "위조 메모",
    cost: 1,
    type: "교란",
    symbol: "잉크",
    image: "assets/action-card-deceive.png",
    desc: "뒤틀린 문장과 위조 단서로 거울 안쪽의 간파를 흐린다.",
    playerLine: "위조 메모를 섞는다. 안쪽의 시선이 다른 곳을 보게 한다.",
    briefing: "잉크 번진 메모들이 탁자 위에서 어긋난 순서로 겹친다. 거울 안쪽의 시선이 잠시 잘못된 문장에 묶인다."
  },
  seal: {
    title: "봉인",
    kicker: "진명 선언",
    cost: 2,
    type: "조건부",
    symbol: "명",
    image: "assets/seal-card.png",
    desc: "진명 조각이 충분히 모였을 때 숨겨진 이름을 되찾게 하는 선언을 시도한다.",
    playerLine: "모은 이름을 거울 앞에 둔다. 이제 끝낼 수 있는지 확인한다.",
    briefing: "이름이 거울 앞에 떨어진다. 검은 실이 재처럼 풀리고, 은빛 표면 전체에 거미줄 같은 금이 번진다."
  }
};

const ENEMY_ACTIONS = [
  { key: "deceive", label: "속임수", action: "괴이 행동: 속임수", line: "그 문장은 네가 쓴 게 아니야." },
  { key: "silence", label: "침묵", action: "괴이 행동: 침묵", line: "소리가 멎으면 기억도 멎어." },
  { key: "contract", label: "계약", action: "괴이 행동: 계약", line: "빈칸을 열면 네 것도 비게 돼." },
  { key: "insight", label: "간파", action: "괴이 행동: 간파", line: "보이는 대로 믿지 마." },
  { key: "curse", label: "저주", action: "괴이 행동: 저주", line: "아픈 곳을 고르면 더 잘 남아." },
  { key: "guard", label: "수호", action: "괴이 행동: 수호", line: "닫아 두면 아무도 들어오지 못해." }
];

const CARD_VISUAL_COPY = {
  guard: {
    card: {
      title: "수호",
      kicker: "방어진을 든 순례자",
      symbol: "방어진",
      image: "assets/action-card-guard.png",
      playerLine: "방어진을 세운다. 지금은 버티는 쪽이 맞다.",
      briefing: "수호의 그림, 두 손 사이에 낡은 방어진이 떠오른다. 빛은 약하지만 저주의 길목을 잠시 막아낸다."
    },
    enemy: {
      label: "수호 / 방어진",
      action: "괴이 행동: 수호 / 방어진",
      line: "닫힌 방은 오래 버틴다."
    }
  },
  silence: {
    card: {
      title: "침묵",
      kicker: "날개 달린 사슴",
      symbol: "날개",
      desc: "침묵 카드. 검은 날개를 펼친 사슴 형상이 거울의 목소리를 잠시 덮어 다음 턴 혼불을 1 회복한다.",
      playerLine: "검은 날개가 접히듯 방 안의 소리를 낮춘다.",
      briefing: "침묵의 그림, 검은 날개가 카드 위에서 천천히 접힌다. 그 그림자가 거울 면을 스치자 안쪽의 속삭임이 한 박자 늦어지고, 남은 혼불이 다시 살아난다."
    },
    enemy: {
      label: "침묵 / 검은 날개",
      action: "괴이 행동: 침묵 / 검은 날개",
      line: "말하지 않으면 아무 일도 없었던 것처럼 남아."
    }
  },
  curse: {
    card: {
      title: "저주",
      kicker: "마른 가지의 형틀",
      symbol: "십자가",
      desc: "저주 카드. 가시처럼 뻗은 십자가가 거울 속 형상을 찌르지만, 저주의 흔적도 함께 깊어진다.",
      playerLine: "가시 십자가를 세운다. 거울 안쪽의 힘이 어디서 새는지 본다.",
      briefing: "저주의 그림, 가시 십자가가 카드 중앙에 솟는다. 그 끝이 거울 면을 긁자 안쪽의 형상이 비틀리지만, 손목을 감은 저주도 더 세게 조인다."
    },
    enemy: {
      label: "저주 / 가시 십자가",
      action: "괴이 행동: 저주 / 가시 십자가",
      line: "상처를 누르면 네 손에도 자국이 남아."
    }
  },
  contract: {
    card: {
      title: "계약",
      kicker: "달 아래 선 후드",
      symbol: "후드",
      desc: "계약 카드. 달 아래 멈춰 선 순례자의 그림자가 기록을 들추어 진명 조각을 찾는다.",
      playerLine: "달 아래 선 그림자를 따라 기록의 빈칸을 확인한다.",
      briefing: "계약의 그림, 달의 순례자가 달빛 속에서 한 걸음 앞으로 나온다. 검은 옷자락이 펼쳐질 때마다 오래 닫힌 기록의 문장이 다시 떠오른다."
    },
    enemy: {
      label: "계약 / 달의 순례자",
      action: "괴이 행동: 계약 / 달의 순례자",
      line: "빈칸은 값을 요구해."
    }
  },
  insight: {
    card: {
      title: "간파",
      kicker: "사슴뿔의 군주",
      symbol: "뿔",
      desc: "간파 카드. 뿔의 왕이 거울 안쪽을 정면으로 응시해 다음 징후와 거짓 단서를 가른다.",
      playerLine: "뿔의 형상이 향한 곳을 본다. 흐린 징후를 하나씩 가른다.",
      briefing: "간파의 그림, 뿔의 왕이 달을 가른다. 왕관처럼 솟은 뿔 사이로 거울의 표면이 얇아지고, 흐릿했던 징후가 하나씩 윤곽을 얻는다."
    },
    enemy: {
      label: "간파 / 뿔의 왕",
      action: "괴이 행동: 간파 / 뿔의 왕",
      line: "너도 네 얼굴을 제대로 못 보고 있어."
    }
  },
  deceive: {
    card: {
      title: "속임수",
      kicker: "달을 삼킨 나무",
      symbol: "고목",
      desc: "속임수 카드. 뒤틀린 고목의 그림자가 거울의 시선을 흐려, 거짓 문장으로 괴이의 판단을 흔든다.",
      playerLine: "뒤틀린 고목의 그림자를 섞어 시선을 다른 문장으로 돌린다.",
      briefing: "속임수의 그림, 뒤틀린 고목이 달빛을 갈라 먹는다. 카드 속 고목의 그림자가 책상 위로 번지자 거울 안쪽의 시선이 엉뚱한 문장을 따라 흔들린다."
    },
    enemy: {
      label: "속임수 / 뒤틀린 고목",
      action: "괴이 행동: 속임수 / 뒤틀린 고목",
      line: "기억은 틀린 길도 진짜처럼 보여 줘."
    }
  }
};

Object.entries(CARD_VISUAL_COPY).forEach(([key, copy]) => {
  if (ACTION_CARDS[key]) Object.assign(ACTION_CARDS[key], copy.card);
  const enemyAction = ENEMY_ACTIONS.find((action) => action.key === key);
  if (enemyAction) Object.assign(enemyAction, copy.enemy);
});

const ACTION_RULE_NOTES = {
  curse: "비용 2. 상대 이성을 2 깎는다. 수호를 만나면 피해는 0이 되고 상대에게 보호막이 남는다.",
  guard: "비용 1. 저주를 받아내면 피해를 0으로 만들고 보호막 1을 얻는다. 보호막은 다음 저주 피해 2를 막고 소모된다.",
  insight: "비용 1. 단서를 판별하거나 괴이의 다음 행동 성향 일부를 확인한다. 속임수와 맞서면 확률 판정을 거친다.",
  deceive: "비용 1. 거짓 단서를 남겨 간파를 흔든다. 간파에 걸리면 차단될 수 있다.",
  silence: "비용 0. 정보 공개를 막고 다음 턴 의식력을 1 더 회복한다. 직접 피해를 막지는 못한다.",
  contract: "비용 3. 성공하면 진명 조각 후보 또는 비밀 노출도 1을 얻는다. 저주나 속임수에 방해받으면 실패할 수 있다."
};

Object.entries(ACTION_RULE_NOTES).forEach(([key, note]) => {
  if (!ACTION_CARDS[key]) return;
  ACTION_CARDS[key].desc = note;
});

const COMPATIBILITY_PUBLIC_LOGS = {
  curse: {
    curse: "두 저주가 정면으로 부딪혔다. 주사위 결과가 의식의 방향을 갈랐다.",
    guard: "수호가 저주를 받아냈다. 방어자의 주변에 옅은 막이 남았다.",
    insight: "간파가 완성되기 전에 저주가 파고들었다. 단서는 흐려졌지만 저주의 흔적은 남았다.",
    deceive: "거짓 기척 사이로 저주가 스쳤다. 완전히 꿰뚫지는 못했지만 흔적은 남았다.",
    silence: "침묵은 저주를 막지 못했다. 조용한 의식장에 균열이 번졌다.",
    contract: "계약이 맺어지기 전에 저주가 끼어들었다. 대가는 허공으로 흩어졌다.",
    seal: "봉인의 문장이 흔들렸다. 저주가 의식의 틈을 물고 늘어졌다."
  },
  guard: {
    curse: "수호가 저주를 받아냈다. 방어자의 주변에 옅은 막이 남았다.",
    guard: "두 수호가 빈 의식장을 감쌌지만, 막아낼 저주는 오지 않았다.",
    insight: "간파는 방어의 흔적만 읽어냈다. 진명은 드러나지 않았다.",
    deceive: "수호는 잘못된 위협을 향했다. 그 틈에 거짓 단서가 의식장에 섞였다.",
    silence: "수호는 허공을 지켰고, 침묵은 다음 의식을 준비했다.",
    contract: "수호는 계약을 완전히 막지 못했다. 그러나 새겨진 이름은 아직 온전하지 않았다.",
    seal: "수호의 막은 봉인의 문장을 막지 못했다. 의식은 계속 이어졌다."
  },
  insight: {
    curse: "간파가 완성되기 전에 저주가 파고들었다. 단서는 흐려졌지만 저주의 흔적은 남았다.",
    guard: "간파는 방어의 흔적만 읽어냈다. 진명은 드러나지 않았다.",
    insight: "서로가 서로를 읽으려 했다. 답은 나오지 않았지만 의심만 짙어졌다.",
    deceive: "간파가 거짓 기척을 더듬었다. 진실과 속임수 중 하나가 모습을 드러냈다.",
    silence: "침묵은 답을 내놓지 않았다. 대신 다음 의식의 방향이 조금 좁혀졌다.",
    contract: "계약의 빈틈이 드러났다. 맺어지지 못한 대가가 계약자에게 되돌아갔다.",
    seal: "간파가 봉인의 문장을 흔들었다. 의식의 약한 획이 드러났다."
  },
  deceive: {
    curse: "거짓 기척 사이로 저주가 스쳤다. 완전히 꿰뚫지는 못했지만 흔적은 남았다.",
    guard: "수호는 잘못된 위협을 향했다. 그 틈에 거짓 단서가 의식장에 섞였다.",
    insight: "간파가 거짓 기척을 더듬었다. 진실과 속임수 중 하나가 모습을 드러냈다.",
    deceive: "거짓과 거짓이 겹쳤다. 아무 단서도 남지 않았지만 서로를 향한 의심은 짙어졌다.",
    silence: "속임수는 침묵 속에서 방향을 잃었다. 조용한 쪽만 다음 의식을 준비했다.",
    contract: "거짓된 조건이 계약을 더럽혔다. 대가는 맺어지지 않았고 흔적만 남았다.",
    seal: "거짓 단서가 봉인의 문장을 비틀었다. 의식은 잘못된 이름을 붙잡고 무너졌다."
  },
  silence: {
    curse: "침묵은 저주를 막지 못했다. 조용한 의식장에 균열이 번졌다.",
    guard: "수호는 허공을 지켰고, 침묵은 다음 의식을 준비했다.",
    insight: "침묵은 답을 내놓지 않았다. 대신 다음 의식의 방향이 조금 좁혀졌다.",
    deceive: "속임수는 침묵 속에서 방향을 잃었다. 조용한 쪽만 다음 의식을 준비했다.",
    silence: "아무 말도 오가지 않았다. 그러나 양쪽 모두 다음 의식을 위한 힘을 모았다.",
    contract: "침묵은 계약을 방해하지 못했다. 말 없는 대가가 의식장에 새겨졌다.",
    seal: "침묵이 봉인의 마지막 음절을 삼켰다. 그래도 문장은 아직 이어질 수 있었다."
  },
  contract: {
    curse: "계약이 맺어지기 전에 저주가 끼어들었다. 대가는 허공으로 흩어졌다.",
    guard: "수호는 계약을 완전히 막지 못했다. 그러나 새겨진 이름은 아직 온전하지 않았다.",
    insight: "계약의 빈틈이 드러났다. 맺어지지 못한 대가가 계약자에게 되돌아갔다.",
    deceive: "거짓된 조건이 계약을 더럽혔다. 대가는 맺어지지 않았고 흔적만 남았다.",
    silence: "침묵은 계약을 방해하지 못했다. 말 없는 대가가 의식장에 새겨졌다.",
    contract: "두 계약이 서로의 대가를 갉아먹었다. 이름은 완성되지 않았고 흔적만 깊어졌다.",
    seal: "계약의 대가가 봉인보다 먼저 도착했다. 문장은 끊어졌고 계약자에게 흔적이 남았다."
  },
  seal: {
    curse: "저주가 봉인의 문장을 흔들었다. 그러나 이름이 충분하다면 의식은 닫힐 수 있었다.",
    guard: "수호의 막은 봉인의 문장을 막지 못했다. 의식은 계속 이어졌다.",
    insight: "간파가 봉인의 약한 획을 건드렸다. 그래도 문장은 아직 완성될 수 있었다.",
    deceive: "거짓 단서가 봉인의 문장을 비틀었다. 의식은 잘못된 이름을 붙잡고 무너졌다.",
    silence: "침묵이 봉인의 마지막 음절을 삼켰다. 그래도 문장은 아직 이어질 수 있었다.",
    contract: "계약의 대가가 봉인보다 먼저 도착했다. 문장은 끊어졌고 계약자에게 흔적이 남았다.",
    seal: "두 봉인의 문장이 동시에 떠올랐다. 조건을 갖춘 쪽의 의식만 완성된다."
  }
};

function getCompatibilityPublicLog(playerAction, enemyAction) {
  return COMPATIBILITY_PUBLIC_LOGS[playerAction]?.[enemyAction] || "";
}

const FALSE_CLUE_RULES = [
  {
    id: "false_clue_1",
    text: "거울을 깨면 끝난다.",
    targets: ["truth_mirror", "self_reflection"]
  },
  {
    id: "false_clue_2",
    text: "피티는 플레이어의 이름을 빼앗으려 한다.",
    targets: ["nameless_thread", "self_reflection"]
  },
  {
    id: "false_clue_3",
    text: "피티를 처치해야 저주가 끝난다.",
    targets: ["basement_wall", "family_journal"],
    requiresTrueNamePieces: 2
  }
];

const INFO_TARGETS = [
  {
    key: "truth_mirror",
    label: "진실의 거울",
    note: "거울 계열 대상. 계약은 이름의 흔적을 더듬고, 간파는 거짓 단서 여부를 가른다."
  },
  {
    key: "family_journal",
    label: "가죽 장정 일기장",
    note: "기록 계열 대상. 간파는 지워진 이름의 첫 획을 확인한다."
  },
  {
    key: "nameless_thread",
    label: "무명실",
    note: "이름과 목소리를 빼앗긴 존재의 상징. 계약은 마지막 목소리를 되돌린다."
  },
  {
    key: "basement_wall",
    label: "지하실 벽",
    note: "상처 계열 대상. 잘못 읽으면 거울 속 목소리를 처치 대상으로 단정하는 거짓 단서가 남는다."
  },
  {
    key: "self_reflection",
    label: "플레이어의 비친 얼굴",
    note: "자기 인식 대상. 반복 조사하면 금기 위반과 거짓 단서 위험이 커진다."
  }
];

const OFFICIAL_ENDING_TEXT = {
  win: "사건 종료 기록.\n피티의 이름이 진실의 거울 앞에서 완성되자, 무명실은 더는 입술을 묶지 못했다.",
  loseSanity: "사건 종료 기록.\n거울은 플레이어의 이름과 피티의 이름을 같은 숨결로 겹쳐 놓았다.",
  loseCurse: "사건 종료 기록.\n저주의 흔적은 살갗이 아니라 이름의 가장자리에 붙어 번졌다.",
  loseTurns: "사건 종료 기록.\n자정의 마지막 소리가 지나가자 진실의 거울은 은빛 표면을 닫았다."
};

const TRUTH_PIECES = [
  {
    id: "true_name_fragment_1",
    title: "일기장에 남은 지워진 이름의 첫 획",
    source: "family_journal",
    reveal: "가죽 장정 일기장은 지워진 이름의 첫 획을 남기고 있다."
  },
  {
    id: "true_name_fragment_2",
    title: "무명실 너머에서 되돌아온 마지막 목소리",
    source: "nameless_thread",
    reveal: "무명실 너머에서 피티의 마지막 목소리가 되돌아온다."
  },
  {
    id: "true_name_fragment_3",
    title: "진실의 거울이 되돌려 준 피티의 이름",
    source: "truth_mirror",
    reveal: "진실의 거울은 감춰진 이름이 피티였음을 되비춘다."
  }
];

function getInfoTargetLabel(key) {
  return INFO_TARGETS.find((target) => target.key === key)?.label || key || "없음";
}

function getInfoTargetNote(key) {
  return INFO_TARGETS.find((target) => target.key === key)?.note || "조사 대상을 선택해야 행동을 사용할 수 있다.";
}

function formatTurnRecordLine(record = {}) {
  const parts = [`${record.turn || "?"}턴`];
  if (record.infoTargetKey) parts.push(getInfoTargetLabel(record.infoTargetKey));
  if (record.tabooViolation) parts.push("금기 흔들림");
  if (record.journalEntry) parts.push(record.journalEntry);
  else if (record.changesSummary) parts.push(`변화 ${record.changesSummary}`);
  if (Array.isArray(record.events) && record.events.length) parts.push(record.events.join(" / "));
  return parts.join(": ");
}

const dom = {
  frame: document.querySelector(".game-frame"),
  clock: document.querySelector("[data-clock]"),
  clockHand: document.querySelector(".clock-hand"),
  actionCard: document.querySelector("[data-action-card]"),
  ritualTools: [...document.querySelectorAll(".ritual-tool[data-action]")],
  ritualEffect: document.querySelector("[data-ritual-effect]"),
  guardWard: document.querySelector("[data-guard-ward]"),
  sealInvocation: document.querySelector(".seal-invocation"),
  sealReason: document.querySelector("[data-seal-reason]"),
  sealInterference: document.querySelector("[data-seal-interference]"),
  sealInterferenceValue: document.querySelector("[data-seal-interference-value]"),
  playerLog: document.querySelector("[data-player-log]"),
  playerLogText: document.querySelector("[data-player-log-text]"),
  ambientDialogue: document.querySelector("[data-ambient-dialogue]"),
  ambientDialogueSpeaker: document.querySelector("[data-ambient-dialogue-speaker]"),
  ambientDialogueText: document.querySelector("[data-ambient-dialogue-text]"),
  protagonistLogStack: document.querySelector("[data-protagonist-log-stack]"),
  systemLogStack: document.querySelector("[data-system-log-stack]"),
  spiritLogStack: document.querySelector("[data-spirit-log-stack]"),
  turnEndCue: document.querySelector("[data-turn-end-cue]"),
  progressOverlay: document.querySelector("[data-progress-overlay]"),
  progressTitle: document.querySelector("[data-progress-title]"),
  progressDetail: document.querySelector("[data-progress-detail]"),
  interactionCue: document.querySelector("[data-interaction-cue]"),
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
  resultScene: document.querySelector("[data-result-scene]"),
  resultImage: document.querySelector("[data-result-image]"),
  journalBook: document.querySelector(".journal-book"),
  journalSections: [...document.querySelectorAll(".journal-section")],
  sealProgressDots: [...document.querySelectorAll(".seal-progress span")]
};

const state = {
  turn: 1,
  caseId: "nameless_curse",
  caseTitle: "무명(無名)의 저주",
  playerDisplayName: DEFAULT_PLAYER_DISPLAY_NAME,
  apparitionDisplayName: MASKED_APPARITION_DISPLAY_NAME,
  isApparitionNameRevealed: false,
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
  llmUiTexts: [],
  ambientDialogueIndex: 0,
  ambientDialogueTimer: null,
  clockPausedByJournal: false,
  clockWasRunningBeforeHidden: false,
  clockRenderCache: {
    angle: "",
    urgent: false,
    expired: false,
    tooltip: ""
  },
  resultShown: false,
  resultAwaitingAdvance: false,
  pendingEnding: null,
  isSubmitting: false,
  remainingSeconds: GAME_RULES.timerSeconds,
  timerId: 0,
  advanceResolver: null,
  progressHintTimer: null
};

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, Number(value)));
}

function formatTwoDigits(value) {
  return String(value).padStart(2, "0");
}

function getRequiredTrueNamePieces() {
  return clamp(
    GAME_RULES.sealRequiredTrueNamePieces,
    1,
    Math.max(1, TRUTH_PIECES.length)
  );
}

function formatTrueNameProgress(value = state.trueNamePieces) {
  const required = getRequiredTrueNamePieces();
  return `${Math.min(value, required)}/${required}`;
}

function getPlayerDisplayName() {
  return state.playerDisplayName || DEFAULT_PLAYER_DISPLAY_NAME;
}

function getApparitionDisplayName() {
  if (!state.isApparitionNameRevealed) return MASKED_APPARITION_DISPLAY_NAME;
  return state.apparitionDisplayName || MASKED_APPARITION_DISPLAY_NAME;
}

function revealApparitionName() {
  state.isApparitionNameRevealed = true;
}

function normalizeLlmText(text) {
  return String(text || "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .slice(0, LLM_UI_LIMITS.maxLines)
    .map((line) => line.length > LLM_UI_LIMITS.maxChars
      ? `${line.slice(0, LLM_UI_LIMITS.maxChars - 1)}...`
      : line)
    .join("\n");
}

function normalizeLlmUiText(entry) {
  if (!entry || typeof entry !== "object") return null;
  return {
    enabled: Boolean(entry.enabled),
    purpose: entry.purpose || "",
    text: entry.text == null ? null : normalizeLlmText(entry.text),
    display_slot: entry.display_slot || null,
    fallback_used: Boolean(entry.fallback_used),
    generation_id: entry.generation_id || null,
    context_refs: Array.isArray(entry.context_refs) ? entry.context_refs : [],
    metadata: {
      status: entry.metadata?.status || (entry.enabled ? "succeeded" : "skipped"),
      provider: entry.metadata?.provider,
      model_id: entry.metadata?.model_id ?? null,
      latency_ms: entry.metadata?.latency_ms,
      error_code: entry.metadata?.error_code,
      error_reason: entry.metadata?.error_reason,
      reason: entry.metadata?.reason
    }
  };
}

function applyLlmUiTexts(entries) {
  state.llmUiTexts = Array.isArray(entries)
    ? entries.map(normalizeLlmUiText).filter(Boolean)
    : [];
}

function getLlmUiText(purpose, displaySlot) {
  return state.llmUiTexts.find((entry) => (
    entry.enabled
    && entry.text
    && entry.purpose === purpose
    && (!displaySlot || entry.display_slot === displaySlot)
  )) || null;
}

function resolveLlmDisplayText(purpose, displaySlot, fallbackText) {
  const llm = getLlmUiText(purpose, displaySlot);
  return {
    text: llm?.text || fallbackText,
    source: llm ? "llm" : "fallback",
    fallbackUsed: !llm
  };
}

function recoverSoulfireForNextTurn() {
  state.soulfire = clamp(
    state.soulfire + GAME_RULES.turnStartSoulfireRecovery,
    0,
    GAME_RULES.maxSoulfire
  );
}

function setTurnState(text) {
  if (!dom.turnState) return;
  dom.turnState.textContent = text || "";
  dom.turnState.hidden = !text;
}

function clearProgressHintTimer() {
  if (!state.progressHintTimer) return;
  window.clearTimeout(state.progressHintTimer);
  state.progressHintTimer = null;
}

function renderProgressOverlay(title, detail = "") {
  if (!dom.progressOverlay || !dom.progressTitle || !dom.progressDetail) return;
  dom.progressTitle.textContent = title;
  dom.progressDetail.textContent = detail;
  dom.progressDetail.hidden = !detail;
  dom.progressOverlay.hidden = false;
}

function setProgressOverlay(title, detail = "") {
  clearProgressHintTimer();
  renderProgressOverlay(title, detail);
}

function clearProgressOverlay() {
  clearProgressHintTimer();
  if (dom.progressOverlay) dom.progressOverlay.hidden = true;
}

function scheduleServerWaitHint() {
  clearProgressHintTimer();
  state.progressHintTimer = window.setTimeout(() => {
    state.progressHintTimer = null;
    renderProgressOverlay(
      "서버 판정 대기 중...",
      "응답이 길어져 최신 판정을 기다리고 있습니다."
    );
  }, SERVER_WAIT_HINT_DELAY_MS);
}

function showInteractionCue(text = INTERACTION_CUE_TEXT) {
  if (!dom.interactionCue) return;
  dom.interactionCue.textContent = text;
  dom.interactionCue.hidden = false;
}

function hideInteractionCue() {
  if (dom.interactionCue) dom.interactionCue.hidden = true;
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
  if (dom.sanityToken) {
    dom.sanityToken.dataset.tooltip = `이성: 0이 되면 ${getPlayerDisplayName()}은 자기 이름과 ${getApparitionDisplayName()}의 이름을 구분하지 못한다.`;
  }
  renderLanternHud();
  renderSanityGauge();

  if (dom.frame) {
    dom.frame.dataset.sanityStage = String(getSanityStage());
    dom.frame.dataset.sealReady = String(state.trueNamePieces >= getRequiredTrueNamePieces());
    dom.frame.setAttribute("aria-label", `${state.caseTitle || "무명의 저주"} 의식 결투 화면`);
  }

  if (dom.turnCount) {
    dom.turnCount.textContent = `${formatTwoDigits(state.turn)}/${GAME_RULES.maxTurn}`;
  }
}

function renderSealState() {
  const required = getRequiredTrueNamePieces();
  const isReady = state.trueNamePieces >= required;

  if (dom.sealInvocation) {
    dom.sealInvocation.classList.toggle("is-locked", !isReady);
    dom.sealInvocation.setAttribute("aria-disabled", String(!isReady));
  }

  if (dom.sealReason) {
    dom.sealReason.textContent = isReady ? "사용 가능" : `진명 ${formatTrueNameProgress()} 필요`;
  }

  dom.sealProgressDots.forEach((dot, index) => {
    dot.classList.toggle("is-filled", index < state.trueNamePieces);
    dot.hidden = index >= required;
  });
}

function renderJournal() {
  if (dom.journalCount) dom.journalCount.textContent = formatTrueNameProgress();
  if (dom.truthProgress) dom.truthProgress.textContent = formatTrueNameProgress();
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
    const allFalseClues = [...state.falseClues, ...state.suspectClues, ...state.revealedFalseClues]
      .filter((clue, index, list) => clue && list.findIndex((item) => item.id === clue.id) === index);
    dom.falseClues.innerHTML = allFalseClues.length
      ? allFalseClues.map((clue) => {
        const isRevealed = state.revealedFalseClues.some((item) => item.id === clue.id);
        return `<li data-clue-state="${isRevealed ? "revealed" : "suspect"}"><span>${clue.text}</span><em>${isRevealed ? "확정 거짓" : "의심 중"}</em></li>`;
      }).join("")
      : "<li>아직 없다.</li>";
  }

  if (dom.timeoutPolicy) {
    const capped = Math.min(state.timeoutCount, 3);
    dom.timeoutPolicy.textContent = `누적 침묵 ${capped}/3. ${state.timeoutCount >= 3 ? "침묵이 습관이 되자 안쪽의 것도 그 틈을 파고들기 시작했다." : `아직은 ${getPlayerDisplayName()}의 망설임으로 기록된다.`}`;
  }

  if (dom.turnRecords) {
    dom.turnRecords.innerHTML = state.turnRecords.length
      ? state.turnRecords.slice(-8).map((record) => {
        const target = record.infoTargetKey ? ` <span>${getInfoTargetLabel(record.infoTargetKey)}</span>` : "";
        const taboo = record.tabooViolation ? " <em>금기 흔들림</em>" : "";
        const entry = record.journalEntry ? `<p>${record.journalEntry}</p>` : "";
        const summary = record.practicalSummary ? `<small>${record.practicalSummary}</small>` : "";
        return `<li><strong>${record.turn}턴</strong>${target}${taboo}${entry}${summary}</li>`;
      }).join("")
      : "<li>아직 남긴 턴 일지가 없다.</li>";
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
      trueNamePieceIds, acquiredClues, suspectClues, falseClues, revealedFalseClues,
      turnRecords, shield, partialTrueName, suspicion, lastInvestigation
    }
  */
  if (Array.isArray(record.trueNamePieceIds)) {
    state.trueNamePieceIds = record.trueNamePieceIds.slice(0, TRUTH_PIECES.length);
    state.trueNamePieces = state.trueNamePieceIds.length;
  }
  if (Array.isArray(record.acquiredClues)) state.acquiredClues = [...record.acquiredClues];
  if (Array.isArray(record.suspectClues)) state.suspectClues = [...record.suspectClues];
  if (Array.isArray(record.falseClues)) state.falseClues = [...record.falseClues];
  if (Array.isArray(record.revealedFalseClues)) state.revealedFalseClues = [...record.revealedFalseClues];
  if (Array.isArray(record.turnRecords)) state.turnRecords = [...record.turnRecords];
  if (Number.isFinite(record.shield)) state.shield = clamp(record.shield, 0, 1);
  if (Number.isFinite(record.partialTrueName)) state.partialTrueName = clamp(record.partialTrueName, 0, 2);
  if (Number.isFinite(record.suspicion)) state.suspicion = clamp(record.suspicion, 0, 99);
  if (typeof record.lastInvestigation === "string") state.lastInvestigation = record.lastInvestigation;

  renderAll();
}

function actionCodeToUiAction(code) {
  return code === "trick" ? "deceive" : code;
}

function getNumeric(value, fallback) {
  return Number.isFinite(value) ? value : fallback;
}

function toTrueNamePieceIds(count) {
  const safeCount = clamp(count, 0, TRUTH_PIECES.length);
  return TRUTH_PIECES.slice(0, safeCount).map((piece) => piece.id);
}

function normalizePrototypeClue(clue) {
  return {
    id: clue?.clue_id || clue?.id || "",
    text: clue?.text || "",
    source: clue?.clue_id || clue?.source || ""
  };
}

function isTrueNameClue(clue) {
  return clue?.truth_state === "true_revealed" || String(clue?.clue_id || "").startsWith("true_name_fragment");
}

function isFalseClue(clue) {
  return clue?.truth_state === "false_revealed" || String(clue?.clue_id || "").startsWith("false_clue");
}

function applyMatchState(match) {
  if (!match || typeof match !== "object") return;

  const resources = match.player?.resources || {};
  const required = getNumeric(
    resources.true_name_fragments_required,
    getNumeric(match.opponent?.public_state?.true_name_fragments_required, DEFAULT_TRUE_NAME_FRAGMENTS_REQUIRED)
  );
  GAME_RULES.sealRequiredTrueNamePieces = clamp(required, 1, TRUTH_PIECES.length);
  GAME_RULES.maxTurn = getNumeric(match.turn?.max_turns, GAME_RULES.maxTurn);

  state.caseId = match.case?.case_id || state.caseId;
  state.caseTitle = match.case?.title || state.caseTitle;
  state.playerDisplayName = match.player?.display_name || DEFAULT_PLAYER_DISPLAY_NAME;
  state.apparitionDisplayName = match.opponent?.display_name || state.apparitionDisplayName || MASKED_APPARITION_DISPLAY_NAME;
  state.turn = clamp(match.turn?.turn_number || state.turn, 1, GAME_RULES.maxTurn);
  state.sanity = clamp(getNumeric(resources.sanity, state.sanity), 0, getNumeric(resources.sanity_max, GAME_RULES.maxSanity));
  state.soulfire = clamp(getNumeric(resources.ritual_power, state.soulfire), 0, getNumeric(resources.ritual_power_max, GAME_RULES.maxSoulfire));
  state.curse = clamp(getNumeric(resources.curse_marks, state.curse), 0, getNumeric(resources.curse_marks_max, GAME_RULES.maxCurseTrace));
  state.shield = clamp(getNumeric(resources.shield, state.shield), 0, getNumeric(resources.shield_max, 1));
  state.partialTrueName = clamp(getNumeric(resources.incomplete_true_name_fragments, state.partialTrueName), 0, 2);
  state.suspicion = clamp(getNumeric(resources.suspicion, state.suspicion), 0, getNumeric(resources.suspicion_max, 3));
  state.timeoutCount = clamp(getNumeric(resources.timeout_count, state.timeoutCount), 0, 99);
  state.trueNamePieceIds = toTrueNamePieceIds(getNumeric(resources.true_name_fragments, state.trueNamePieces));
  state.trueNamePieces = state.trueNamePieceIds.length;
  state.remainingSeconds = clamp(
    getNumeric(match.turn?.remaining_seconds, state.remainingSeconds),
    0,
    GAME_RULES.timerSeconds
  );
  state.allowedActions = Array.isArray(match.available_actions)
    ? match.available_actions
      .filter((action) => action.enabled)
      .map((action) => actionCodeToUiAction(action.code))
    : state.allowedActions;

  const clues = Array.isArray(match.clues) ? match.clues : [];
  state.acquiredClues = clues.filter(isTrueNameClue).map((clue) => clue.text).filter(Boolean);
  state.suspectClues = clues
    .filter((clue) => isFalseClue(clue) && clue.truth_state !== "false_revealed")
    .map(normalizePrototypeClue)
    .filter((clue) => clue.id && clue.text);
  state.falseClues = clues
    .filter(isFalseClue)
    .map(normalizePrototypeClue)
    .filter((clue) => clue.id && clue.text);
  state.revealedFalseClues = clues
    .filter((clue) => clue.truth_state === "false_revealed")
    .map(normalizePrototypeClue)
    .filter((clue) => clue.id && clue.text);

  if (Array.isArray(match.recent_public_logs) && match.recent_public_logs.length) {
    state.turnRecords = match.recent_public_logs.map((log) => ({
      turn: log.turn_number,
      journalEntry: log.text,
      journalEntrySource: "server",
      practicalSummary: "",
      changesSummary: "",
      events: []
    }));
  }

  renderAll();
  renderClock();
}

function clearAmbientDialogueTimer() {
  if (state.ambientDialogueTimer) {
    window.clearTimeout(state.ambientDialogueTimer);
    state.ambientDialogueTimer = null;
  }
}

function hideAmbientDialogue() {
  if (!dom.ambientDialogue) return;
  dom.ambientDialogue.hidden = true;
  dom.ambientDialogue.classList.remove("is-visible");
}

function showAmbientDialogueLine(entry) {
  if (!dom.ambientDialogue || !dom.ambientDialogueSpeaker || !dom.ambientDialogueText) return;
  dom.ambientDialogue.dataset.side = entry.side;
  dom.ambientDialogueSpeaker.textContent = entry.speaker;
  dom.ambientDialogueText.textContent = entry.text;
  dom.ambientDialogue.hidden = false;
  dom.ambientDialogue.classList.remove("is-visible");
  void dom.ambientDialogue.offsetWidth;
  dom.ambientDialogue.classList.add("is-visible");
}

function playNextAmbientDialogueLine() {
  if (state.ambientDialogueIndex >= AMBIENT_DIALOGUE_LINES.length) {
    state.ambientDialogueTimer = window.setTimeout(finishAmbientDialogue, AMBIENT_DIALOGUE_END_DELAY_MS);
    return;
  }

  showAmbientDialogueLine(AMBIENT_DIALOGUE_LINES[state.ambientDialogueIndex]);
  state.ambientDialogueIndex += 1;
  state.ambientDialogueTimer = window.setTimeout(playNextAmbientDialogueLine, AMBIENT_DIALOGUE_INTERVAL_MS);
}

function advanceAmbientDialogue() {
  if (state.phase !== "intro") return false;
  clearAmbientDialogueTimer();

  if (state.ambientDialogueIndex >= AMBIENT_DIALOGUE_LINES.length) {
    finishAmbientDialogue();
    return true;
  }

  playNextAmbientDialogueLine();
  return true;
}

function startAmbientDialogue() {
  clearAmbientDialogueTimer();
  state.phase = "intro";
  state.ambientDialogueIndex = 0;
  hideAmbientDialogue();
  renderIntroLock();
  if (!dom.ambientDialogue) {
    finishAmbientDialogue();
    return;
  }
  setTurnState("대화");
  state.ambientDialogueTimer = window.setTimeout(playNextAmbientDialogueLine, AMBIENT_DIALOGUE_START_DELAY_MS);
}

function ensureAmbientDialogue() {
  if (state.phase !== "intro") return;
  renderIntroLock();
  if (state.ambientDialogueTimer) return;
  if (!dom.ambientDialogue || state.ambientDialogueIndex >= AMBIENT_DIALOGUE_LINES.length) {
    finishAmbientDialogue();
    return;
  }
  state.ambientDialogueTimer = window.setTimeout(playNextAmbientDialogueLine, 80);
}

function finishAmbientDialogue() {
  clearAmbientDialogueTimer();
  hideAmbientDialogue();
  if (state.phase !== "intro") return;
  state.phase = "ready";
  renderIntroLock();
  setTurnState("");
  renderClock();
  startClock();
}

function renderIntroLock() {
  dom.frame?.classList.toggle("is-intro-locked", state.phase === "intro");
}

function renderToolAvailability() {
  dom.ritualTools.forEach((tool) => {
    const action = tool.dataset.action;
    const isLocked = Boolean(state.allowedActions && !state.allowedActions.includes(action));
    tool.classList.toggle("is-locked", isLocked);
    tool.setAttribute("aria-disabled", String(isLocked));
  });
}

function renderGuardWard() {
  if (!dom.guardWard) return;
  dom.guardWard.classList.toggle("is-held", state.shield > 0);
}

function pulseGuardWard(mode = "active") {
  if (!dom.guardWard) return;
  const className = mode === "break" ? "is-breaking" : "is-activating";
  dom.guardWard.classList.remove("is-activating", "is-breaking");
  void dom.guardWard.offsetWidth;
  dom.guardWard.classList.add(className);
  window.setTimeout(() => {
    dom.guardWard?.classList.remove(className);
    renderGuardWard();
  }, mode === "break" ? 920 : 1100);
}

function renderAll() {
  renderHud();
  renderSealState();
  renderJournal();
  renderJournalNavigation();
  renderToolAvailability();
  renderGuardWard();
  renderIntroLock();
}

function getJournalSectionTitle(section, index) {
  return section.querySelector("h2")?.textContent?.trim() || `일지 ${index + 1}`;
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
    nav.setAttribute("aria-label", "일지 섹션");

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
  if (actionKey === "seal" && state.trueNamePieces < getRequiredTrueNamePieces()) {
    return { canUse: false, reason: `진명 조각 ${getRequiredTrueNamePieces()}개 필요. 현재 ${formatTrueNameProgress()}.` };
  }
  if ((actionKey === "insight" || actionKey === "contract") && !state.selectedInfoTargetKey) {
    return { canUse: false, reason: "조사 대상을 먼저 선택해야 한다." };
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

function playSealReleaseEffect() {
  if (!dom.sealInvocation) return;
  dom.sealInvocation.classList.remove("is-casting");
  void dom.sealInvocation.offsetWidth;
  dom.sealInvocation.classList.add("is-casting");
  window.setTimeout(() => {
    dom.sealInvocation?.classList.remove("is-casting");
  }, 1800);
}

function getCorruptedActionDesc(desc) {
  const stage = getSanityStage();
  if (stage >= 4) return `${desc}\n[연출] 선택지는 처음부터 하나였다.`;
  if (stage >= 3) return `${desc}\n[연출] 네가 고른 게 아니어도 괜찮아.`;
  if (stage >= 2) return `${desc}\n[연출] 보지 말고 선택해.`;
  return desc;
}

function openActionCard(actionKey, sourceElement) {
  if (!dom.actionCard || state.phase === "intro" || state.isSubmitting || isLogVisible()) return;

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
  const infoTargetNote = dom.actionCard.querySelector("[data-card-info-target-note]");
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
  if (infoTargetWrap && infoTargetSelect) {
    infoTargetWrap.hidden = !needsInfoTarget;
    if (needsInfoTarget) {
      state.selectedInfoTargetKey = "";
      const selectedKey = state.selectedInfoTargetKey;
      infoTargetSelect.innerHTML = `<option value="">조사 대상을 선택</option>` + INFO_TARGETS
        .map((target) => `<option value="${target.key}">${target.label}</option>`)
        .join("");
      infoTargetSelect.value = selectedKey;
      if (infoTargetNote) infoTargetNote.textContent = getInfoTargetNote(selectedKey);
      infoTargetSelect.onchange = () => {
        state.selectedInfoTargetKey = infoTargetSelect.value;
        const nextValidation = getActionValidation(actionKey);
        if (infoTargetNote) infoTargetNote.textContent = getInfoTargetNote(state.selectedInfoTargetKey);
        if (cardWarning) {
          cardWarning.textContent = nextValidation.reason;
          cardWarning.hidden = nextValidation.canUse;
        }
        if (useButton) useButton.disabled = !nextValidation.canUse;
      };
    } else {
      state.selectedInfoTargetKey = "";
      infoTargetSelect.onchange = null;
      if (infoTargetNote) infoTargetNote.textContent = "";
    }
  }
  const finalValidation = getActionValidation(actionKey);
  if (cardWarning) {
    cardWarning.textContent = finalValidation.reason;
    cardWarning.hidden = finalValidation.canUse;
  }
  if (useButton) useButton.disabled = !finalValidation.canUse;

  state.selectedAction = actionKey;
  dom.actionCard.dataset.selectedAction = actionKey;
  dom.actionCard.hidden = false;
}

function isLogVisible() {
  return Boolean(state.logAwaitingAdvance || state.turnEndAwaitingAdvance);
}

function trimLogText(text, {
  maxLines = 2,
  keepLabels = false,
  prioritizeChanges = false
} = {}) {
  const lines = String(text || "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  let selected = lines;
  if (prioritizeChanges) {
    const changeLine = lines.find((line) => line.startsWith("[변화]"));
    const otherLines = lines.filter((line) => line !== changeLine).slice(0, Math.max(1, maxLines - 1));
    selected = changeLine ? [...otherLines, changeLine] : lines;
  }

  return selected
    .slice(0, maxLines)
    .map((line) => keepLabels ? line : line.replace(/^\[[^\]]+\]\s*/, "").trim())
    .join("\n");
}

function pushDialogueLog(side, speaker, text, mode = "clean") {
  const stack = side === "spirit"
    ? dom.spiritLogStack
    : side === "system"
      ? dom.systemLogStack
      : dom.protagonistLogStack;
  if (!stack) return;

  const isSystem = side === "system";
  const cleanText = trimLogText(text, {
    maxLines: isSystem ? 3 : 2,
    keepLabels: isSystem,
    prioritizeChanges: isSystem
  });
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
  showInteractionCue();
  dom.turnEndCue.hidden = false;
  dom.turnEndCue.classList.remove("is-active");
  void dom.turnEndCue.offsetWidth;
  dom.turnEndCue.classList.add("is-active");
}

function hideTurnEndCue() {
  state.turnEndAwaitingAdvance = false;
  hideInteractionCue();
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
  showInteractionCue();
  pushDialogueLog(channel, channel === "system" ? "기록" : "나", rendered, corrupted ? "corrupted" : channel);

  if (dom.playerLog && dom.playerLogText) {
    dom.playerLog.dataset.logMode = corrupted ? "corrupted" : "clean";
    dom.playerLogText.textContent = rendered;
    dom.playerLog.hidden = true;
  }
}

function hidePlayerLog() {
  state.logAwaitingAdvance = false;
  hideInteractionCue();
  if (dom.playerLog) dom.playerLog.hidden = true;
}

function waitForAdvance() {
  return new Promise((resolve) => {
    state.advanceResolver = resolve;
  });
}

function waitMs(duration) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, duration);
  });
}

function officialActionCodeFor(actionKey) {
  return OFFICIAL_ACTION_CODE_BY_UI_ACTION[actionKey] || actionKey;
}

function officialInfoTargetKeyFor(infoTargetKey) {
  if (!infoTargetKey) return null;
  return OFFICIAL_INFO_TARGET_KEY_BY_UI_TARGET[infoTargetKey] || infoTargetKey;
}

function newClientNonce() {
  if (window.crypto?.randomUUID) return window.crypto.randomUUID();
  return `prototype-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function buildTurnSubmitPayload(actionKey, options = {}) {
  const officialActionCode = officialActionCodeFor(actionKey);
  const officialInfoTargetKey = officialInfoTargetKeyFor(
    options.infoTargetKey || state.selectedInfoTargetKey
  );
  const payload = {
    action_code: officialActionCode,
    client_nonce: options.clientNonce || newClientNonce()
  };
  if (officialInfoTargetKey) {
    payload.info_target_key = officialInfoTargetKey;
  }
  return payload;
}

function advanceLogSequence() {
  if (state.resultAwaitingAdvance && state.pendingEnding) {
    const { outcome, reason } = state.pendingEnding;
    state.resultAwaitingAdvance = false;
    openEndingScreen(outcome, reason);
    return true;
  }
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
  const display = resolveLlmDisplayText(
    "turn_flavor_text",
    LLM_DISPLAY_SLOTS.spirit,
    enemy.line
  );
  dom.enemyAction.textContent = enemy.action;
  dom.enemyText.textContent = display.text;
  state.logAwaitingAdvance = true;
  showInteractionCue();
  pushDialogueLog("spirit", getApparitionDisplayName(), display.text, display.source === "llm" ? "llm" : "spirit");
  dom.enemyVoice.hidden = true;
}

function hideEnemyVoice() {
  state.logAwaitingAdvance = false;
  hideInteractionCue();
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

function showResultScene(outcome, reason = "unknown") {
  if (!dom.resultScene || !dom.resultImage || state.resultShown) return;
  state.resultShown = true;
  state.resultAwaitingAdvance = true;
  state.pendingEnding = { outcome, reason };
  state.phase = "ended";
  stopClock();
  hideActionCard();
  hidePlayerLog();
  hideEnemyVoice();
  hideTurnEndCue();
  setDialogueArchiveOpen(false);
  clearDialogueLogs();

  const isWin = outcome === "win";
  dom.resultImage.src = isWin ? RESULT_SCENE.clearImage : RESULT_SCENE.gameOverImage;
  dom.resultImage.alt = isWin ? "Clear" : "Game Over";
  dom.resultScene.dataset.outcome = isWin ? "clear" : "game-over";
  dom.resultScene.hidden = false;
  dom.resultScene.setAttribute("aria-hidden", "false");
  dom.resultScene.classList.remove("is-active");
  dom.frame?.classList.remove("is-ending-clear", "is-ending-lose");
  dom.frame?.classList.add("is-ending", isWin ? "is-ending-clear" : "is-ending-lose");
  void dom.resultScene.offsetWidth;
  dom.resultScene.classList.add("is-active");
}

function openEndingScreen(outcome, reason) {
  const target = new URL("ending.html", window.location.href);
  const resultSummary = resolveLlmDisplayText("result_summary", null, "");
  const styleSummary = resolveLlmDisplayText("style_summary", null, "");
  const payload = {
    outcome,
    reason,
    turn: String(Math.min(state.turn, GAME_RULES.maxTurn)),
    truth: formatTrueNameProgress(),
    sanity: `${state.sanity}/${GAME_RULES.maxSanity}`,
    curse: `${state.curse}/${GAME_RULES.maxCurseTrace}`,
    log: state.turnRecords.slice(-4).map(formatTurnRecordLine).join(" | ")
  };
  if (resultSummary.text) {
    payload.result_summary = resultSummary.text;
    payload.result_summary_fallback = String(resultSummary.fallbackUsed);
  }
  if (styleSummary.text) {
    payload.style_summary = styleSummary.text;
    payload.style_summary_fallback = String(styleSummary.fallbackUsed);
  }

  Object.entries(payload).forEach(([key, value]) => {
    target.searchParams.set(key, value);
  });

  if (typeof window.gamePrototypeBridge?.openEndingScreen === "function") {
    window.gamePrototypeBridge.openEndingScreen(payload);
    return;
  }

  window.location.href = target.toString();
}

function scheduleEndingScreen(outcome, reason) {
  const waitsForJumpscare = outcome === "lose" && reason === "sanity";
  const delayMs = waitsForJumpscare ? 4200 : RESULT_SCENE.clearDelayMs;
  window.setTimeout(() => showResultScene(outcome, reason), delayMs);
}

function getEndingScreenState(result) {
  if (result?.seal?.success) return { outcome: "win", reason: "seal" };

  const curseDefeat = result?.stateChanges?.defeatFlags?.contractFailedAtMaxCurse
    || result?.stateChanges?.defeatFlags?.hitByCurseAtMaxCurse;

  if (state.sanity <= 0) return { outcome: "lose", reason: "sanity" };
  if (curseDefeat) return { outcome: "lose", reason: "curse" };
  if (state.turn >= GAME_RULES.maxTurn) return { outcome: "lose", reason: "turns" };
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
    return "";
  }

  if (playerAction === "contract") {
    return "";
  }

  if (playerAction === "deceive") {
    if (state.trueNamePieces >= 2) return "basement_wall";
    return state.lastInfoTargetKey || "truth_mirror";
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
  if (!state.falseClues.some((item) => item.id === clue.id)) state.falseClues.push(clue);
  return clue;
}

function revealSuspectFalseClue(targetKey) {
  const index = state.suspectClues.findIndex((clue) => {
    const rule = FALSE_CLUE_RULES.find((item) => item.id === clue.id);
    return !targetKey || rule?.targets.includes(targetKey);
  });

  if (index < 0) return null;

  const [clue] = state.suspectClues.splice(index, 1);
  if (!state.falseClues.some((item) => item.id === clue.id)) state.falseClues.push(clue);
  state.revealedFalseClues.push(clue);
  return clue;
}

function resolveTableStateChanges(playerAction, enemy, isTimeout) {
  const card = ACTION_CARDS[playerAction];
  const infoTargetKey = getInfoTargetKey(playerAction);
  const isInfoAction = playerAction === "insight" || playerAction === "contract";
  const tabooViolation = Boolean(infoTargetKey && state.lastInfoTargetKey === infoTargetKey);
  const partialBefore = state.partialTrueName;
  const trueNamePiecesBefore = state.trueNamePieceIds.length;
  const suspicionBefore = state.suspicion;
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
  let probabilityCheck = null;
  let diceCheck = null;

  const addFalseClueFromRule = (source, target = infoTargetKey || "truth_mirror") => {
    const clue = addSuspectClue(pickFalseClue(target), source);
    if (clue) suspectClues.push(clue);
    return clue;
  };

  const addPartialPiece = () => {
    partialAfter = clamp(partialAfter + 1, 0, 2);
    if (partialAfter >= 2 && trueNamePieceIds.length < getRequiredTrueNamePieces()) {
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
    const success = roll <= successRate;
    probabilityCheck = {
      type: "insight_deceive",
      suspicionBefore: state.suspicion,
      successRate,
      roll,
      success
    };
    state.suspicion = 0;
    if (success) {
      const revealed = revealSuspectFalseClue(infoTargetKey);
      if (revealed) revealedFalseClues.push(revealed);
      turnEvents.push("간파가 속임수의 결을 붙잡았다. 거짓 기척 하나가 힘을 잃었다.");
    } else if (addFalseClueFromRule("insight_failed")) {
      turnEvents.push("간파가 빗나갔다. 거짓 단서 하나가 일지에 섞였다.");
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
        diceCheck = {
          type: "curse_clash",
          playerRoll,
          enemyRoll,
          winner: playerRoll === enemyRoll ? "tie" : (playerRoll > enemyRoll ? "player" : "enemy")
        };
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
        turnEvents.push("수호가 저주를 받아냈다. 보호막이 다음 저주 피해를 막을 준비를 했다.");
      } else if (enemyAction === "guard") {
        turnEvents.push("양측의 수호가 빈 의식판 위에서 사라졌다. 직접 효과는 없었다.");
      } else if (enemyAction === "insight") {
        turnEvents.push("괴이가 수호의 흔적만 읽었다. 진명 조각은 드러나지 않았다.");
      } else if (enemyAction === "silence") {
        turnEvents.push("수호는 침묵을 막지 못했다. 침묵은 다음 의식을 준비했다.");
      } else if (enemyAction === "contract") {
        turnEvents.push("수호는 계약을 완전히 막지 못했다. 불완전한 진명 진척이 남았다.");
      } else if (enemyAction === "seal") {
        turnEvents.push("수호는 봉인의 문장을 막지 못했다.");
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
    partialTrueNameBefore: partialBefore,
    partialTrueName: partialAfter,
    trueNamePiecesBefore,
    suspicion: state.suspicion,
    suspicionBefore,
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
    probabilityCheck,
    diceCheck,
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
  return `거울 안쪽의 것은 ${getPlayerDisplayName()}의 반복된 의식에 반응하기 시작했다. 같은 선택의 틈을 기억한다.`;
}

function createPrototypeTurnResult(playerAction, { timeout = false, enemyActionKey = null } = {}) {
  const forcedEnemy = enemyActionKey
    ? ENEMY_ACTIONS.find((entry) => entry.key === enemyActionKey)
    : null;
  const enemy = forcedEnemy || pickPrototypeEnemyAction(playerAction, timeout);
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
    publicLog: getCompatibilityPublicLog(playerAction, enemy.key),
    briefing: seal
      ? (seal.success ? "기록이 맞물리고, 피티의 이름이 마침내 진실의 거울 앞에서 완성된다." : "거울 안쪽의 저항이 진명 선언을 찢어 놓았다.")
      : card.briefing,
    delta: seal ? (seal.success ? "진명 선언 성공" : "진명 선언 실패") : card.desc,
    stateChanges: changes,
    patternHint: getPatternHint(playerAction),
    seal
  };
}

function requestTurnResult(playerAction, options = {}) {
  // Swap this prototype provider with the Django turn-result API when backend endpoints are ready.
  state.lastTurnSubmitPayload = buildTurnSubmitPayload(playerAction, options);
  if (typeof window.gamePrototypeBridge?.requestTurnResult === "function") {
    const bridgeResult = window.gamePrototypeBridge.requestTurnResult({
      playerAction,
      turnSubmitPayload: state.lastTurnSubmitPayload,
      options,
      state: {
        turn: state.turn,
        sanity: state.sanity,
        soulfire: state.soulfire,
        curse: state.curse,
        trueNamePieces: state.trueNamePieces,
        selectedInfoTargetKey: state.selectedInfoTargetKey
      }
    });

    if (bridgeResult) return Promise.resolve(bridgeResult);
  }

  return new Promise((resolve) => {
    window.setTimeout(() => {
      resolve(createPrototypeTurnResult(playerAction, options));
    }, 650);
  });
}

function resolveTurnResult(playerAction, options = {}) {
  return requestTurnResult(playerAction, options);
}

function applyTurnStateChanges(changes = {}, result = null) {
  const applied = {};
  if (result?.seal?.success) revealApparitionName();

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
  if (Array.isArray(changes.allowedActions)) {
    state.allowedActions = [...changes.allowedActions];
  }
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
    if (!state.falseClues.some((item) => item.id === clue.id)) state.falseClues.push(clue);
  });
  (changes.revealedFalseClues || []).forEach((clue) => {
    state.suspectClues = state.suspectClues.filter((item) => item.id !== clue.id);
    if (!state.falseClues.some((item) => item.id === clue.id)) state.falseClues.push(clue);
    if (!state.revealedFalseClues.some((item) => item.id === clue.id)) state.revealedFalseClues.push(clue);
  });
  if (changes.tabooViolation) {
    state.tabooEvents.push({ turn: state.turn, target: changes.lastInfoTargetKey });
  }
  state.turnRecords.push({
    turn: state.turn,
    infoTargetKey: changes.lastInfoTargetKey || "",
    tabooViolation: Boolean(changes.tabooViolation),
    journalEntry: resolveJournalTurnEntry(result, changes),
    journalEntrySource: getJournalTurnEntrySource(result, changes),
    practicalSummary: formatJournalPracticalSummary(result, changes),
    changesSummary: formatResourceChangesReadable(changes),
    events: changes.turnEvents || []
  });

  renderAll();
  if (changes.shieldConsumed) pulseGuardWard("break");
  else if (changes.shieldGranted) pulseGuardWard("active");
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
    lines.push(`진명 조각 ${formatTrueNameProgress(changes.trueNamePieces)}`);
  }
  return lines.length ? lines.join(" / ") : "변화 없음";
}

function formatTurnBriefingLegacy(result) {
  const lines = [
    `[행동] 나: ${result.playerLabel} / 괴이: ${result.enemy.label}`,
    `[결과] ${formatResourceChanges(result.stateChanges)}`
  ];

  if (result.seal) {
    lines.push(`[봉인] 방해 ${result.seal.interference}/2 / ${result.seal.success ? "성공" : "실패"}`);
  }

  return lines.join("\n");
}

function formatResourceChangesReadable(changes = {}) {
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
  if (changes.shieldGranted) {
    lines.push("보호막 +1(다음 턴 종료까지)");
  } else if (changes.shieldConsumed) {
    lines.push("보호막 소모");
  }
  if (
    Number.isFinite(changes.partialTrueName)
    && Number.isFinite(changes.partialTrueNameBefore)
    && changes.partialTrueName !== changes.partialTrueNameBefore
  ) {
    lines.push(`불완전 진명 ${changes.partialTrueNameBefore}->${changes.partialTrueName}/2`);
  }
  if (
    Number.isFinite(changes.trueNamePieces)
    && Number.isFinite(changes.trueNamePiecesBefore)
    && changes.trueNamePieces !== changes.trueNamePiecesBefore
  ) {
    lines.push(`진명 조각 ${changes.trueNamePiecesBefore}->${formatTrueNameProgress(changes.trueNamePieces)}`);
  }
  if (Array.isArray(changes.suspectClues) && changes.suspectClues.length) {
    lines.push(`거짓 단서 +${changes.suspectClues.length}`);
  }
  if (Array.isArray(changes.revealedFalseClues) && changes.revealedFalseClues.length) {
    lines.push(`거짓 단서 제거 ${changes.revealedFalseClues.length}`);
  }
  if (
    Number.isFinite(changes.suspicion)
    && Number.isFinite(changes.suspicionBefore)
    && changes.suspicion !== changes.suspicionBefore
  ) {
    lines.push(`의심 ${changes.suspicionBefore}->${changes.suspicion}/3`);
  }
  if (changes.probabilityCheck?.type === "insight_deceive") {
    const check = changes.probabilityCheck;
    lines.push(`간파 판정 ${check.roll}/${check.successRate}% ${check.success ? "성공" : "실패"}`);
  }
  if (changes.diceCheck?.type === "curse_clash") {
    const check = changes.diceCheck;
    const winner = check.winner === "tie" ? "동률" : (check.winner === "player" ? `${getPlayerDisplayName()} 우세` : `${getApparitionDisplayName()} 우세`);
    lines.push(`저주 주사위 ${check.playerRoll}:${check.enemyRoll} ${winner}`);
  }
  return lines.length ? lines.join(" / ") : "변화 없음";
}

function getActionDisplayName(actionKey, fallback = "알 수 없음") {
  return ACTION_CARDS[actionKey]?.title || fallback;
}

function formatJournalPracticalSummary(result = {}, changes = {}) {
  const playerAction = result?.playerAction || "";
  const enemyAction = result?.enemy?.key || "";
  const parts = [
    `행동: ${getPlayerDisplayName()} ${getActionDisplayName(playerAction, result?.playerLabel || "알 수 없음")}, ${getApparitionDisplayName()} ${getActionDisplayName(enemyAction, result?.enemy?.label || "알 수 없음")}`
  ];

  if (changes.lastInfoTargetKey) {
    parts.push(`대상: ${getInfoTargetLabel(changes.lastInfoTargetKey)}`);
  }

  const changeText = formatResourceChangesReadable(changes);
  if (changeText !== "변화 없음") {
    parts.push(`변화: ${changeText}`);
  }

  if (Array.isArray(changes.nextEnemyCandidates) && changes.nextEnemyCandidates.length) {
    parts.push(`다음 후보: ${changes.nextEnemyCandidates.map((key) => getActionDisplayName(key, key)).join("/")}`);
  }

  if (changes.sanity?.after <= 4) {
    parts.push(`위험: 이성 ${changes.sanity.after}/${GAME_RULES.maxSanity}`);
  }

  if (changes.curse?.after >= 4) {
    parts.push(`위험: 저주 ${changes.curse.after}/${GAME_RULES.maxCurseTrace}`);
  }

  if (changes.shieldGranted) {
    parts.push("수호: 다음 저주 피해 2 차단");
  } else if (changes.shieldConsumed) {
    parts.push("수호: 보호막 소모");
  }

  if (changes.trueNamePieces > changes.trueNamePiecesBefore) {
    parts.push(`봉인 준비: 진명 ${formatTrueNameProgress(changes.trueNamePieces)}`);
  }

  return parts.join(" · ");
}

function formatDefaultJournalTurnEntry(result = {}, changes = {}) {
  const playerAction = getActionDisplayName(result?.playerAction, result?.playerLabel || "알 수 없는 행동");
  const enemyAction = getActionDisplayName(result?.enemy?.key, result?.enemy?.label || "알 수 없는 반응");
  const target = changes.lastInfoTargetKey ? ` ${getInfoTargetLabel(changes.lastInfoTargetKey)}을 다시 표시해 두었다.` : "";
  const changeText = formatResourceChangesReadable(changes);
  const changeSentence = changeText === "변화 없음"
    ? "겉으로 드러난 변화는 없었지만, 다음 선택을 위해 이 조합을 남긴다."
    : `${changeText}로 기록한다.`;
  const hint = Array.isArray(changes.nextEnemyCandidates) && changes.nextEnemyCandidates.length
    ? ` 다음 괴이의 징후는 ${changes.nextEnemyCandidates.map((key) => getActionDisplayName(key, key)).join(" 또는 ")} 쪽으로 좁혀졌다.`
    : "";

  return `나는 ${playerAction}을 선택했고, 거울 안쪽은 ${enemyAction}로 응했다.${target} ${changeSentence}${hint}`;
}

function resolveJournalTurnEntry(result = {}, changes = {}) {
  const fallback = formatDefaultJournalTurnEntry(result, changes);
  return resolveLlmDisplayText("journal_turn_entry", null, fallback).text || fallback;
}

function getJournalTurnEntrySource(result = {}, changes = {}) {
  const fallback = formatDefaultJournalTurnEntry(result, changes);
  return resolveLlmDisplayText("journal_turn_entry", null, fallback).source;
}

function formatTurnBriefingReadable(result, applied) {
  const sanity = applied?.sanity;
  const enemyActionName = ACTION_CARDS[result.enemy?.key]?.title || result.enemy?.key || "알 수 없음";
  if (result.publicLog) {
    const lines = [
      `${getPlayerDisplayName()}: ${result.playerLabel}, ${getApparitionDisplayName()}: ${enemyActionName}`,
      result.publicLog
    ];
    const resourceChanges = formatResourceChangesReadable(result.stateChanges);
    lines.push(`[변화] ${resourceChanges}`);
    if (result.seal) {
      lines.push(`[봉인] 방해 단계 ${result.seal.interference}/2 - ${result.seal.success ? "성공" : "실패"}`);
    }
    return lines.join("\n");
  }

  const lines = [
    `[공개] 나: ${result.playerLabel} / 괴이: ${result.enemy.label}`,
    `[판정] ${result.briefing}`,
    sanity
      ? `[상태] 이성 ${sanity.before}/${sanity.max} -> ${sanity.after}/${sanity.max} (${sanity.delta > 0 ? "+" : ""}${sanity.delta})`
      : "[상태] 이성 변화 없음",
    `[변화] ${formatResourceChangesReadable(result.stateChanges)}`
  ];

  if (result.seal) {
    lines.push(`[봉인] 방해 단계 ${result.seal.interference}/2 - ${result.seal.success ? "성공" : "실패"}`);
  }
  if (result.stateChanges?.shieldGranted) {
    lines.push("[수호] 보호막이 형성됐다. 다음 저주 피해 2를 막는다.");
  }
  if (result.stateChanges?.shieldConsumed) {
    lines.push("[수호] 보호막이 저주 피해를 막고 흩어졌다.");
  }
  (result.stateChanges?.turnEvents || []).forEach((event) => {
    lines.push(`[기록] ${event}`);
  });
  if (result.patternHint) {
    lines.push(`[징후] ${result.patternHint}`);
  }

  return lines.join("\n");
}

function endGameIfNeeded(result) {
  if (result?.seal?.success) {
    setTurnState("\uBD09\uC778 \uC131\uACF5");
    stopClock();
    return true;
  }

  if (state.sanity <= 0) {
    setTurnState("\uC774\uC131 \uBD95\uAD34");
    dom.frame?.classList.add("is-sanity-collapse");
    scheduleDefeatJumpscare(3000);
    stopClock();
    return true;
  }

  const curseDefeat = result?.stateChanges?.defeatFlags?.contractFailedAtMaxCurse
    || result?.stateChanges?.defeatFlags?.hitByCurseAtMaxCurse;

  if (curseDefeat) {
    setTurnState("\uC800\uC8FC \uC7A0\uC2DD");
    stopClock();
    return true;
  }

  if (state.turn >= GAME_RULES.maxTurn) {
    setTurnState("12\uD134 \uC885\uB8CC");
    stopClock();
    return true;
  }

  return false;
}

async function runTurnSequence(actionKey, options = {}) {
  if (state.phase === "intro" && !options.ignoreIntro) return;

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
  if (actionKey === "seal") playSealReleaseEffect();
  showPlayerLog(options.timeout ? "시간이 다했다. 검은 초가 먼저 침묵을 선언한다." : card.playerLine, { allowCorruption: !options.timeout });

  await waitForAdvance();
  hidePlayerLog();

  setProgressOverlay("결과 처리 중...", "서버 판정을 기다리고 있습니다.");
  scheduleServerWaitHint();

  let result;
  try {
    result = await resolveTurnResult(actionKey, options);
  } catch (error) {
    console.error("Failed to resolve turn result.", error);
    clearProgressOverlay();
    state.phase = "ready";
    state.isSubmitting = false;
    showPlayerLog(
      "서버 응답을 처리하지 못했습니다. 최신 상태를 확인한 뒤 다시 시도해 주세요.",
      { allowCorruption: false, channel: "system" }
    );
    await waitForAdvance();
    hidePlayerLog();
    renderAll();
    resetClock();
    setTurnState("");
    return;
  }

  clearProgressOverlay();
  if (Array.isArray(result.llm_ui_texts)) applyLlmUiTexts(result.llm_ui_texts);
  if (Array.isArray(result.llmUiTexts)) applyLlmUiTexts(result.llmUiTexts);
  const applied = applyTurnStateChanges(result.stateChanges, result);
  state.lastEnemyAction = result.enemy.key;
  playRitualEffect(result.enemy.key, "enemy");
  showEnemyVoice(result.enemy);

  await waitForAdvance();
  hideEnemyVoice();
  hideSealInterference();

  showPlayerLog(formatTurnBriefingReadable(result, applied), { allowCorruption: false, channel: "system" });
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
  recoverSoulfireForNextTurn();
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
  if (state.phase !== "ready" || state.timerId || state.remainingSeconds <= 0 || document.hidden) return;
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
  if (state.phase === "intro" && isOpen) return;

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
    addPrototypeEvent(tool, "click", () => {
      if (!tool.classList.contains("is-locked")) openActionCard(action, tool);
    });
    addPrototypeEvent(tool, "keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        if (!tool.classList.contains("is-locked")) openActionCard(action, tool);
      }
    });
  });

  addPrototypeEvent(dom.sealInvocation, "click", () => {
    if (state.trueNamePieces >= getRequiredTrueNamePieces()) {
      openActionCard("seal", dom.sealInvocation);
    }
  });

  addPrototypeEvent(dom.actionCard?.querySelector("[data-card-cancel]"), "click", hideActionCard);
  addPrototypeEvent(dom.actionCard?.querySelector("[data-card-use]"), "click", () => {
    if (state.selectedAction) runTurnSequence(state.selectedAction);
  });

  addPrototypeEvent(dom.dialogueArchiveToggle, "click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    setDialogueArchiveOpen(dom.dialogueArchivePanel?.hidden);
  });

  addPrototypeEvent(dom.dialogueArchiveClose, "click", (event) => {
    event.preventDefault();
    setDialogueArchiveOpen(false);
  });

  addPrototypeEvent(dom.dialogueArchivePanel, "click", (event) => {
    event.stopPropagation();
  });

  addPrototypeEvent(dom.playerLog, "click", (event) => {
    event.preventDefault();
    advanceLogSequence();
  });

  addPrototypeEvent(dom.frame, "click", (event) => {
    if (advanceAmbientDialogue()) {
      event.preventDefault();
      event.stopPropagation();
      return;
    }
    if (!state.resultAwaitingAdvance && !state.advanceResolver && !isLogVisible()) return;
    event.preventDefault();
    event.stopPropagation();
    advanceLogSequence();
  }, true);

  addPrototypeEvent(window, "keydown", (event) => {
    if ((event.key === "Enter" || event.key === " ") && advanceAmbientDialogue()) {
      event.preventDefault();
      return;
    }
    if (event.key === "Enter" && (state.resultAwaitingAdvance || state.advanceResolver || isLogVisible())) {
      event.preventDefault();
      advanceLogSequence();
    }
    if (event.key === "Escape") {
      hideActionCard();
      setJournalOpen(false);
    }
  });
  addPrototypeEvent(document, "visibilitychange", handleVisibilityChange);

  addPrototypeEvent(dom.journalToggle, "click", () => setJournalOpen(dom.journalPanel?.hidden));
  addPrototypeEvent(dom.journalClose, "click", () => setJournalOpen(false));
  addPrototypeEvent(dom.journalPanel, "click", (event) => {
    if (event.target === dom.journalPanel) setJournalOpen(false);
  });
  addPrototypeEvent(dom.journalBook, "click", (event) => {
    event.stopPropagation();
  });
}

function resetDemoGame() {
  clearAmbientDialogueTimer();
  clearProgressOverlay();
  hideInteractionCue();
  Object.assign(state, {
    turn: 1,
    apparitionDisplayName: MASKED_APPARITION_DISPLAY_NAME,
    isApparitionNameRevealed: false,
    phase: "intro",
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
    llmUiTexts: [],
    ambientDialogueIndex: 0,
    ambientDialogueTimer: null,
    clockPausedByJournal: false,
    clockWasRunningBeforeHidden: false,
    clockRenderCache: {
      angle: "",
      urgent: false,
      expired: false,
      tooltip: ""
    },
    resultShown: false,
    resultAwaitingAdvance: false,
    pendingEnding: null,
    isSubmitting: false,
    remainingSeconds: GAME_RULES.timerSeconds,
    advanceResolver: null,
    progressHintTimer: null
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
  if (dom.resultScene) {
    dom.resultScene.hidden = true;
    dom.resultScene.classList.remove("is-active");
    dom.resultScene.setAttribute("aria-hidden", "true");
    delete dom.resultScene.dataset.outcome;
  }
  dom.frame?.classList.remove("is-ending", "is-ending-clear", "is-ending-lose", "is-sanity-collapse");
  renderAll();
  resetClock();
  setTurnState("");
  startAmbientDialogue();
}

function testEnding(kind) {
  resetDemoGame();
  clearAmbientDialogueTimer();
  hideAmbientDialogue();
  state.phase = "ready";
  renderIntroLock();
  resetClock();
  const key = String(kind || "").toLowerCase();

  if (key === "clear" || key === "win" || key === "seal") {
    window.gamePrototypeState.setTrueNamePieces(getRequiredTrueNamePieces());
    return runTurnSequence("seal", { enemyActionKey: "guard" });
  }

  if (key === "seal-fail" || key === "sealfail") {
    window.gamePrototypeState.setTrueNamePieces(getRequiredTrueNamePieces());
    return runTurnSequence("seal", { enemyActionKey: "deceive" });
  }

  if (key === "sanity" || key === "jumpscare") {
    window.gamePrototypeState.setSanity(2);
    return runTurnSequence("silence", { enemyActionKey: "curse" });
  }

  if (key === "curse") {
    state.curse = 4;
    state.selectedInfoTargetKey = "truth_mirror";
    renderAll();
    return runTurnSequence("contract", { enemyActionKey: "deceive", ignoreValidation: true });
  }

  if (key === "turns" || key === "timeout" || key === "turn") {
    state.turn = GAME_RULES.maxTurn;
    renderAll();
    return runTurnSequence("silence", { enemyActionKey: "guard" });
  }

  console.warn("Unknown ending test. Use clear, seal-fail, sanity, curse, or turns.");
  return null;
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
    const count = clamp(value, 0, TRUTH_PIECES.length);
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
  setLlmUiTexts(entries) {
    applyLlmUiTexts(entries);
  },
  clearLlmUiTexts() {
    applyLlmUiTexts([]);
  },
  setCurse(value) {
    state.curse = clamp(value, 0, GAME_RULES.maxCurseTrace);
    renderAll();
  },
  setTurn(value) {
    state.turn = clamp(value, 1, GAME_RULES.maxTurn);
    renderAll();
  },
  setInfoTarget(key) {
    state.selectedInfoTargetKey = key || "";
  },
  testEnding,
  applyJournalRecord,
  applyMatchState,
  applyTurnStateChanges,
  buildTurnSubmitPayload,
  runTurnSequence,
  restartIntroDialogue: startAmbientDialogue,
  ensureIntroDialogue: ensureAmbientDialogue,
  advanceIntroDialogue: advanceAmbientDialogue
};

bindEvents();
resetDemoGame();
applyMatchState(window.gamePrototypeBridge?.initialMatchState);
}
