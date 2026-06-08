import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import styles from "./RitualDuelScreen.module.css";

const PROTOTYPE_ROOT = "/prototype";
const PROTOTYPE_HTML_PATH = `${PROTOTYPE_ROOT}/game-background.html`;
const PROTOTYPE_CSS_ID = "mirror-guest-prototype-style";
const PROTOTYPE_SCRIPT_ID = "mirror-guest-prototype-script";

type PrototypeEndingPayload = Record<string, string | number | boolean | null | undefined>;

export type PrototypeTurnRequest = {
  playerAction: string;
  turnSubmitPayload?: {
    action_code: string;
    info_target_key?: string | null;
    client_nonce: string;
  };
  options: Record<string, unknown>;
  state: {
    turn: number;
    sanity: number;
    soulfire: number;
    curse: number;
    trueNamePieces: number;
    selectedInfoTargetKey: string;
  };
};

type PrototypeLlmTextPayload = {
  llm_text?: {
    enabled: boolean;
    text: string | null;
    display_slot: string | null;
  };
};

export type PrototypeTurnResultProvider = (
  request: PrototypeTurnRequest,
) => Promise<(Record<string, unknown> & PrototypeLlmTextPayload) | unknown> | (Record<string, unknown> & PrototypeLlmTextPayload) | unknown;

type RitualDuelScreenProps = {
  fadeIn?: boolean;
  matchId?: string;
  turnResultProvider?: PrototypeTurnResultProvider;
};

declare global {
  interface Window {
    gamePrototypeBridge?: {
      openEndingScreen?: (payload: PrototypeEndingPayload) => void;
      requestTurnResult?: (request: PrototypeTurnRequest) => Promise<unknown> | unknown;
    };
    gamePrototypeState?: {
      restartIntroDialogue?: () => void;
      ensureIntroDialogue?: () => void;
      [key: string]: unknown;
    };
    __mirrorGuestPrototypeActiveRunId?: string;
    __mirrorGuestPrototypeCleanup?: () => void;
  }
}

function rewritePrototypeAssetPaths(markup: string) {
  return markup
    .replaceAll('src="assets/', `src="${PROTOTYPE_ROOT}/assets/`)
    .replaceAll("src='assets/", `src='${PROTOTYPE_ROOT}/assets/`)
    .replaceAll('href="assets/', `href="${PROTOTYPE_ROOT}/assets/`)
    .replaceAll("href='assets/", `href='${PROTOTYPE_ROOT}/assets/`);
}

function ensurePrototypeStylesheet() {
  if (document.getElementById(PROTOTYPE_CSS_ID)) return;

  const link = document.createElement("link");
  link.id = PROTOTYPE_CSS_ID;
  link.rel = "stylesheet";
  link.href = `${PROTOTYPE_ROOT}/game-background.css`;
  document.head.appendChild(link);
}

function loadPrototypeScript(runId: string) {
  return new Promise<void>((resolve, reject) => {
    document.getElementById(PROTOTYPE_SCRIPT_ID)?.remove();

    const script = document.createElement("script");
    script.id = PROTOTYPE_SCRIPT_ID;
    script.src = `${PROTOTYPE_ROOT}/game-background.js`;
    script.async = false;
    script.dataset.prototypeRunId = runId;
    window.__mirrorGuestPrototypeActiveRunId = runId;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("게임 스크립트를 불러오지 못했습니다."));
    document.body.appendChild(script);
  });
}

export function RitualDuelScreen({
  fadeIn = false,
  matchId = "prototype-mirror-guest",
  turnResultProvider,
}: RitualDuelScreenProps) {
  const navigate = useNavigate();
  const hostRef = useRef<HTMLDivElement>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const openEndingScreen = useCallback(
    (payload: PrototypeEndingPayload) => {
      const searchParams = new URLSearchParams();

      Object.entries(payload).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.set(key, String(value));
        }
      });

      navigate(`/matches/${matchId}/result?${searchParams.toString()}`);
    },
    [matchId, navigate],
  );

  useEffect(() => {
    let cancelled = false;
    const runId = `${Date.now()}-${Math.random().toString(36).slice(2)}`;

    async function mountPrototype() {
      try {
        setLoadError(null);
        window.__mirrorGuestPrototypeCleanup?.();
        window.gamePrototypeBridge = {
          openEndingScreen,
          requestTurnResult: turnResultProvider,
        };

        ensurePrototypeStylesheet();

        const response = await fetch(PROTOTYPE_HTML_PATH);
        if (!response.ok) {
          throw new Error(`게임 화면 HTML을 불러오지 못했습니다. (${response.status})`);
        }

        const html = await response.text();
        const documentFragment = new DOMParser().parseFromString(html, "text/html");
        const host = hostRef.current;
        if (!host || cancelled) return;

        host.innerHTML = rewritePrototypeAssetPaths(documentFragment.body.innerHTML);
        await loadPrototypeScript(runId);
        if (cancelled || window.__mirrorGuestPrototypeActiveRunId !== runId) return;

        window.requestAnimationFrame(() => {
          if (!cancelled && window.__mirrorGuestPrototypeActiveRunId === runId) {
            window.gamePrototypeState?.restartIntroDialogue?.();
          }
        });

        window.setTimeout(() => {
          if (!cancelled && window.__mirrorGuestPrototypeActiveRunId === runId) {
            window.gamePrototypeState?.ensureIntroDialogue?.();
          }
        }, 650);
      } catch (error) {
        if (!cancelled) {
          setLoadError(error instanceof Error ? error.message : "게임 화면을 불러오지 못했습니다.");
        }
      }
    }

    mountPrototype();

    return () => {
      cancelled = true;
      window.__mirrorGuestPrototypeCleanup?.();
      delete window.gamePrototypeBridge;
      if (window.__mirrorGuestPrototypeActiveRunId === runId) {
        delete window.__mirrorGuestPrototypeActiveRunId;
      }
      document.getElementById(PROTOTYPE_SCRIPT_ID)?.remove();
      document.getElementById(PROTOTYPE_CSS_ID)?.remove();
      if (hostRef.current) hostRef.current.innerHTML = "";
    };
  }, [openEndingScreen, turnResultProvider]);

  return (
    <main className={`${styles.screen} ${fadeIn ? styles.fadeIn : ""}`} aria-label="거울 속의 손님 게임 화면">
      <div ref={hostRef} className={styles.prototypeHost} />
      <button type="button" className={styles.backButton} onClick={() => navigate("/story-cases")}>
        사건 선택
      </button>
      {loadError ? (
        <section className={styles.loadError} role="alert">
          <strong>의식장을 열 수 없습니다.</strong>
          <p>{loadError}</p>
        </section>
      ) : null}
    </main>
  );
}
