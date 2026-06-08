import { useCallback } from "react";
import { useLocation, useParams } from "react-router-dom";
import { RitualDuelScreen, PrototypeTurnRequest } from "../../features/match/RitualDuelScreen";
import { generateTurnLlmText, submitTurn } from "../../shared/api/resources";
import type { LlmText, MatchState, TurnResult } from "../../shared/types/api";

type MatchRouteState = {
  fromLobbyTransition?: boolean;
  fromPrologueTransition?: boolean;
};

export function MatchRoute() {
  const location = useLocation();
  const { matchId = "prototype-mirror-guest" } = useParams();
  const state = location.state as MatchRouteState | null;
  const turnResultProvider = useCallback(
    async (request: PrototypeTurnRequest) => {
      if (!request.turnSubmitPayload) {
        throw new Error("turnSubmitPayload is required for backend turn submission.");
      }

      const data = await submitTurn(matchId, request.turnSubmitPayload);
      let llmText: LlmText | null = null;
      try {
        const llmResponse = await generateTurnLlmText(
          matchId,
          data.turn_result.turn_id,
          "right_apparition_message",
        );
        llmText = llmResponse.llm_text;
      } catch {
        llmText = null;
      }

      return toPrototypeTurnResult(data.turn_result, data.match, llmText);
    },
    [matchId],
  );

  return (
    <RitualDuelScreen
      matchId={matchId}
      fadeIn={Boolean(state?.fromLobbyTransition || state?.fromPrologueTransition)}
      turnResultProvider={turnResultProvider}
    />
  );
}

function toPrototypeTurnResult(turnResult: TurnResult, match: MatchState, llmText: LlmText | null) {
  const enemyKey = toPrototypeActionKey(turnResult.opponent_action.code);
  const stateChanges = toPrototypeStateChanges(turnResult, match);
  const sealSuccess = turnResult.match_outcome === "player_win";

  return {
    playerLabel: turnResult.player_action.display_name,
    enemy: {
      key: enemyKey,
      label: turnResult.opponent_action.display_name,
      action: `괴이 행동: ${turnResult.opponent_action.display_name}`,
      line: turnResult.public_log.text,
    },
    briefing: turnResult.public_log.text,
    delta: formatStateDelta(turnResult),
    publicLog: turnResult.public_log.text,
    stateChanges,
    patternHint: llmText?.text || "",
    seal: turnResult.player_action.code === "seal"
      ? {
          interference: sealSuccess ? 0 : 2,
          success: sealSuccess,
        }
      : null,
    llm_text: llmText,
    llm_ui_texts: llmText?.enabled && llmText.text ? [llmText] : [],
  };
}

function toPrototypeActionKey(actionCode: string): string {
  return actionCode === "trick" ? "deceive" : actionCode;
}

function toPrototypeStateChanges(turnResult: TurnResult, match: MatchState) {
  const stateDelta = turnResult.state_delta;
  const resources = match.player.resources;

  return {
    sanity: mapResourceDelta(stateDelta.sanity, resources.sanity_max),
    soulfire: mapResourceDelta(stateDelta.ritual_power, resources.ritual_power_max),
    curse: mapResourceDelta(stateDelta.curse_marks, resources.curse_marks_max),
    shield: resources.shield,
    partialTrueName: resources.incomplete_true_name_fragments ?? 0,
    trueNamePieces: resources.true_name_fragments,
    suspicion: resources.suspicion,
    clues: turnResult.clue_delta.added
      .filter((clue) => clue.truth_state === "true_revealed")
      .map(toPrototypeClue),
    suspectClues: turnResult.clue_delta.added
      .filter((clue) => clue.truth_state === "false_revealed")
      .map(toPrototypeClue),
    revealedFalseClues: turnResult.clue_delta.revealed.map(toPrototypeClue),
    turnEvents: [turnResult.public_log.text],
  };
}

function mapResourceDelta(value: unknown, max: number) {
  if (!isDelta(value)) return undefined;
  return {
    before: value.before,
    after: value.after,
    delta: value.delta,
    max,
  };
}

function isDelta(value: unknown): value is { before: number; after: number; delta: number } {
  return typeof value === "object"
    && value !== null
    && typeof (value as { before?: unknown }).before === "number"
    && typeof (value as { after?: unknown }).after === "number"
    && typeof (value as { delta?: unknown }).delta === "number";
}

function toPrototypeClue(clue: { clue_id: string; text: string }) {
  return {
    id: clue.clue_id,
    text: clue.text,
    source: clue.clue_id,
  };
}

function formatStateDelta(turnResult: TurnResult): string {
  const entries = Object.entries(turnResult.state_delta);
  if (entries.length === 0) {
    return "상태 변화 없음";
  }

  return entries
    .map(([key, value]) => {
      if (!isDelta(value)) return key;
      const sign = value.delta > 0 ? "+" : "";
      return `${key} ${value.before}->${value.after} (${sign}${value.delta})`;
    })
    .join(" / ");
}
