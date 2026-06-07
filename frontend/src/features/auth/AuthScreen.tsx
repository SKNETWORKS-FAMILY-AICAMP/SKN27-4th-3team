import { FormEvent, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import styles from "./AuthScreen.module.css";

type AuthMode = "login" | "signup" | "password-reset";

type AuthScreenProps = {
  mode: AuthMode;
};

const copyByMode = {
  login: {
    kicker: "계정 확인",
    title: "로그인",
    description: "의식 기록은 Spring Boot 인증 API가 연결되면 계정에 보관됩니다.",
    submitLabel: "로그인",
    notice: "로그인 API 연결 전 임시 화면입니다.",
  },
  signup: {
    kicker: "새 기록 생성",
    title: "회원가입",
    description: "HttpOnly cookie 기반 인증 연결 전까지는 화면 흐름만 확인합니다.",
    submitLabel: "회원가입",
    notice: "회원가입 API 연결 전 임시 화면입니다.",
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

  const submitForm = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setNotice(copy.notice);
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

          <button className={styles.submitButton} type="submit">
            {copy.submitLabel}
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
