"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

const translations = {
  kz: {
    title: "Жеке кабинет",
    myStation: "Менің станциям",
    status: "Статус",
    update: "Жаңарту",
    logout: "Шығу",
    green: "Газ бар",
    yellow: "Газ аз",
    red: "Газ жоқ",
    updated: "Жаңартылды!",
  },
  ru: {
    title: "Личный кабинет",
    myStation: "Моя станция",
    status: "Статус",
    update: "Обновить",
    logout: "Выйти",
    green: "Газ есть",
    yellow: "Газ мало",
    red: "Газа нет",
    updated: "Обновлено!",
  },
};

const statusColors: Record<string, string> = {
  green: "#22c55e",
  yellow: "#eab308",
  red: "#ef4444",
};

export default function DashboardPage() {
  const router = useRouter();
  const [lang, setLang] = useState<"kz" | "ru">("kz");
  const [user, setUser] = useState<any>(null);
  const [station, setStation] = useState<any>(null);
  const [selectedStatus, setSelectedStatus] = useState("green");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const t = translations[lang];

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) { router.push("/login"); return; }

    fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => { if (!r.ok) { router.push("/login"); return null; } return r.json(); })
      .then(data => {
        if (!data) return;
        setUser(data);
        return fetch(`${process.env.NEXT_PUBLIC_API_URL}/stations`);
      })
      .then(r => r?.json())
      .then(stations => {
        if (!stations || !user) return;
        const mine = stations.find((s: any) => s.id === user.station_id);
        if (mine) { setStation(mine); setSelectedStatus(mine.status); }
      });
  }, []);

  useEffect(() => {
    if (!user) return;
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/stations`)
      .then(r => r.json())
      .then(stations => {
        const mine = stations.find((s: any) => s.id === user.station_id);
        if (mine) { setStation(mine); setSelectedStatus(mine.status); }
      });
  }, [user]);

  const handleUpdate = async () => {
    const token = localStorage.getItem("token");
    setLoading(true);
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/stations/${station.id}/update`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ status: selectedStatus }),
      });
      setStation({ ...station, status: selectedStatus });
      setSuccess(true);
      setTimeout(() => setSuccess(false), 2000);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    router.push("/login");
  };

  if (!user || !station) return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ fontSize: 18 }}>⏳ Загрузка...</div>
    </div>
  );

  return (
    <div style={{ minHeight: "100vh", background: "#f5f5f5", fontFamily: "sans-serif" }}>
      {/* Header */}
      <div style={{ background: "white", padding: "16px 24px", display: "flex", justifyContent: "space-between", alignItems: "center", boxShadow: "0 2px 8px rgba(0,0,0,0.08)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 20, fontWeight: "bold" }}>⛽ {t.title}</span>
        </div>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <button onClick={() => setLang(lang === "kz" ? "ru" : "kz")}
            style={{ padding: "4px 12px", borderRadius: 20, border: "1px solid #ccc", cursor: "pointer" }}>
            {lang === "kz" ? "RU" : "ҚЗ"}
          </button>
          <button onClick={handleLogout}
            style={{ padding: "6px 16px", borderRadius: 8, background: "#fee2e2", border: "none", color: "#dc2626", cursor: "pointer", fontWeight: "bold" }}>
            {t.logout}
          </button>
        </div>
      </div>

      {/* Content */}
      <div style={{ maxWidth: 480, margin: "40px auto", padding: "0 16px" }}>
        <div style={{ background: "white", borderRadius: 16, padding: 28, boxShadow: "0 4px 20px rgba(0,0,0,0.08)" }}>
          <h3 style={{ margin: "0 0 20px", fontSize: 18 }}>📍 {t.myStation}</h3>

          <div style={{ fontSize: 22, fontWeight: "bold", marginBottom: 8 }}>{station.name}</div>

          {/* Текущий статус */}
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 24 }}>
            <div style={{ width: 12, height: 12, borderRadius: "50%", background: statusColors[station.status] || "#a855f7" }} />
            <span style={{ color: "#666" }}>
              {station.status === "green" ? t.green : station.status === "yellow" ? t.yellow : t.red}
            </span>
          </div>

          {/* Выбор нового статуса */}
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 14, color: "#888", marginBottom: 10 }}>{t.status}:</div>
            <div style={{ display: "flex", gap: 10 }}>
              {(["green", "yellow", "red"] as const).map(s => (
                <button key={s} onClick={() => setSelectedStatus(s)}
                  style={{
                    flex: 1, padding: 12, borderRadius: 10, border: "2px solid",
                    borderColor: selectedStatus === s ? statusColors[s] : "#e5e7eb",
                    background: selectedStatus === s ? statusColors[s] + "22" : "white",
                    cursor: "pointer", fontWeight: "bold", fontSize: 13,
                    color: selectedStatus === s ? statusColors[s] : "#666",
                  }}>
                  {s === "green" ? `🟢 ${t.green}` : s === "yellow" ? `🟡 ${t.yellow}` : `🔴 ${t.red}`}
                </button>
              ))}
            </div>
          </div>

          <button onClick={handleUpdate} disabled={loading}
            style={{ width: "100%", padding: 14, background: "#22c55e", color: "white", border: "none", borderRadius: 10, cursor: "pointer", fontSize: 16, fontWeight: "bold" }}>
            {loading ? "..." : success ? `✅ ${t.updated}` : t.update}
          </button>
        </div>

        <div style={{ textAlign: "center", marginTop: 16 }}>
          <span onClick={() => router.push("/")}
            style={{ color: "#22c55e", cursor: "pointer", fontSize: 14 }}>
            ← Картаға оралу / Вернуться на карту
          </span>
        </div>
      </div>
    </div>
  );
}