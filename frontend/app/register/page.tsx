"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

const translations = {
  kz: {
    title: "Тіркелу",
    name: "Аты-жөні",
    phone: "Телефон нөмірі",
    password: "Құпия сөз",
    station: "Станцияны таңдаңыз",
    submit: "Тіркелу",
    success: "Өтінім жіберілді! Модерация күтіңіз.",
    hasAccount: "Аккаунт бар ма?",
    login: "Кіру",
  },
  ru: {
    title: "Регистрация",
    name: "Имя",
    phone: "Номер телефона",
    password: "Пароль",
    station: "Выберите станцию",
    submit: "Зарегистрироваться",
    success: "Заявка отправлена! Ожидайте модерации.",
    hasAccount: "Уже есть аккаунт?",
    login: "Войти",
  },
};

export default function RegisterPage() {
  const router = useRouter();
  const [lang, setLang] = useState<"kz" | "ru">("kz");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [stationId, setStationId] = useState("");
  const [stations, setStations] = useState<any[]>([]);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const t = translations[lang];

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/stations`)
      .then(r => r.json())
      .then(data => setStations(data.filter((s: any) => !s.hasOwner)));
  }, []);

  const handleRegister = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, phone, password, station_id: parseInt(stationId) }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "Ошибка");
        return;
      }
      setSuccess(true);
      setTimeout(() => router.push("/login"), 3000);
    } catch {
      setError("Ошибка сети");
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

        {success ? (
          <div style={{ textAlign: "center", color: "#22c55e", fontSize: 16, padding: 20 }}>
            ✅ {t.success}
          </div>
        ) : (
          <>
            <input placeholder={t.name} value={name} onChange={e => setName(e.target.value)}
              style={{ width: "100%", padding: 12, marginBottom: 12, borderRadius: 8, border: "1px solid #ddd", boxSizing: "border-box", fontSize: 15 }} />
            <input placeholder={t.phone} value={phone} onChange={e => setPhone(e.target.value)}
              style={{ width: "100%", padding: 12, marginBottom: 12, borderRadius: 8, border: "1px solid #ddd", boxSizing: "border-box", fontSize: 15 }} />
            <input type="password" placeholder={t.password} value={password} onChange={e => setPassword(e.target.value)}
              style={{ width: "100%", padding: 12, marginBottom: 12, borderRadius: 8, border: "1px solid #ddd", boxSizing: "border-box", fontSize: 15 }} />

            <select value={stationId} onChange={e => setStationId(e.target.value)}
              style={{ width: "100%", padding: 12, marginBottom: 16, borderRadius: 8, border: "1px solid #ddd", boxSizing: "border-box", fontSize: 15 }}>
              <option value="">{t.station}</option>
              {stations.map(s => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>

            {error && <div style={{ color: "red", marginBottom: 12, fontSize: 14 }}>{error}</div>}

            <button onClick={handleRegister} disabled={loading || !name || !phone || !password || !stationId}
              style={{ width: "100%", padding: 12, background: "#22c55e", color: "white", border: "none", borderRadius: 8, cursor: "pointer", fontSize: 16, fontWeight: "bold", opacity: (!name || !phone || !password || !stationId) ? 0.6 : 1 }}>
              {loading ? "..." : t.submit}
            </button>

            <div style={{ textAlign: "center", marginTop: 16, fontSize: 14 }}>
              {t.hasAccount}{" "}
              <span onClick={() => router.push("/login")}
                style={{ color: "#22c55e", cursor: "pointer", fontWeight: "bold" }}>
                {t.login}
              </span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}