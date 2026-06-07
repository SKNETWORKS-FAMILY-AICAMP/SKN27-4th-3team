import { useNavigate } from "react-router-dom";
import styles from "./ProfileSummaryScreen.module.css";

const profile = {
  nickname: "이안",
  email: "mirror.guest@example.com",
  joinedAt: "임시 계정",
  summary: "거울 속의 손님 사건을 기준으로 한 임시 프로필입니다. 실제 값은 GET /api/v1/profile/me 연결 후 교체됩니다.",
};

const recordSummary = [
  { label: "총 매치", value: "12" },
  { label: "클리어", value: "7" },
  { label: "실패", value: "5" },
  { label: "최고 진명", value: "3/3" },
];

const styleMetrics = [
  { label: "공격성", value: 0.28, note: "저주 선택 비율" },
  { label: "방어성", value: 0.22, note: "수호 선택 비율" },
  { label: "정보 집착", value: 0.36, note: "간파 선택 비율" },
  { label: "기만성", value: 0.14, note: "속임수 선택 비율" },
  { label: "위험 선호", value: 0.18, note: "계약 선택 비율" },
  { label: "침묵 의존", value: 0.31, note: "침묵 선택 비율" },
];

const recentEvents = [
  { turn: "12턴", action: "봉인", result: "진명 선언 성공", outcome: "클리어" },
  { turn: "09턴", action: "간파", result: "거짓 단서 확정", outcome: "진행" },
  { turn: "04턴", action: "수호", result: "이성 손실 방어", outcome: "진행" },
];

export function ProfileSummaryScreen() {
  const navigate = useNavigate();
  const returnToPreviousScreen = () => {
    if (window.history.state?.idx > 0) {
      navigate(-1);
      return;
    }

    navigate("/lobby");
  };

  return (
    <main className={styles.screen} aria-label="프로필 및 전적 요약">
      <section className={styles.panel} aria-labelledby="profile-summary-title">
        <header className={styles.header}>
          <div>
            <p className={styles.kicker}>프로필 기록</p>
            <h1 id="profile-summary-title">프로필 및 전적 요약</h1>
          </div>
          <button type="button" onClick={returnToPreviousScreen}>
            돌아가기
          </button>
        </header>

        <section className={styles.identity} aria-label="계정 요약">
          <div className={styles.sealMark} aria-hidden="true">無</div>
          <div>
            <strong>{profile.nickname}</strong>
            <span>{profile.email}</span>
            <p>{profile.summary}</p>
          </div>
          <em>{profile.joinedAt}</em>
        </section>

        <section className={styles.recordGrid} aria-label="전적 요약">
          {recordSummary.map((item) => (
            <article key={item.label}>
              <span>{item.label}</span>
              <strong>{item.value}</strong>
            </article>
          ))}
        </section>

        <section className={styles.contentGrid}>
          <article className={styles.sectionBlock} aria-labelledby="style-metrics-title">
            <h2 id="style-metrics-title">스타일 지표</h2>
            <p>각 턴 resolve 직후 계산되고, 매치 종료 시 최종 재계산되는 AI Profile 더미값입니다.</p>
            <ul className={styles.metricList}>
              {styleMetrics.map((metric) => (
                <li key={metric.label}>
                  <div>
                    <strong>{metric.label}</strong>
                    <span>{metric.note}</span>
                  </div>
                  <meter min="0" max="1" value={metric.value} aria-label={`${metric.label} ${metric.value}`} />
                  <em>{Math.round(metric.value * 100)}%</em>
                </li>
              ))}
            </ul>
          </article>

          <article className={styles.sectionBlock} aria-labelledby="recent-events-title">
            <h2 id="recent-events-title">최근 행동 이벤트</h2>
            <p>행동 이벤트 저장 schema에 맞춘 임시 표시입니다. 실제 저장은 백엔드 연결 후 반영됩니다.</p>
            <ol className={styles.eventList}>
              {recentEvents.map((event) => (
                <li key={`${event.turn}-${event.action}`}>
                  <span>{event.turn}</span>
                  <strong>{event.action}</strong>
                  <p>{event.result}</p>
                  <em>{event.outcome}</em>
                </li>
              ))}
            </ol>
          </article>
        </section>
      </section>
    </main>
  );
}
