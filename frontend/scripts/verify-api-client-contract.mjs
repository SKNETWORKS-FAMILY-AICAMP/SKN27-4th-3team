import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const clientSource = readFileSync(resolve("src/shared/api/client.ts"), "utf8");
const resourceSource = readFileSync(resolve("src/shared/api/resources.ts"), "utf8");

const requiredClientSnippets = [
  'credentials: "include"',
  "let csrfToken: string | null = null",
  '"X-CSRFToken"',
  "/api/v1/auth/csrf",
  "localStorage",
  "sessionStorage",
];

const missing = requiredClientSnippets.filter((snippet) => !clientSource.includes(snippet));
if (missing.length > 0) {
  console.error("API client contract missing snippets:");
  for (const snippet of missing) console.error(`- ${snippet}`);
  process.exit(1);
}

if (/localStorage\s*\.(setItem|getItem)|sessionStorage\s*\.(setItem|getItem)/.test(clientSource + resourceSource)) {
  console.error("Token storage in localStorage/sessionStorage is forbidden.");
  process.exit(1);
}

const requiredResourceSnippets = [
  "login(",
  "signup(",
  "logout(",
  "getCurrentSession(",
  "listStoryCases(",
  "startStoryMatch(",
  "submitTurn(",
  "generateTurnLlmText(",
  "getMatchResult(",
  "getProfileMe(",
];

const missingResources = requiredResourceSnippets.filter((snippet) => !resourceSource.includes(snippet));
if (missingResources.length > 0) {
  console.error("API resources missing wrappers:");
  for (const snippet of missingResources) console.error(`- ${snippet}`);
  process.exit(1);
}

const loginFunctionMatch = resourceSource.match(/export async function login[\s\S]*?\n}\n/);
if (!loginFunctionMatch || !loginFunctionMatch[0].includes("clearCsrfTokenForNewSession();")) {
  console.error("login must clear cached CSRF token after Django rotates CSRF on successful login.");
  process.exit(1);
}

const authScreenSource = readFileSync(resolve("src/features/auth/AuthScreen.tsx"), "utf8");
for (const snippet of ["login(", "signup(", "ApiClientError", "navigate(\"/lobby\")", "formatFieldErrors(", "error.details"]) {
  if (!authScreenSource.includes(snippet)) {
    console.error(`AuthScreen missing API snippet: ${snippet}`);
    process.exit(1);
  }
}

const storySource = readFileSync(resolve("src/features/story/StoryCasesScreen.tsx"), "utf8");
const prologueSource = readFileSync(resolve("src/features/prologue/PrologueScreen.tsx"), "utf8");
const matchRouteSource = readFileSync(resolve("src/routes/match/MatchRoute.tsx"), "utf8");
const duelSource = readFileSync(resolve("src/features/match/RitualDuelScreen.tsx"), "utf8");

for (const [name, source, snippets] of [
  ["StoryCasesScreen", storySource, ["listStoryCases(", "navigate(\"/prologue\""]],
  ["PrologueScreen", prologueSource, ["startStoryMatch(", "client_request_id", "crypto.randomUUID"]],
  ["MatchRoute", matchRouteSource, ["submitTurn(", "generateTurnLlmText(", "ApiClientError", "getMatchDetail(", "TURN_DEADLINE_EXPIRED"]],
  ["RitualDuelScreen", duelSource, ["turnSubmitPayload", "llm_text"]],
]) {
  for (const snippet of snippets) {
    if (!source.includes(snippet)) {
      console.error(`${name} missing API snippet: ${snippet}`);
      process.exit(1);
    }
  }
}

const resultSource = readFileSync(resolve("src/features/result/ResultScreen.tsx"), "utf8");
const profileSource = readFileSync(resolve("src/features/profile/ProfileSummaryScreen.tsx"), "utf8");

for (const [name, source, snippets] of [
  ["ResultScreen", resultSource, ["getMatchResult(", "llm_summary", "story_result_text"]],
  ["ProfileSummaryScreen", profileSource, ["getProfileMe(", "style_summary", "public_record"]],
]) {
  for (const snippet of snippets) {
    if (!source.includes(snippet)) {
      console.error(`${name} missing API snippet: ${snippet}`);
      process.exit(1);
    }
  }
}
