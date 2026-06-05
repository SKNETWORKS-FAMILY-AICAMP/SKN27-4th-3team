import styles from "./RitualDuelScreen.module.css";

export function RitualDuelScreen() {
  return (
    <main className={styles.screen}>
      <iframe
        className={styles.prototypeFrame}
        src="/prototype/game-background.html"
        title="Mirror Guest prototype"
      />
    </main>
  );
}
