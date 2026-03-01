"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

const translations = {
  kz: {
    title: "Кіру",
    phone: "Телефон нөмірі",
    password: "Құпия сөз",
    login: "Кіру",
    noAccount: "Аккаунт жоқ па?",
    register: "Тіркелу",
    error: "Қате логин немесе пароль",
  },
  ru: {
    title: "Вход",
    phone: "Номер телефона",
    password: "Пароль",
    login: "Войти",
    noAccount: "Нет аккаунта?",
    register: "Зарегистрироваться",
    error: "Неверный логин или пароль",
  },
};

export default function LoginPage() {
  const router = useRouter();
  const [lang, setLang] = useState<"kz" | "ru">("kz");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const t = translations[lang];

  const handleLogin = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ username: phone, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || t.error);
        return;
      }
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("role", data.role);
      if (data.role === "admin") {
        router.push("/admin");
      } else {
        router.push("/dashboard");
      }
    } catch {
      setError(t.error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh", display: "flex", alignItems: "center",
      justifyContent: "center", background: "#f5f5f5", fontFamily: "sans-serif"
    }}>
      <div style={{
        background: "white", borderRadius: 16, padding: 32,
        width: "100%", maxWidth: 380, boxShadow: "0 4px 20px rgba(0,0,0,0.1)"
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
          <h2 style={{ margin: 0, fontSize: 22 }}>⛽ {t.title}</h2>
          <button onClick={() => setLang(lang === "kz" ? "ru" : "kz")}
            style={{ padding: "4px 12px", borderRadius: 20, border: "1px solid #ccc", cursor: "pointer" }}>
            {lang === "kz" ? "RU" : "ҚЗ"}
          </button>
        </div>

        <input
          placeholder={t.phone}
          value={phone}
          onChange={e => setPhone(e.target.value)}
          style={{ width: "100%", padding: 12, marginBottom: 12, borderRadius: 8, border: "1px solid #ddd", boxSizing: "border-box", fontSize: 15 }}
        />
        <input
          type="password"
          placeholder={t.password}
          value={password}
          onChange={e => setPassword(e.target.value)}
          onKeyDown={e => e.key === "Enter" && handleLogin()}
          style={{ width: "100%", padding: 12, marginBottom: 16, borderRadius: 8, border: "1px solid #ddd", boxSizing: "border-box", fontSize: 15 }}
        />

        {error && <div style={{ color: "red", marginBottom: 12, fontSize: 14 }}>{error}</div>}

        <button onClick={handleLogin} disabled={loading} style={{
          width: "100%", padding: 12, background: "#22c55e", color: "white",
          border: "none", borderRadius: 8, cursor: "pointer", fontSize: 16, fontWeight: "bold"
        }}>
          {loading ? "..." : t.login}
        </button>

        <div style={{ textAlign: "center", marginTop: 16, fontSize: 14 }}>
          {t.noAccount}{" "}
          <span onClick={() => router.push("/register")}
            style={{ color: "#22c55e", cursor: "pointer", fontWeight: "bold" }}>
            {t.register}
          </span>
        </div>
      </div>
    </div>
  );
}