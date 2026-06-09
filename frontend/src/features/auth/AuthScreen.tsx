import { FormEvent, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiClientError } from "../../shared/api/client";
import { login, signup } from "../../shared/api/resources";
import styles from "./AuthScreen.module.css";

type AuthMode = "login" | "signup" | "password-reset";

type AuthScreenProps = {
  mode: AuthMode;
};

const copyByMode = {
  login: {
    kicker: "계정 확인",
    title: "로그인",
    description: "의식 기록은 HttpOnly cookie 기반 Django 인증 세션에 보관됩니다.",
    submitLabel: "로그인",
    notice: "로그인 정보를 확인하고 있습니다.",
  },
  signup: {
    kicker: "새 기록 생성",
    title: "회원가입",
    description: "가입 후 로그인 화면에서 새 세션을 시작합니다.",
    submitLabel: "회원가입",
    notice: "회원가입 정보를 확인하고 있습니다.",
  },
  "password-reset": {
    kicker: "계정 복구",
    title: "비밀번호 재설정",
    description: "등록한 이메일로 재설정 안내를 보내는 화면으로 연결될 예정입니다.",
    submitLabel: "재설정 요청",
    notice: "비밀번호 재설정 API 연결 전 임시 화면입니다.",
  },
} satisfies Record<AuthMode, { kicker: string; title: string; description: string; submitLabel: string; notice: string }>;

export function AuthScreen({ mode }: AuthScreenProps) {
  const navigate = useNavigate();
  const [notice, setNotice] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const copy = copyByMode[mode];
  const isSignup = mode === "signup";
  const isPasswordReset = mode === "password-reset";

  const fields = useMemo(() => {
    if (isPasswordReset) {
      return [
        { id: "email", label: "이메일", type: "email", autoComplete: "email" },
      ];
    }

    const baseFields = [
      { id: "email", label: "이메일", type: "email", autoComplete: "email" },
      { id: "password", label: "비밀번호", type: "password", autoComplete: isSignup ? "new-password" : "current-password" },
    ];

    if (!isSignup) {
      return baseFields;
    }

    return [
      { id: "nickname", label: "닉네임", type: "text", autoComplete: "nickname" },
      ...baseFields,
      { id: "password-confirm", label: "비밀번호 확인", type: "password", autoComplete: "new-password" },
    ];
  }, [isPasswordReset, isSignup]);

  const submitForm = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);

    if (isPasswordReset) {
      setNotice(copy.notice);
      return;
    }

    setIsSubmitting(true);
    setNotice(copy.notice);

    try {
      const email = getRequiredFormString(form, "email");
      const password = getRequiredFormString(form, "password");

      if (isSignup) {
        const passwordConfirm = getRequiredFormString(form, "password-confirm");
        if (password !== passwordConfirm) {
          setNotice("비밀번호 확인이 일치하지 않습니다.");
          return;
        }

        await signup({
          email,
          nickname: getRequiredFormString(form, "nickname"),
          password,
        });
        setNotice("회원가입이 완료되었습니다. 로그인해주세요.");
        navigate("/login");
        return;
      }

      await login({ email, password });
      navigate("/lobby");
    } catch (error) {
      setNotice(formatAuthError(error));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className={styles.screen} aria-label={copy.title}>
      <img className={styles.background} src="/prototype/assets/lobby-background.png" alt="" draggable={false} />
      <div className={styles.shadow} aria-hidden="true" />

      <section className={styles.panel} aria-labelledby="auth-title">
        <p className={styles.kicker}>{copy.kicker}</p>
        <h1 id="auth-title">{copy.title}</h1>
        <p className={styles.description}>{copy.description}</p>

        <form className={styles.form} onSubmit={submitForm}>
          {fields.map((field) => (
            <label className={styles.field} htmlFor={field.id} key={field.id}>
              <span>{field.label}</span>
              <input id={field.id} name={field.id} type={field.type} autoComplete={field.autoComplete} />
            </label>
          ))}

          <button className={styles.submitButton} type="submit" disabled={isSubmitting}>
            {isSubmitting ? "처리 중" : copy.submitLabel}
          </button>
        </form>

        <div className={styles.links}>
          {mode !== "login" && <Link to="/login">로그인으로</Link>}
          {mode !== "signup" && <Link to="/signup">회원가입</Link>}
          {mode !== "password-reset" && <Link to="/password-reset">비밀번호 재설정</Link>}
        </div>

        <p className={`${styles.notice} ${notice ? styles.isVisible : ""}`} aria-live="polite">
          {notice}
        </p>

        <button className={styles.backButton} type="button" onClick={() => navigate("/")}>
          메인으로 돌아가기
        </button>
      </section>
    </main>
  );
}

function getRequiredFormString(form: FormData, key: string): string {
  const value = form.get(key);
  return typeof value === "string" ? value.trim() : "";
}

function formatAuthError(error: unknown): string {
  if (error instanceof ApiClientError) {
    if (error.code === "LOGIN_RATE_LIMITED") {
      return "로그인 실패가 반복되어 잠시 후 다시 시도해야 합니다.";
    }
    if (error.code === "INVALID_CREDENTIALS") {
      return "이메일 또는 비밀번호가 올바르지 않습니다.";
    }
    if (error.code === "VALIDATION_ERROR") {
      return formatFieldErrors(error.details) || "입력값을 다시 확인해주세요.";
    }
    return error.message || error.code;
  }

  return "요청 처리 중 문제가 발생했습니다.";
}

function formatFieldErrors(details: Record<string, unknown>): string {
  const messages = Object.entries(details)
    .flatMap(([field, value]) => formatFieldErrorValue(field, value))
    .filter((message) => message.length > 0);

  return messages.join(" ");
}

function formatFieldErrorValue(field: string, value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.flatMap((item) => formatFieldErrorValue(field, item));
  }

  if (typeof value === "string") {
    return [`${formatFieldLabel(field)}: ${value}`];
  }

  if (value && typeof value === "object") {
    return Object.entries(value as Record<string, unknown>).flatMap(([nestedField, nestedValue]) =>
      formatFieldErrorValue(nestedField, nestedValue),
    );
  }

  return [];
}

function formatFieldLabel(field: string): string {
  const labels: Record<string, string> = {
    email: "이메일",
    nickname: "닉네임",
    password: "비밀번호",
    non_field_errors: "입력값",
  };

  return labels[field] ?? field;
}
