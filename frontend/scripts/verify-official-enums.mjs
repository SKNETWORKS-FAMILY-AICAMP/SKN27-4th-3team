import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const sourcePath = resolve("public/prototype/game-background.js");
const source = readFileSync(sourcePath, "utf8");

const requiredSnippets = [
  'deceive: "trick"',
  'attic_diary: "mirror_back"',
  'truth_mirror: "truth_mirror"',
  'family_journal: "family_journal"',
  'nameless_thread: "nameless_thread"',
  'basement_wall: "basement_wall"',
  'stitched_mouth: "missing_child_voice"',
  'bloodied_teddy: "forgotten_room"',
  'ian_reflection: "self_reflection"',
  "function buildTurnSubmitPayload(",
  "action_code: officialActionCode",
  "payload.info_target_key = officialInfoTargetKey",
  "client_nonce:",
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error("Official API enum boundary is missing required snippets:");
  for (const snippet of missing) {
    console.error(`- ${snippet}`);
  }
  process.exit(1);
}
