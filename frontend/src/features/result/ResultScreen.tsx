import { useEffect, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { ApiClientError } from "../../shared/api/client";
import { getMatchResult } from "../../shared/api/resources";
import { BGM_TRACKS, useBackgroundMusic } from "../../shared/audio/audio";
import type { MatchResult, PublicLog, ResourceState } from "../../shared/types/api";
import styles from "./ResultScreen.module.css";

const RESULT_COPY = {
  player_win: {
    kicker: "사건 종료 기록",
    title: "봉인 성공",
    outcome: "클리어",
    summary: "숨겨진 이름이 진실의 거울 앞에서 완성되었고, 무명실은 더는 입술을 묶지 못했다.",
    style: "단서를 모아 봉인 조건을 완성한 플레이 기록입니다.",
  },
  player_loss: {
    sanity_zero: {
      kicker: "사건 종료 기록",
      title: "이성 붕괴",
      outcome: "게임 오버",
      summary: "플레이어의 이름과 숨겨진 이름이 같은 숨결로 겹쳐졌다.",
      style: "이성 손실을 감수하며 의식을 밀어붙인 플레이 기록입니다.",
    },
    curse_marks_loss: {
      kicker: "사건 종료 기록",
      title: "저주 잠식",
      outcome: "게임 오버",
      summary: "저주의 흔적이 한계를 넘었고, 마지막 기록은 닫힌 채 남았다.",
      style: "강한 행동의 대가가 누적된 플레이 기록입니다.",
    },
    turn_limit: {
      kicker: "사건 종료 기록",
      title: "시간 초과",
      outcome: "게임 오버",
      summary: "정해진 턴 안에 봉인을 완성하지 못했다.",
      style: "탐색과 방어에 많은 시간을 사용한 플레이 기록입니다.",
    },
    unresolved: {
      kicker: "사건 종료 기록",
      title: "의식 실패",
      outcome: "게임 오버",
      summary: "사건 파일은 미완성 기록으로 닫혔다.",
      style: "결과 원인을 확정할 수 없는 기록입니다.",
    },
  },
};

function getCopy(resultCode: string, reason: string) {
  if (resultCode === "player_win") return RESULT_COPY.player_win;
  return RESULT_COPY.player_loss[reason as keyof typeof RESULT_COPY.player_loss] ?? RESULT_COPY.player_loss.unresolved;
}

export function ResultScreen() {
  const navigate = useNavigate();
  const { matchId = "prototype-mirror-guest" } = useParams();
  const [searchParams] = useSearchParams();
  const [result, setResult] = useState<MatchResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const fallbackResultCode = searchParams.get("outcome") === "win" ? "player_win" : "player_loss";
  const fallbackReason = toOfficialReason(searchParams.get("reason") ?? "unresolved");
  const resultCode = result?.result ?? fallbackResultCode;
  const resultReason = result?.result_reason ?? fallbackReason;
  const copy = getCopy(resultCode, resultReason);
  const storyResultText = result?.story_result_text.length
    ? result.story_result_text
    : [searchParams.get("result_summary") || copy.summary];
  const styleSummaryText = result?.style_summary.display_text || result?.style_summary.label || searchParams.get("style_summary") || copy.style;
  const publicLogs = result?.turn_logs.length ? result.turn_logs : fallbackPublicLogs(searchParams.get("log"));
  const finalResources = result?.final_resources;
  const llmSummaryText = result?.llm_summary.text?.trim();
  useBackgroundMusic(getResultMusicTrack(resultCode, resultReason), { volume: 0.48 });

  useEffect(() => {
    let cancelled = false;

    async function loadResult() {
      setIsLoading(true);
      setErrorMessage("");

      try {
        const data = await getMatchResult(matchId);
        if (cancelled) return;
        setResult(data.result);
      } catch (error) {
        if (cancelled) return;
        setErrorMessage(formatResultError(error));
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    loadResult();
    return () => {
      cancelled = true;
    };
  }, [matchId]);

  return (
    <main className={styles.screen} data-outcome={resultCode === "player_win" ? "win" : "lose"}>
      <section className={styles.panel} aria-labelledby="result-title">
        <p className={styles.kicker}>{copy.kicker}</p>
        <h1 id="result-title">{copy.title}</h1>
        <p className={styles.summary} aria-live="polite">
          {isLoading ? "결과 기록을 불러오고 있습니다." : errorMessage || storyResultText[0]}
        </p>

        <dl className={styles.stats} aria-label="최종 상태">
          <div>
            <dt>결과</dt>
            <dd>{copy.outcome}</dd>
          </div>
          <div>
            <dt>턴</dt>
            <dd>{formatTurnCount(publicLogs, searchParams.get("turn"))}</dd>
          </div>
          <div>
            <dt>이성</dt>
            <dd>{formatResourceValue(finalResources, "sanity", "sanity_max", searchParams.get("sanity"))}</dd>
          </div>
          <div>
            <dt>저주</dt>
            <dd>{formatResourceValue(finalResources, "curse_marks", "curse_marks_max", searchParams.get("curse"))}</dd>
          </div>
          <div>
            <dt>진명</dt>
            <dd>
              {formatResourceValue(
                finalResources,
                "true_name_fragments",
                "true_name_fragments_required",
                searchParams.get("truth"),
              )}
            </dd>
          </div>
        </dl>

        <section className={styles.record} aria-labelledby="story-result-title">
          <h2 id="story-result-title">사건 결말</h2>
          {storyResultText.map((line) => (
            <p key={line}>{line}</p>
          ))}
        </section>

        <section className={styles.record} aria-labelledby="public-log-title">
          <h2 id="public-log-title">공개 로그</h2>
          {publicLogs.map((log) => (
            <p key={`${log.turn_number}-${log.text}`}>
              {log.turn_number > 0 ? `${log.turn_number}턴. ` : ""}
              {log.text}
            </p>
          ))}
        </section>

        <section className={styles.record} aria-labelledby="style-title">
          <h2 id="style-title">플레이 요약</h2>
          <p>{styleSummaryText}</p>
          {llmSummaryText ? <p>{llmSummaryText}</p> : null}
        </section>

        <div className={styles.actions}>
          <button type="button" onClick={() => navigate(`/matches/${matchId}`, { state: { fromPrologueTransition: true } })}>
            다시 의식장으로
          </button>
          <button type="button" onClick={() => navigate("/lobby")}>
            로비로 돌아가기
          </button>
        </div>
      </section>
    </main>
  );
}

function toOfficialReason(reason: string): string {
  const aliases: Record<string, string> = {
    sanity: "sanity_zero",
    curse: "curse_marks_loss",
    turns: "turn_limit",
    unknown: "unresolved",
  };

  return aliases[reason] ?? reason;
}

function fallbackPublicLogs(log: string | null): PublicLog[] {
  return [
    {
      turn_number: 0,
      text: log || "저장된 공개 로그가 없습니다.",
    },
  ];
}

function formatTurnCount(publicLogs: PublicLog[], fallback: string | null): string {
  const lastTurn = publicLogs.at(-1)?.turn_number;
  if (lastTurn && lastTurn > 0) return `${lastTurn}`;
  return fallback || "--";
}

function formatResourceValue(
  resources: ResourceState | undefined,
  valueKey: keyof ResourceState,
  maxKey: keyof ResourceState,
  fallback: string | null,
): string {
  if (!resources) return fallback || "--";

  const value = resources[valueKey];
  const maxValue = resources[maxKey];
  if (typeof value !== "number" || typeof maxValue !== "number") return fallback || "--";

  return `${value}/${maxValue}`;
}

function formatResultError(error: unknown): string {
  if (error instanceof ApiClientError) {
    if (error.code === "MATCH_NOT_RESOLVED") {
      return "아직 종료되지 않은 매치입니다. 의식장으로 돌아가 매치를 마무리해야 합니다.";
    }
    if (error.code === "AUTH_REQUIRED" || error.code === "SESSION_EXPIRED") {
      return "로그인 세션을 확인한 뒤 결과를 조회할 수 있습니다.";
    }

    return error.message || error.code;
  }

  return "결과 기록을 불러오지 못했습니다.";
}

function getResultMusicTrack(resultCode: string, reason: string): string {
  if (resultCode === "player_win") return BGM_TRACKS.clear;
  if (reason === "sanity_zero") return BGM_TRACKS.sanityGameOver;
  return BGM_TRACKS.gameOver;
}
