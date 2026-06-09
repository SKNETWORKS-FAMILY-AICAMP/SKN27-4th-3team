import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiClientError } from "../../shared/api/client";
import { getProfileMe } from "../../shared/api/resources";
import { BGM_TRACKS, useBackgroundMusic } from "../../shared/audio/audio";
import type { ProfileSummary, StyleMetrics, User } from "../../shared/types/api";
import styles from "./ProfileSummaryScreen.module.css";

type ProfileData = {
  user: User;
  profile: ProfileSummary;
};

const STYLE_METRIC_ITEMS: Array<{ key: keyof StyleMetrics; label: string; note: string }> = [
  { key: "aggression", label: "공격성", note: "저주 선택 비율" },
  { key: "defense", label: "방어성", note: "수호 선택 비율" },
  { key: "insight_focus", label: "정보 집중", note: "간파 선택 비율" },
  { key: "deception", label: "기만성", note: "속임수 선택 비율" },
  { key: "risk_preference", label: "위험 선호", note: "계약 선택 비율" },
  { key: "silence_reliance", label: "침묵 의존", note: "침묵 선택 비율" },
  { key: "crisis_guard_rate", label: "위기 수호", note: "위기 상황 수호 비율" },
  { key: "crisis_contract_rate", label: "위기 계약", note: "위기 상황 계약 비율" },
  { key: "late_choice_rate", label: "지연 선택", note: "제한 시간 임박 선택 비율" },
];

export function ProfileSummaryScreen() {
  const navigate = useNavigate();
  const [profileData, setProfileData] = useState<ProfileData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  useBackgroundMusic(BGM_TRACKS.menu);
  const returnToPreviousScreen = () => {
    if (window.history.state?.idx > 0) {
      navigate(-1);
      return;
    }

    navigate("/lobby");
  };
  const profile = profileData?.profile;
  const user = profileData?.user;
  const recordSummary = profile
    ? [
        { label: "총 매치", value: `${profile.public_record.ai_story_matches}` },
        { label: "클리어", value: `${profile.public_record.ai_story_wins}` },
        { label: "실패", value: `${profile.public_record.ai_story_losses}` },
        { label: "스타일", value: profile.style_summary.label || "분석 중" },
      ]
    : [];
  const styleMetrics = profile
    ? STYLE_METRIC_ITEMS.map((metric) => ({
        ...metric,
        value: normalizeMetric(profile.style_summary.metrics[metric.key]),
      }))
    : [];

  useEffect(() => {
    let cancelled = false;

    async function loadProfile() {
      setIsLoading(true);
      setErrorMessage("");

      try {
        const data = await getProfileMe();
        if (cancelled) return;
        setProfileData(data);
      } catch (error) {
        if (cancelled) return;
        setErrorMessage(formatProfileError(error));
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    loadProfile();
    return () => {
      cancelled = true;
    };
  }, []);

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
            <strong>{profile?.nickname ?? "프로필 확인 중"}</strong>
            <span>{user?.email ?? "세션 계정을 확인하고 있습니다."}</span>
            <p aria-live="polite">
              {isLoading
                ? "프로필 기록을 불러오고 있습니다."
                : errorMessage || profile?.style_summary.display_text || "아직 누적된 스타일 설명이 없습니다."}
            </p>
          </div>
          <em>{formatDate(user?.created_at)}</em>
        </section>

        <section className={styles.recordGrid} aria-label="전적 요약">
          {recordSummary.length > 0
            ? recordSummary.map((item) => (
                <article key={item.label}>
                  <span>{item.label}</span>
                  <strong>{item.value}</strong>
                </article>
              ))
            : ["총 매치", "클리어", "실패", "스타일"].map((label) => (
                <article key={label}>
                  <span>{label}</span>
                  <strong>--</strong>
                </article>
              ))}
        </section>

        <section className={styles.contentGrid}>
          <article className={styles.sectionBlock} aria-labelledby="style-metrics-title">
            <h2 id="style-metrics-title">스타일 지표</h2>
            <p>{profile?.style_summary.updated_at ? "최근 갱신된 AI Profile 지표입니다." : "누적 기록이 쌓이면 AI Profile 지표가 갱신됩니다."}</p>
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
            <h2 id="recent-events-title">프로필 상태</h2>
            <p>공식 프로필 응답 기준으로 집계된 공개 기록과 스타일 갱신 시점입니다.</p>
            <ol className={styles.eventList}>
              <li>
                <span>전적</span>
                <strong>{profile ? `${profile.public_record.ai_story_matches}건` : "--"}</strong>
                <p>AI 스토리 매치 누적 공개 기록</p>
                <em>{profile ? `${profile.public_record.ai_story_wins}승/${profile.public_record.ai_story_losses}패` : "--"}</em>
              </li>
              <li>
                <span>스타일</span>
                <strong>{profile?.style_summary.label || "분석 중"}</strong>
                <p>{profile?.style_summary.display_text || "아직 누적된 스타일 설명이 없습니다."}</p>
                <em>{formatDate(profile?.style_summary.updated_at)}</em>
              </li>
            </ol>
          </article>
        </section>
      </section>
    </main>
  );
}

function normalizeMetric(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.min(1, Math.max(0, value));
}

function formatDate(value: string | null | undefined): string {
  if (!value) return "기록 없음";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

function formatProfileError(error: unknown): string {
  if (error instanceof ApiClientError) {
    if (error.code === "AUTH_REQUIRED" || error.code === "SESSION_EXPIRED") {
      return "로그인 세션을 확인한 뒤 프로필을 조회할 수 있습니다.";
    }

    return error.message || error.code;
  }

  return "프로필 기록을 불러오지 못했습니다.";
}
