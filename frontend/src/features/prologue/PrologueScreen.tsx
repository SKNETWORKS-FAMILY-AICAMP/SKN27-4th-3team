import { CSSProperties, MouseEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { startStoryMatch } from "../../shared/api/resources";
import { BGM_TRACKS, useBackgroundMusic } from "../../shared/audio/audio";
import styles from "./PrologueScreen.module.css";
import { prologueScenes } from "./prologueScenes";

const NEXT_SCENE_FADE_MS = 760;
const MATCH_FADE_MS = 1500;
const BLACKOUT_SCENE_FADE_MS = 3200;
const SKIP_FADE_MS = 620;
const DEFAULT_CASE_ID = "nameless_curse";
const PROTOTYPE_MATCH_ID = "prototype-mirror-guest";

type PrologueRouteState = {
  caseId?: string;
};

type PlaybackPhase = "image" | "typing" | "segmentComplete" | "detail";

function getTypingDelay(previousCharacter: string) {
  if (previousCharacter === "\n") {
    return 70;
  }

  if (/[.!?…。,””]/.test(previousCharacter)) {
    return 52;
  }

  return 15;
}

function getSceneSegments(mainText: string) {
  return mainText
    .split(/\n{2,}/)
    .map((segment) => segment.trim())
    .filter(Boolean);
}

export function PrologueScreen() {
  const navigate = useNavigate();
  const location = useLocation();
  const routeState = location.state as PrologueRouteState | null;
  const caseId = routeState?.caseId || DEFAULT_CASE_ID;
  const transitionTimerRef = useRef<number | null>(null);
  const [sceneIndex, setSceneIndex] = useState(0);
  const [phase, setPhase] = useState<PlaybackPhase>("image");
  const [segmentIndex, setSegmentIndex] = useState(0);
  const [visibleCharacters, setVisibleCharacters] = useState(0);
  const [isLeaving, setIsLeaving] = useState(false);
  const [isStartingMatch, setIsStartingMatch] = useState(false);
  useBackgroundMusic(BGM_TRACKS.prologue, { volume: 0.46 });

  const scene = prologueScenes[sceneIndex];
  const sceneSegments = useMemo(() => getSceneSegments(scene.main), [scene.main]);
  const currentSegment = sceneSegments[segmentIndex] ?? "";
  const isFinalScene = sceneIndex === prologueScenes.length - 1;
  const isFinalSegment = segmentIndex >= sceneSegments.length - 1;
  const isSegmentComplete = visibleCharacters >= currentSegment.length;
  const isBlackoutLeaving = isLeaving && scene.transition === "blackout";
  const isSceneComplete = phase === "detail";
  const isTextVisible = phase !== "image";
  const visibleMain = currentSegment.slice(0, visibleCharacters);

  const clearTransitionTimer = useCallback(() => {
    if (transitionTimerRef.current !== null) {
      window.clearTimeout(transitionTimerRef.current);
      transitionTimerRef.current = null;
    }
  }, []);

  useEffect(() => clearTransitionTimer, [clearTransitionTimer]);

  useEffect(() => {
    clearTransitionTimer();
    setPhase("image");
    setSegmentIndex(0);
    setVisibleCharacters(0);
    setIsLeaving(false);
  }, [clearTransitionTimer, sceneIndex]);

  useEffect(() => {
    if (isLeaving || phase !== "typing") {
      return undefined;
    }

    if (isSegmentComplete) {
      setPhase("segmentComplete");
      return undefined;
    }

    const previousCharacter = visibleCharacters > 0 ? currentSegment[visibleCharacters - 1] : "";
    const delay = visibleCharacters === 0 ? 120 : getTypingDelay(previousCharacter);
    const typingTimer = window.setTimeout(() => {
      setVisibleCharacters((current) => Math.min(current + 1, currentSegment.length));
    }, delay);

    return () => window.clearTimeout(typingTimer);
  }, [currentSegment, isLeaving, isSegmentComplete, phase, visibleCharacters]);

  const navigateToPrototypeMatch = useCallback(() => {
    navigate(`/matches/${PROTOTYPE_MATCH_ID}`, { state: { fromPrologueTransition: true } });
  }, [navigate]);

  const startMatchAndNavigate = useCallback(async () => {
    setIsStartingMatch(true);

    try {
      const data = await startStoryMatch(caseId, {
        client_request_id: createClientRequestId(),
        player_display_name: null,
      });
      navigate(`/matches/${data.match.match_id}`, { state: { fromPrologueTransition: true } });
    } catch {
      navigateToPrototypeMatch();
    } finally {
      setIsStartingMatch(false);
    }
  }, [caseId, navigate, navigateToPrototypeMatch]);

  const leaveCurrentScene = useCallback(() => {
    setIsLeaving(true);

    const transitionDelay = isFinalScene
      ? MATCH_FADE_MS
      : scene.transition === "blackout"
        ? BLACKOUT_SCENE_FADE_MS
        : NEXT_SCENE_FADE_MS;

    transitionTimerRef.current = window.setTimeout(() => {
      if (isFinalScene) {
        void startMatchAndNavigate();
        return;
      }

      setSceneIndex((current) => Math.min(current + 1, prologueScenes.length - 1));
    }, transitionDelay);
  }, [isFinalScene, scene.transition, startMatchAndNavigate]);

  const advanceScene = useCallback(() => {
    if (isLeaving || isStartingMatch) {
      return;
    }

    if (phase === "image") {
      setPhase("typing");
      setVisibleCharacters(0);
      return;
    }

    if (phase === "typing") {
      setVisibleCharacters(currentSegment.length);
      setPhase("segmentComplete");
      return;
    }

    if (phase === "segmentComplete") {
      if (!isFinalSegment) {
        setSegmentIndex((current) => current + 1);
        setVisibleCharacters(0);
        setPhase("typing");
        return;
      }

      setPhase("detail");
      return;
    }

    leaveCurrentScene();
  }, [currentSegment.length, isFinalSegment, isLeaving, isStartingMatch, leaveCurrentScene, phase]);

  const skipPrologue = useCallback((event: MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    if (isLeaving || isStartingMatch) {
      return;
    }

    clearTransitionTimer();
    setIsLeaving(true);
    transitionTimerRef.current = window.setTimeout(() => {
      void startMatchAndNavigate();
    }, SKIP_FADE_MS);
  }, [clearTransitionTimer, isLeaving, isStartingMatch, startMatchAndNavigate]);

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
      } ${isBlackoutLeaving ? styles.blackoutLeaving : ""}`}
      style={sceneStyle}
      onClick={advanceScene}
      aria-label="프롤로그"
    >
      <div className={styles.sceneImage} aria-hidden="true" />
      <div className={styles.vignette} aria-hidden="true" />
      <div className={styles.noise} aria-hidden="true" />
      <div className={`${styles.blackoutOverlay} ${isBlackoutLeaving ? styles.isVisible : ""}`} aria-hidden="true" />

      <button className={styles.skipButton} type="button" onClick={skipPrologue}>
        {isStartingMatch ? "사건 준비 중" : "전체 건너뛰기"}
      </button>

      {isTextVisible && (
        <section className={styles.textPanel} aria-live="polite">
          <p className={styles.mainText}>{renderVisibleSegment(visibleMain)}</p>
          {phase === "detail" && <p className={styles.detailText}>{scene.detail}</p>}
        </section>
      )}

      <div
        className={`${styles.continueMark} ${
          !isLeaving && (phase === "image" || phase === "segmentComplete" || phase === "detail") ? styles.isVisible : ""
        }`}
        aria-hidden="true"
      />
    </main>
  );
}

function createClientRequestId(): string {
  if (window.crypto?.randomUUID) {
    return window.crypto.randomUUID();
  }

  return `story-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function renderVisibleSegment(segment: string) {
  const firstBreakIndex = segment.indexOf("\n");
  if (firstBreakIndex === -1) {
    return (
      <span className={styles.speakerName} data-speaker="unknown">
        {segment}
      </span>
    );
  }

  const speaker = segment.slice(0, firstBreakIndex).trim();
  const line = segment.slice(firstBreakIndex + 1);

  return (
    <>
      <span className={styles.speakerName} data-speaker={getSpeakerTone(speaker)}>
        {speaker}
      </span>
      <span className={styles.speakerLine}>{line}</span>
    </>
  );
}

function getSpeakerTone(speaker: string): string {
  if (speaker.includes("어머니")) return "mother";
  if (speaker.includes("주술사")) return "shaman";
  if (speaker.includes("아버지") || speaker.includes("가주")) return "father";
  if (speaker.includes("소녀") || speaker.includes("환청")) return "girl";
  if (speaker.includes("분열")) return "fracture";
  if (speaker.includes("나") || speaker.includes("소년")) return "protagonist";
  return "unknown";
}
