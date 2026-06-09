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

function forbidPattern(name, source, pattern, message) {
  if (pattern.test(source)) {
    console.error(`${name} violates realtime contract: ${message}`);
    process.exit(1);
  }
}

const realtimeSource = read("src/shared/api/realtime.ts");
const realtimeConstantsSource = read("src/shared/constants/realtime.ts");
const matchRouteSource = read("src/routes/match/MatchRoute.tsx");
const viteConfigSource = read("vite.config.ts");
const readProjectFile = (path) => read(`../${path}`);
const realtimeContractSource = readProjectFile("docs/09_Approved_Contracts/29_MVP_Realtime_Redis_WebSocket_계약.md");
const readmeSource = readProjectFile("README.md");

for (const snippet of [
  "export type MatchRealtimeEvent",
  "connectMatchRealtime",
  "buildMatchWebSocketUrl",
  "new WebSocket(",
  "VITE_WEBSOCKET_BASE_URL",
  "window.location.protocol",
  "/api/v1/ws/matches",
  "encodeURIComponent(matchId)",
  "DEFAULT_WEBSOCKET_CONNECT_TIMEOUT_SECONDS",
  "MILLISECONDS_PER_SECOND",
  "setTimeout(",
  "socket.close()",
]) {
  requireSnippet("RealtimeClient", realtimeSource, snippet);
}

for (const snippet of [
  "DEFAULT_WEBSOCKET_CONNECT_TIMEOUT_SECONDS",
  "MILLISECONDS_PER_SECOND",
]) {
  requireSnippet("RealtimeConstants", realtimeConstantsSource, snippet);
}

for (const snippet of [
  "connectMatchRealtime",
  "onEvent",
  "match.snapshot",
  "turn.resolved",
  "llm.text.ready",
  "result.ready",
  "setInitialMatchState",
  "getMatchDetail(matchId)",
]) {
  requireSnippet("MatchRoute", matchRouteSource, snippet);
}

for (const snippet of [
  "VITE_WEBSOCKET_BASE_URL",
  "VITE_WEBSOCKET_CONNECT_TIMEOUT_SECONDS",
]) {
  requireSnippet("RealtimeContractDoc", realtimeContractSource, snippet);
  requireSnippet("README", readmeSource, snippet);
}

for (const snippet of [
  "/api/v1/ws/matches/{match_id}",
]) {
  requireSnippet("RealtimeContractDoc", realtimeContractSource, snippet);
  requireSnippet("README", readmeSource, snippet);
}

for (const snippet of [
  "server:",
  "\"/api\"",
  "\"/healthz\"",
  "\"/api/v1/ws\"",
  "ws: true",
]) {
  requireSnippet("ViteConfig", viteConfigSource, snippet);
}

forbidPattern(
  "RealtimeClient",
  realtimeSource,
  /localStorage\s*\.(setItem|getItem)|sessionStorage\s*\.(setItem|getItem)/,
  "WebSocket client must not store or read tokens from browser storage",
);

forbidPattern(
  "RealtimeClient",
  realtimeSource,
  /\b6000\b|\*\s*1000\b/,
  "timeout defaults and unit conversion must use named realtime constants",
);

forbidPattern(
  "MatchRoute",
  matchRouteSource,
  /localStorage\s*\.(setItem|getItem)|sessionStorage\s*\.(setItem|getItem)/,
  "Match route must not store or read tokens from browser storage",
);
