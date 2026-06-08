import { CSSProperties, MouseEvent, useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import styles from "./PrologueScreen.module.css";
import { prologueScenes } from "./prologueScenes";

const DETAIL_REVEAL_DELAY_MS = 260;
const NEXT_SCENE_FADE_MS = 880;
const MATCH_FADE_MS = 1850;

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
  const transitionTimerRef = useRef<number | null>(null);
  const [sceneIndex, setSceneIndex] = useState(0);
  const [visibleCharacters, setVisibleCharacters] = useState(0);
  const [isDetailVisible, setIsDetailVisible] = useState(false);
  const [isLeaving, setIsLeaving] = useState(false);

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

  const advanceScene = useCallback(() => {
    if (isLeaving) {
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
        navigate("/matches/prototype-mirror-guest", { state: { fromPrologueTransition: true } });
        return;
      }

      setVisibleCharacters(0);
      setIsDetailVisible(false);
      setIsLeaving(false);
      setSceneIndex((current) => Math.min(current + 1, prologueScenes.length - 1));
    }, isFinalScene ? MATCH_FADE_MS : NEXT_SCENE_FADE_MS);
  }, [isFinalScene, isLeaving, isSceneComplete, navigate, scene.main.length]);

  const skipPrologue = useCallback((event: MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    if (isLeaving) {
      return;
    }

    if (transitionTimerRef.current !== null) {
      window.clearTimeout(transitionTimerRef.current);
    }

    setIsLeaving(true);
    transitionTimerRef.current = window.setTimeout(() => {
      navigate("/matches/prototype-mirror-guest", { state: { fromPrologueTransition: true } });
    }, 720);
  }, [isLeaving, navigate]);

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
        전체 건너뛰기
      </button>

      <section className={styles.textPanel} aria-live="polite">
        <p className={styles.mainText}>{visibleMain}</p>
        <p className={`${styles.detailText} ${isDetailVisible ? styles.isVisible : ""}`}>
          {scene.detail}
        </p>
      </section>

      <div className={`${styles.continueMark} ${isSceneComplete ? styles.isVisible : ""}`} aria-hidden="true" />
    </main>
  );
}
