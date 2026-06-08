import { useNavigate } from "react-router-dom";
import styles from "./HomeScreen.module.css";
import { useState } from "react";

export function HomeScreen() {
  const navigate = useNavigate();
  const [exitNotice, setExitNotice] = useState("");

  const requestExit = () => {
    window.close();
    setExitNotice("브라우저에서는 창 닫기가 차단될 수 있습니다.");
  };

  return (
    <main className={styles.screen} aria-label="메인 화면">
      <img
        className={styles.background}
        src="/prototype/assets/lobby-background.png"
        alt=""
        draggable={false}
      />
      <div className={styles.shadow} aria-hidden="true" />

      <section className={styles.menu}>
        <p className={styles.eyebrow}>The Curse of Namelessness</p>
        <h1 className={styles.title}>무명의 저주</h1>
        <nav className={styles.menuList} aria-label="메인 메뉴">
          <button className={styles.menuButton} type="button" onClick={() => navigate("/lobby")}>
            새 게임
          </button>
          <button className={styles.menuButton} type="button" onClick={() => navigate("/login")}>
            로그인
          </button>
          <button className={styles.menuButton} type="button" onClick={() => navigate("/signup")}>
            회원가입
          </button>
          <button className={styles.menuButton} type="button" onClick={requestExit}>
            종료
          </button>
        </nav>
        <p className={`${styles.exitNotice} ${exitNotice ? styles.isVisible : ""}`} aria-live="polite">
          {exitNotice}
        </p>
      </section>
    </main>
  );
}
