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

const authScreenSource = readFileSync(resolve("src/features/auth/AuthScreen.tsx"), "utf8");
for (const snippet of ["login(", "signup(", "ApiClientError", "navigate(\"/lobby\")"]) {
  if (!authScreenSource.includes(snippet)) {
    console.error(`AuthScreen missing API snippet: ${snippet}`);
    process.exit(1);
  }
}
