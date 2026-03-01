"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AdminPage() {
  const router = useRouter();
  const [users, setUsers] = useState<any[]>([]);
  const [stations, setStations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"pending" | "approved">("pending");

  const token = typeof window !== "undefined" ? localStorage.getItem("token") : "";

  useEffect(() => {
    const role = localStorage.getItem("role");
    if (role !== "admin") { router.push("/login"); return; }
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    const [usersRes, stationsRes] = await Promise.all([
      fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/users`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      }),
      fetch(`${process.env.NEXT_PUBLIC_API_URL}/stations`),
    ]);
    setUsers(await usersRes.json());
    setStations(await stationsRes.json());
    setLoading(false);
  };

  const approve = async (id: number) => {
    await fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/users/${id}/approve`, {
      method: "POST",
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
    });
    loadData();
  };

  const reject = async (id: number) => {
    await fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/users/${id}/reject`, {
      method: "POST",
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
    });
    loadData();
  };

  const getStationName = (id: number) => stations.find(s => s.id === id)?.name || "—";

  const pending = users.filter(u => !u.is_approved);
  const approved = users.filter(u => u.is_approved);
  const displayed = tab === "pending" ? pending : approved;

  const statusColors: Record<string, string> = {
    green: "#22c55e", yellow: "#eab308", red: "#ef4444", purple: "#a855f7",
  };

  return (
    <div style={{ minHeight: "100vh", background: "#f5f5f5", fontFamily: "sans-serif" }}>
      {/* Header */}
      <div style={{ background: "white", padding: "16px 24px", display: "flex", justifyContent: "space-between", alignItems: "center", boxShadow: "0 2px 8px rgba(0,0,0,0.08)" }}>
        <span style={{ fontSize: 20, fontWeight: "bold" }}>⛽ Админ панель</span>
        <div style={{ display: "flex", gap: 12 }}>
          <button onClick={() => router.push("/")}
            style={{ padding: "6px 16px", borderRadius: 8, border: "1px solid #ccc", background: "white", cursor: "pointer" }}>
            🗺 Карта
          </button>
          <button onClick={() => { localStorage.clear(); router.push("/login"); }}
            style={{ padding: "6px 16px", borderRadius: 8, background: "#fee2e2", border: "none", color: "#dc2626", cursor: "pointer", fontWeight: "bold" }}>
            Выйти
          </button>
        </div>
      </div>

      <div style={{ maxWidth: 800, margin: "32px auto", padding: "0 16px" }}>

        {/* Статистика */}
        <div style={{ display: "flex", gap: 16, marginBottom: 24 }}>
          {[
            { label: "Ожидают", value: pending.length, color: "#f59e0b" },
            { label: "Одобрены", value: approved.length, color: "#22c55e" },
            { label: "Станций", value: stations.length, color: "#3b82f6" },
          ].map(stat => (
            <div key={stat.label} style={{ flex: 1, background: "white", borderRadius: 12, padding: 20, textAlign: "center", boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
              <div style={{ fontSize: 32, fontWeight: "bold", color: stat.color }}>{stat.value}</div>
              <div style={{ color: "#888", fontSize: 14 }}>{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Станции */}
        <div style={{ background: "white", borderRadius: 16, padding: 24, marginBottom: 24, boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
          <h3 style={{ margin: "0 0 16px" }}>📍 Станции</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {stations.map(s => (
              <div key={s.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 16px", background: "#f9f9f9", borderRadius: 8 }}>
                <span style={{ fontWeight: "bold" }}>{s.name}</span>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <div style={{ width: 10, height: 10, borderRadius: "50%", background: statusColors[s.status] }} />
                  <span style={{ fontSize: 13, color: "#666" }}>{s.hasOwner ? "✅ Владелец есть" : "❌ Без владельца"}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Пользователи */}
        <div style={{ background: "white", borderRadius: 16, padding: 24, boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
          <div style={{ display: "flex", gap: 0, marginBottom: 20, borderRadius: 10, overflow: "hidden", border: "1px solid #e5e7eb" }}>
            {(["pending", "approved"] as const).map(t2 => (
              <button key={t2} onClick={() => setTab(t2)}
                style={{ flex: 1, padding: 10, border: "none", cursor: "pointer", fontWeight: "bold", fontSize: 14,
                  background: tab === t2 ? "#22c55e" : "white",
                  color: tab === t2 ? "white" : "#666" }}>
                {t2 === "pending" ? `⏳ Ожидают (${pending.length})` : `✅ Одобрены (${approved.length})`}
              </button>
            ))}
          </div>

          {loading ? (
            <div style={{ textAlign: "center", padding: 40, color: "#888" }}>Загрузка...</div>
          ) : displayed.length === 0 ? (
            <div style={{ textAlign: "center", padding: 40, color: "#888" }}>
              {tab === "pending" ? "Нет заявок" : "Нет одобренных"}
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {displayed.map(u => (
                <div key={u.id} style={{ padding: 16, background: "#f9f9f9", borderRadius: 10, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <div style={{ fontWeight: "bold", fontSize: 16 }}>{u.name}</div>
                    <div style={{ color: "#888", fontSize: 13 }}>📞 {u.phone}</div>
                    <div style={{ color: "#888", fontSize: 13 }}>📍 {getStationName(u.station_id)}</div>
                    <div style={{ color: "#aaa", fontSize: 12 }}>{new Date(u.created_at).toLocaleString()}</div>
                  </div>
                  {tab === "pending" && (
                    <div style={{ display: "flex", gap: 8 }}>
                      <button onClick={() => approve(u.id)}
                        style={{ padding: "8px 16px", background: "#22c55e", color: "white", border: "none", borderRadius: 8, cursor: "pointer", fontWeight: "bold" }}>
                        ✅
                      </button>
                      <button onClick={() => reject(u.id)}
                        style={{ padding: "8px 16px", background: "#ef4444", color: "white", border: "none", borderRadius: 8, cursor: "pointer", fontWeight: "bold" }}>
                        ❌
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}