import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiClientError } from "../../shared/api/client";
import { listStoryCases } from "../../shared/api/resources";
import type { StoryCaseSummary } from "../../shared/types/api";
import styles from "./StoryCasesScreen.module.css";

export function StoryCasesScreen() {
  const navigate = useNavigate();
  const [cases, setCases] = useState<StoryCaseSummary[]>([]);
  const [notice, setNotice] = useState("사건 목록을 불러오고 있습니다.");

  useEffect(() => {
    let cancelled = false;

    async function loadCases() {
      try {
        const data = await listStoryCases();
        if (cancelled) return;

        setCases(data.cases);
        setNotice(data.cases.length > 0 ? "" : "진행 가능한 사건이 없습니다.");
      } catch (error) {
        if (cancelled) return;
        setNotice(formatStoryCaseError(error));
      }
    }

    loadCases();
    return () => {
      cancelled = true;
    };
  }, []);

  const visibleCases = cases.length > 0 ? cases : [fallbackStoryCase];

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

        {visibleCases.map((storyCase, index) => (
          <article className={styles.caseCard} key={storyCase.case_id}>
            <div className={styles.caseMeta}>
              <span>사건 파일 {String(index + 1).padStart(2, "0")}</span>
              <span>{storyCase.mvp_available ? "진행 가능" : "잠김"}</span>
            </div>
            <h2>{storyCase.title}</h2>
            <p className={styles.summary}>{storyCase.summary || fallbackStoryCase.summary}</p>
            <dl className={styles.details}>
              <div>
                <dt>난이도</dt>
                <dd>{storyCase.difficulty || "MVP"}</dd>
              </div>
              <div>
                <dt>예상 턴</dt>
                <dd>{storyCase.estimated_turns ? `${storyCase.estimated_turns}턴` : "12턴"}</dd>
              </div>
              <div>
                <dt>목표</dt>
                <dd>진명 조각을 모아 이름을 완성하고 봉인할 것</dd>
              </div>
            </dl>
            <button
              className={styles.startButton}
              type="button"
              disabled={!storyCase.mvp_available}
              onClick={() => navigate("/prologue", { state: { caseId: storyCase.case_id } })}
            >
              이 사건을 선택한다
            </button>
          </article>
        ))}

        {notice ? <p aria-live="polite">{notice}</p> : null}

        <button className={styles.backButton} type="button" onClick={() => navigate("/lobby")}>
          로비로 돌아가기
        </button>
      </section>
    </main>
  );
}

const fallbackStoryCase: StoryCaseSummary = {
  case_id: "nameless_curse",
  title: "무명(無名)의 저주",
  summary: "이름을 빼앗긴 원혼과 진실의 거울을 마주하는 사건.",
  difficulty: "MVP",
  mvp_available: true,
  estimated_turns: 12,
};

function formatStoryCaseError(error: unknown): string {
  if (error instanceof ApiClientError) {
    if (error.code === "AUTH_REQUIRED" || error.code === "SESSION_EXPIRED") {
      return "로그인 후 사건 목록을 확인할 수 있습니다.";
    }
    return error.message || error.code;
  }

  return "사건 목록을 불러오지 못했습니다.";
}
