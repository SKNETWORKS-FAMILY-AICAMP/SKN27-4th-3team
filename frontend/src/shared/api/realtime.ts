import type { LlmText, MatchState, TurnResult } from "../types/api";
import {
  DEFAULT_WEBSOCKET_CONNECT_TIMEOUT_SECONDS,
  MILLISECONDS_PER_SECOND,
} from "../constants/realtime";

const WEBSOCKET_BASE_URL = import.meta.env.VITE_WEBSOCKET_BASE_URL ?? "";
const WEBSOCKET_CONNECT_TIMEOUT_SECONDS = Number(
  import.meta.env.VITE_WEBSOCKET_CONNECT_TIMEOUT_SECONDS
    ?? String(DEFAULT_WEBSOCKET_CONNECT_TIMEOUT_SECONDS),
);
const MATCH_WEBSOCKET_PATH_PREFIX = "/api/v1/ws/matches";

export type MatchRealtimeEvent =
  | {
      type: "match.snapshot";
      match: MatchState;
    }
  | {
      type: "turn.resolved";
      turn_result: TurnResult;
      match: MatchState;
    }
  | {
      type: "llm.text.ready";
      match_id: string;
      turn_id: string;
      llm_text: LlmText;
    }
  | {
      type: "result.ready";
      match: MatchState;
    }
  | {
      type: "heartbeat";
    }
  | {
      type: "error";
      error: {
        code: string;
        message: string;
      };
    };

type MatchRealtimeOptions = {
  onEvent: (event: MatchRealtimeEvent) => void;
  onError?: (error: Event | Error) => void;
  connectTimeoutMs?: number;
};

type MatchRealtimeConnection = {
  close: () => void;
};

export function buildMatchWebSocketUrl(matchId: string): string {
  const encodedMatchId = encodeURIComponent(matchId);
  const configuredBaseUrl = WEBSOCKET_BASE_URL.trim();
  if (configuredBaseUrl) {
    return `${trimTrailingSlash(configuredBaseUrl)}${MATCH_WEBSOCKET_PATH_PREFIX}/${encodedMatchId}`;
  }

  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}${MATCH_WEBSOCKET_PATH_PREFIX}/${encodedMatchId}`;
}

export function connectMatchRealtime(
  matchId: string,
  options: MatchRealtimeOptions,
): MatchRealtimeConnection {
  const socket = new WebSocket(buildMatchWebSocketUrl(matchId));
  const connectTimeoutMs = options.connectTimeoutMs ?? normalizedConnectTimeoutMs();
  let closedByClient = false;
  const timeoutId = window.setTimeout(() => {
    if (socket.readyState === WebSocket.CONNECTING) {
      socket.close();
      options.onError?.(new Error("WEBSOCKET_CONNECT_TIMEOUT"));
    }
  }, connectTimeoutMs);

  socket.addEventListener("open", () => {
    window.clearTimeout(timeoutId);
  });

  socket.addEventListener("message", (event) => {
    const parsedEvent = parseRealtimeEvent(event.data);
    if (parsedEvent) {
      options.onEvent(parsedEvent);
    }
  });

  socket.addEventListener("error", (event) => {
    if (!closedByClient) options.onError?.(event);
  });

  socket.addEventListener("close", () => {
    window.clearTimeout(timeoutId);
  });

  return {
    close() {
      closedByClient = true;
      window.clearTimeout(timeoutId);
      socket.close();
    },
  };
}

function parseRealtimeEvent(value: unknown): MatchRealtimeEvent | null {
  if (typeof value !== "string") return null;

  try {
    const parsed = JSON.parse(value) as MatchRealtimeEvent;
    if (!isKnownRealtimeEvent(parsed)) return null;
    return parsed;
  } catch {
    return null;
  }
}

function isKnownRealtimeEvent(value: unknown): value is MatchRealtimeEvent {
  if (typeof value !== "object" || value === null) return false;
  const eventType = (value as { type?: unknown }).type;
  return eventType === "match.snapshot"
    || eventType === "turn.resolved"
    || eventType === "llm.text.ready"
    || eventType === "result.ready"
    || eventType === "heartbeat"
    || eventType === "error";
}

function normalizedConnectTimeoutMs(): number {
  if (!Number.isFinite(WEBSOCKET_CONNECT_TIMEOUT_SECONDS) || WEBSOCKET_CONNECT_TIMEOUT_SECONDS <= 0) {
    return DEFAULT_WEBSOCKET_CONNECT_TIMEOUT_SECONDS * MILLISECONDS_PER_SECOND;
  }
  return WEBSOCKET_CONNECT_TIMEOUT_SECONDS * MILLISECONDS_PER_SECOND;
}

function trimTrailingSlash(value: string): string {
  return value.endsWith("/") ? value.slice(0, -1) : value;
}
