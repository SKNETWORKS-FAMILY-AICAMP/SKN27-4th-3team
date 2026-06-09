import { readFileSync } from "node:fs";
import { resolve } from "node:path";

function read(path) {
  return readFileSync(resolve(path), "utf8");
}

function requireSnippet(name, source, snippet) {
  if (!source.includes(snippet)) {
    console.error(`${name} missing required snippet: ${snippet}`);
    process.exit(1);
  }
}

function forbidSnippet(name, source, snippet) {
  if (source.includes(snippet)) {
    console.error(`${name} contains forbidden snippet: ${snippet}`);
    process.exit(1);
  }
}

const prototypeHtml = read("public/prototype/game-background.html");
const prototypeCss = read("public/prototype/game-background.css");
const prototypeScript = read("public/prototype/game-background.js");
const matchRoute = read("src/routes/match/MatchRoute.tsx");
const duelScreen = read("src/features/match/RitualDuelScreen.tsx");
const resultScreen = read("src/features/result/ResultScreen.tsx");
const storyCasesScreen = read("src/features/story/StoryCasesScreen.tsx");
const prologueScreen = read("src/features/prologue/PrologueScreen.tsx");

for (const [name, source] of [
  ["PrototypeHtml", prototypeHtml],
  ["PrototypeScript", prototypeScript],
  ["ResultScreen", resultScreen],
]) {
  forbidSnippet(name, source, "이안");
}

forbidSnippet("PrototypeScript", prototypeScript, 'pushDialogueLog("spirit", "???"');
forbidSnippet("PrototypeScript", prototypeScript, "??:");
forbidSnippet("PrototypeScript", prototypeScript, 'DEFAULT_APPARITION_DISPLAY_NAME = "피티"');
forbidSnippet("PrototypeHtml", prototypeHtml, "피티");
forbidSnippet("StoryCasesScreen", storyCasesScreen, "피티");
forbidSnippet("ResultScreen", resultScreen, "피티");
forbidSnippet("PrototypeScript", prototypeScript, "sealRequiredTrueNamePieces: 3");
forbidSnippet("PrototypeScript", prototypeScript, "진명 ${state.trueNamePieces}/3");
forbidSnippet("PrototypeScript", prototypeScript, "현재 ${state.trueNamePieces}/3");
forbidSnippet("PrototypeScript", prototypeScript, "진명 조각 ${changes.trueNamePieces}/3");
forbidSnippet("PrototypeScript", prototypeScript, "진명 조각 ${changes.trueNamePiecesBefore}->${changes.trueNamePieces}/3");
forbidSnippet("PrototypeHtml", prototypeHtml, "진명 3/3");
forbidSnippet("PrototypeHtml", prototypeHtml, "진명 조각 3개");
forbidSnippet("PrototypeScript", prototypeScript, 'clearImage: "assets/clear_.png"');
forbidSnippet("PrototypeScript", prototypeScript, 'gameOverImage: "assets/gameover_.png"');

requireSnippet("PrototypeScript", prototypeScript, 'MASKED_APPARITION_DISPLAY_NAME = "거울 속 목소리"');
requireSnippet("PrototypeScript", prototypeScript, "isApparitionNameRevealed");
requireSnippet("PrototypeScript", prototypeScript, "revealApparitionName()");
requireSnippet("PrototypeScript", prototypeScript, "getRequiredTrueNamePieces()");
requireSnippet("PrototypeScript", prototypeScript, "getPlayerDisplayName()");
requireSnippet("PrototypeScript", prototypeScript, "getApparitionDisplayName()");
requireSnippet("PrototypeScript", prototypeScript, "applyMatchState(match)");
requireSnippet("PrototypeHtml", prototypeHtml, "진명 0/2");
requireSnippet("PrototypeScript", prototypeScript, "SEAL_INFO_TARGET_KEY_BY_CASE");
requireSnippet("PrototypeScript", prototypeScript, "getSealInfoTargetKey()");
requireSnippet("PrototypeScript", prototypeScript, 'actionKey === "seal"');
requireSnippet("PrototypeScript", prototypeScript, "RESULT_SCENE.minDisplayMs");
requireSnippet("PrototypeScript", prototypeScript, 'clearImage: "/prototype/assets/clear_.png"');
requireSnippet("PrototypeScript", prototypeScript, 'gameOverImage: "/prototype/assets/gameover_.png"');
requireSnippet("PrototypeScript", prototypeScript, "resultAdvanceAvailableAt");
requireSnippet("PrototypeScript", prototypeScript, "Date.now() < state.resultAdvanceAvailableAt");
requireSnippet("PrototypeCss", prototypeCss, '.result-scene[data-outcome="game-over"].is-active img');
forbidSnippet("PrototypeCss", prototypeCss, 'animation: resultBackdropIn 260ms ease forwards 760ms;');

requireSnippet("MatchRoute", matchRoute, "useEffect");
requireSnippet("MatchRoute", matchRoute, "getMatchDetail(matchId)");
requireSnippet("MatchRoute", matchRoute, "initialMatchState");
requireSnippet("MatchRoute", matchRoute, "allowedActions: toPrototypeAllowedActions(match)");
requireSnippet("MatchRoute", matchRoute, "matchOutcome: turnResult.match_outcome");
requireSnippet("RitualDuelScreen", duelScreen, "initialMatchState");
requireSnippet("RitualDuelScreen", duelScreen, "applyMatchState");
requireSnippet("PrototypeScript", prototypeScript, "if (Array.isArray(changes.allowedActions))");
requireSnippet("PrototypeScript", prototypeScript, "getServerMatchOutcome(result)");
requireSnippet("PrototypeScript", prototypeScript, 'if (outcome === "unresolved") return false;');

requireSnippet("StoryCasesScreen", storyCasesScreen, 'case_id: "nameless_curse"');
requireSnippet("PrologueScreen", prologueScreen, 'DEFAULT_CASE_ID = "nameless_curse"');
