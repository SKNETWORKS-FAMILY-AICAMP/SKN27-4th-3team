import { CSSProperties, MouseEvent, useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ApiClientError } from "../../shared/api/client";
import { startStoryMatch } from "../../shared/api/resources";
import styles from "./PrologueScreen.module.css";
import { prologueScenes } from "./prologueScenes";

const DETAIL_REVEAL_DELAY_MS = 260;
const NEXT_SCENE_FADE_MS = 880;
const MATCH_FADE_MS = 1850;
const DEFAULT_CASE_ID = "nameless_curse";

type PrologueRouteState = {
  caseId?: string;
};

function getTypingDelay(previousCharacter: string) {
  if (previousCharacter === "\n") {
    return 120;
  }

  if (/[.!?…。？！,，]/.test(previousCharacter)) {
    return 82;
  }

  return 24;
}

export function PrologueScreen() {
  const navigate = useNavigate();
  const location = useLocation();
  const routeState = location.state as PrologueRouteState | null;
  const caseId = routeState?.caseId || DEFAULT_CASE_ID;
  const transitionTimerRef = useRef<number | null>(null);
  const [sceneIndex, setSceneIndex] = useState(0);
  const [visibleCharacters, setVisibleCharacters] = useState(0);
  const [isDetailVisible, setIsDetailVisible] = useState(false);
  const [isLeaving, setIsLeaving] = useState(false);
  const [isStartingMatch, setIsStartingMatch] = useState(false);
  const [startError, setStartError] = useState("");

  const scene = prologueScenes[sceneIndex];
  const isFinalScene = sceneIndex === prologueScenes.length - 1;
  const isMainComplete = visibleCharacters >= scene.main.length;
  const isSceneComplete = isMainComplete && isDetailVisible;
  const visibleMain = scene.main.slice(0, visibleCharacters);

  useEffect(() => {
    return () => {
      if (transitionTimerRef.current !== null) {
        window.clearTimeout(transitionTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    setVisibleCharacters(0);
    setIsDetailVisible(false);
    setIsLeaving(false);
  }, [sceneIndex]);

  useEffect(() => {
    if (isLeaving) {
      return;
    }

    if (!isMainComplete) {
      const previousCharacter = visibleCharacters > 0 ? scene.main[visibleCharacters - 1] : "";
      const delay = visibleCharacters === 0 ? 360 : getTypingDelay(previousCharacter);
      const typingTimer = window.setTimeout(() => {
        setVisibleCharacters((current) => Math.min(current + 1, scene.main.length));
      }, delay);

      return () => window.clearTimeout(typingTimer);
    }

    if (!isDetailVisible) {
      const detailTimer = window.setTimeout(() => {
        setIsDetailVisible(true);
      }, DETAIL_REVEAL_DELAY_MS);

      return () => window.clearTimeout(detailTimer);
    }

    return undefined;
  }, [isDetailVisible, isLeaving, isMainComplete, scene.main, visibleCharacters]);

  const startMatchAndNavigate = useCallback(async () => {
    setIsStartingMatch(true);
    setStartError("");

    try {
      const data = await startStoryMatch(caseId, {
        client_request_id: createClientRequestId(),
        player_display_name: null,
      });
      navigate(`/matches/${data.match.match_id}`, { state: { fromPrologueTransition: true } });
    } catch (error) {
      setIsLeaving(false);
      setStartError(formatStartMatchError(error));
    } finally {
      setIsStartingMatch(false);
    }
  }, [caseId, navigate]);

  const advanceScene = useCallback(() => {
    if (isLeaving || isStartingMatch) {
      return;
    }

    if (!isSceneComplete) {
      setVisibleCharacters(scene.main.length);
      setIsDetailVisible(true);
      return;
    }

    setIsLeaving(true);
    transitionTimerRef.current = window.setTimeout(() => {
      if (isFinalScene) {
        void startMatchAndNavigate();
        return;
      }

      setVisibleCharacters(0);
      setIsDetailVisible(false);
      setIsLeaving(false);
      setSceneIndex((current) => Math.min(current + 1, prologueScenes.length - 1));
    }, isFinalScene ? MATCH_FADE_MS : NEXT_SCENE_FADE_MS);
  }, [isFinalScene, isLeaving, isSceneComplete, isStartingMatch, scene.main.length, startMatchAndNavigate]);

  const skipPrologue = useCallback((event: MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    if (isLeaving || isStartingMatch) {
      return;
    }

    if (transitionTimerRef.current !== null) {
      window.clearTimeout(transitionTimerRef.current);
    }

    setIsLeaving(true);
    transitionTimerRef.current = window.setTimeout(() => {
      void startMatchAndNavigate();
    }, 720);
  }, [isLeaving, isStartingMatch, startMatchAndNavigate]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Enter" && event.key !== " ") {
        return;
      }

      event.preventDefault();
      advanceScene();
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [advanceScene]);

  const sceneStyle = {
    "--scene-image": `url("${scene.image}")`,
    "--scene-focus": scene.focus,
  } as CSSProperties;

  return (
    <main
      className={`${styles.screen} ${isLeaving ? styles.isLeaving : ""} ${
        isFinalScene && isLeaving ? styles.toMatch : ""
      }`}
      style={sceneStyle}
      onClick={advanceScene}
      aria-label="프롤로그"
    >
      <div className={styles.sceneImage} aria-hidden="true" />
      <div className={styles.vignette} aria-hidden="true" />
      <div className={styles.noise} aria-hidden="true" />

      <button className={styles.skipButton} type="button" onClick={skipPrologue}>
        {isStartingMatch ? "사건 준비 중" : "전체 건너뛰기"}
      </button>

      <section className={styles.textPanel} aria-live="polite">
        <p className={styles.mainText}>{visibleMain}</p>
        <p className={`${styles.detailText} ${isDetailVisible ? styles.isVisible : ""}`}>
          {startError || scene.detail}
        </p>
      </section>

      <div className={`${styles.continueMark} ${isSceneComplete ? styles.isVisible : ""}`} aria-hidden="true" />
    </main>
  );
}

function createClientRequestId(): string {
  if (window.crypto?.randomUUID) {
    return window.crypto.randomUUID();
  }

  return `story-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function formatStartMatchError(error: unknown): string {
  if (error instanceof ApiClientError) {
    if (error.code === "AUTH_REQUIRED" || error.code === "SESSION_EXPIRED") {
      return "로그인 후 사건을 시작할 수 있습니다.";
    }
    return error.message || error.code;
  }

  return "사건을 시작하지 못했습니다.";
}
