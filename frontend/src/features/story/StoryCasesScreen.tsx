import { useNavigate } from "react-router-dom";
import styles from "./StoryCasesScreen.module.css";

export function StoryCasesScreen() {
  const navigate = useNavigate();

  return (
    <main className={styles.screen} aria-label="AI 사건 선택">
      <img className={styles.background} src="/prototype/assets/lobby-background.png" alt="" draggable={false} />
      <div className={styles.shadow} aria-hidden="true" />

      <section className={styles.shell} aria-labelledby="story-cases-title">
        <div className={styles.header}>
          <p className={styles.kicker}>AI 스토리 모드</p>
          <h1 id="story-cases-title">사건 선택</h1>
          <p>
            MVP에서는 첫 사건만 열려 있다. 사건을 고르면 프롤로그 기록을 확인한 뒤 의식장으로 들어간다.
          </p>
        </div>

        <article className={styles.caseCard}>
          <div className={styles.caseMeta}>
            <span>사건 파일 01</span>
            <span>진행 가능</span>
          </div>
          <h2>거울 속의 손님</h2>
          <p className={styles.summary}>
            오래된 방의 거울은 얼굴을 비추지 않는다. 그 안에는 잊힌 기억, 사라진 목소리, 그리고 잃어버린 방 번호가 남아 있다.
          </p>
          <dl className={styles.details}>
            <div>
              <dt>괴이</dt>
              <dd>거울을 통해 사람의 기억을 훔치는 존재</dd>
            </div>
            <div>
              <dt>금기</dt>
              <dd>같은 것을 두 번 묻지 말 것</dd>
            </div>
            <div>
              <dt>목표</dt>
              <dd>진명 조각을 모아 이름을 완성하고 봉인할 것</dd>
            </div>
          </dl>
          <button className={styles.startButton} type="button" onClick={() => navigate("/prologue")}>
            이 사건을 선택한다
          </button>
        </article>

        <button className={styles.backButton} type="button" onClick={() => navigate("/lobby")}>
          로비로 돌아가기
        </button>
      </section>
    </main>
  );
}
