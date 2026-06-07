import { KeyboardEvent, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import styles from "./LobbyScreen.module.css";

type ZoneId = "house" | "profile";
type LobbyLocationState = {
  fromPrologue?: boolean;
} | null;

const HOUSE_HIT_PATH = [
  "M598 650",
  "L606 338",
  "L704 291",
  "L714 224",
  "L758 224",
  "L766 278",
  "L807 278",
  "L929 126",
  "L1051 278",
  "L1089 278",
  "L1097 231",
  "L1143 234",
  "L1152 288",
  "L1206 328",
  "L1198 650",
  "L998 650",
  "L994 610",
  "C994 558 968 523 932 523",
  "C895 523 852 560 848 612",
  "L846 650",
  "Z",
].join(" ");

const PROFILE_HIT_PATH = [
  "M915 514",
  "C936 514 950 529 950 551",
  "C950 565 944 574 938 581",
  "C960 588 975 610 981 644",
  "L991 711",
  "C996 727 992 744 979 750",
  "L967 753",
  "L956 727",
  "L956 784",
  "L968 900",
  "C974 909 969 918 954 918",
  "L925 916",
  "L917 807",
  "L903 916",
  "L874 916",
  "C860 916 856 908 863 899",
  "L875 783",
  "L875 729",
  "L863 752",
  "L850 748",
  "C837 743 834 727 840 712",
  "L849 644",
  "C854 611 870 589 890 581",
  "C883 572 879 562 880 550",
  "C881 528 895 514 915 514",
  "Z",
].join(" ");

const LOBBY_TO_GAME_DELAY_MS = 1050;

export function LobbyScreen() {
  const navigate = useNavigate();
  const location = useLocation();
  const transitionTimerRef = useRef<number | null>(null);
  const prologueStateTimerRef = useRef<number | null>(null);
  const [activeZone, setActiveZone] = useState<ZoneId | null>(null);
  const [isEntering, setIsEntering] = useState(false);
  const isFromPrologue = Boolean((location.state as LobbyLocationState)?.fromPrologue);

  useEffect(() => {
    return () => {
      if (transitionTimerRef.current !== null) {
        window.clearTimeout(transitionTimerRef.current);
      }

      if (prologueStateTimerRef.current !== null) {
        window.clearTimeout(prologueStateTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!isFromPrologue) {
      return undefined;
    }

    prologueStateTimerRef.current = window.setTimeout(() => {
      navigate("/lobby", { replace: true, state: null });
    }, 2600);

    return () => {
      if (prologueStateTimerRef.current !== null) {
        window.clearTimeout(prologueStateTimerRef.current);
        prologueStateTimerRef.current = null;
      }
    };
  }, [isFromPrologue, navigate]);

  const openZone = (zone: ZoneId) => {
    if (isEntering) {
      return;
    }

    if (zone === "house") {
      setActiveZone("house");
      setIsEntering(true);
      transitionTimerRef.current = window.setTimeout(() => {
        navigate("/story-cases", {
          state: { fromLobbyTransition: true },
        });
      }, LOBBY_TO_GAME_DELAY_MS);
      return;
    }

    navigate("/profile");
  };

  const handleKeyDown = (event: KeyboardEvent<SVGGElement>, zone: ZoneId) => {
    if (event.key !== "Enter" && event.key !== " ") {
      return;
    }

    event.preventDefault();
    openZone(zone);
  };

  return (
    <main
      className={`${styles.screen} ${isEntering ? styles.isEntering : ""} ${
        isFromPrologue ? styles.fromPrologue : ""
      }`}
      aria-label="로비"
    >
      <img
        className={styles.background}
        src="/prototype/assets/lobby-background.png"
        alt=""
        draggable={false}
      />
      <div className={styles.shadow} aria-hidden="true" />

      <button className={styles.backButton} type="button" onClick={() => navigate("/")}>
        메인으로
      </button>

      <img
        className={`${styles.hoverLayer} ${activeZone === "house" ? styles.isVisible : ""}`}
        src="/prototype/assets/lobby-house-hover-outline.png"
        alt=""
        draggable={false}
      />
      <img
        className={`${styles.hoverLayer} ${activeZone === "profile" ? styles.isVisible : ""}`}
        src="/prototype/assets/lobby-person-hover-outline.png"
        alt=""
        draggable={false}
      />

      <svg
        className={styles.sceneOverlay}
        viewBox="0 0 1672 941"
        preserveAspectRatio="xMidYMid slice"
        aria-hidden="false"
      >
        <g
          className={`${styles.zone} ${activeZone === "house" ? styles.isActive : ""}`}
          role="button"
          tabIndex={0}
          aria-label="AI 스토리 모드 진입"
          onMouseEnter={() => setActiveZone("house")}
          onMouseLeave={() => !isEntering && setActiveZone(null)}
          onFocus={() => setActiveZone("house")}
          onBlur={() => !isEntering && setActiveZone(null)}
          onClick={() => openZone("house")}
          onKeyDown={(event) => handleKeyDown(event, "house")}
        >
          <path className={styles.hitArea} d={HOUSE_HIT_PATH} />
          <text className={styles.zoneLabel} x="930" y="218" textAnchor="middle">
            의식을 시작한다
          </text>
        </g>

        <g
          className={`${styles.zone} ${activeZone === "profile" ? styles.isActive : ""}`}
          role="button"
          tabIndex={0}
          aria-label="프로필 및 전적 요약"
          onMouseEnter={() => setActiveZone("profile")}
          onMouseLeave={() => !isEntering && setActiveZone(null)}
          onFocus={() => setActiveZone("profile")}
          onBlur={() => !isEntering && setActiveZone(null)}
          onClick={() => openZone("profile")}
          onKeyDown={(event) => handleKeyDown(event, "profile")}
        >
          <path className={styles.hitArea} d={PROFILE_HIT_PATH} />
          <text className={styles.zoneLabel} x="918" y="490" textAnchor="middle">
            나에 대하여
          </text>
        </g>
      </svg>

      <div className={styles.entryShade} aria-hidden="true" />
      <div className={styles.blackFade} aria-hidden="true" />
    </main>
  );
}
