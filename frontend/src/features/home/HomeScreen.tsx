import { useNavigate } from "react-router-dom";
import styles from "./HomeScreen.module.css";
import { useState } from "react";
import { BGM_TRACKS, useBackgroundMusic } from "../../shared/audio/audio";

export function HomeScreen() {
  const navigate = useNavigate();
  const [exitNotice, setExitNotice] = useState("");
  useBackgroundMusic(BGM_TRACKS.menu);

  const requestExit = () => {
    window.close();
    setExitNotice("브라우저에서는 창 닫기가 차단될 수 있습니다.");
  };

  const menuItems = [
    { label: "새 게임", onClick: () => navigate("/lobby") },
    { label: "로그인", onClick: () => navigate("/login") },
    { label: "회원가입", onClick: () => navigate("/signup") },
    { label: "종료", onClick: requestExit },
  ];

  return (
    <main className={styles.screen} aria-label="메인 화면">
      <div className={styles.shadow} aria-hidden="true" />

      <section className={styles.bookFrame} aria-labelledby="main-title">
        <img
          className={styles.background}
          src="/prototype/assets/메인메뉴 바탕.png"
          alt=""
          draggable={false}
        />

        <div className={styles.menuLayer}>
          <h1 id="main-title" className={styles.visuallyHidden}>
            무명의 저주
          </h1>
          <img
            className={styles.titleImage}
            src="/prototype/assets/main-title-clean.png"
            alt="The Curse of Namelessness, 무명의 저주"
            draggable={false}
          />

        <nav className={styles.menuList} aria-label="메인 메뉴">
            {menuItems.map((item) => (
              <button className={styles.menuButton} type="button" onClick={item.onClick} key={item.label}>
                <span>{item.label}</span>
              </button>
            ))}
        </nav>

        <p className={`${styles.exitNotice} ${exitNotice ? styles.isVisible : ""}`} aria-live="polite">
          {exitNotice}
        </p>
        </div>
      </section>
    </main>
  );
}
