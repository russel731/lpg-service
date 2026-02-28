"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";

const Map = dynamic(() => import("./map"), { ssr: false });

const translations = {
  kz: {
    title: "АГЗС картасы",
    addStation: "Станция қосу",
    name: "Атауы",
    lat: "Ендік",
    lng: "Бойлық",
    status: "Мәртебесі",
    save: "Сақтау",
    cancel: "Болдырмау",
    available: "Газ бар",
    low: "Газ аз",
    unavailable: "Газ жоқ",
    unknown: "Белгісіз",
  },
  ru: {
    title: "Карта АГЗС",
    addStation: "Добавить станцию",
    name: "Название",
    lat: "Широта",
    lng: "Долгота",
    status: "Статус",
    save: "Сохранить",
    cancel: "Отмена",
    available: "Газ есть",
    low: "Газ мало",
    unavailable: "Газа нет",
    unknown: "Неизвестно",
  },
};

export default function Page() {
  const [stations, setStations] = useState([]);
  const [lang, setLang] = useState<"kz" | "ru">("kz");
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ name: "", lat: "", lng: "", status: "green" });

  const t = translations[lang];

  useEffect(() => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL;
    if (!API_URL) return;
    fetch(`${API_URL}/stations`)
      .then(res => res.json())
      .then(data => setStations(data))
      .catch(err => console.error(err));
  }, []);

  const handleAdd = () => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL;
    if (!API_URL) return;
    fetch(`${API_URL}/stations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: form.name,
        lat: parseFloat(form.lat),
        lon: parseFloat(form.lng),
        status: form.status,
        lastUpdated: new Date().toISOString(),
      }),
    })
      .then(res => res.json())
      .then(newStation => {
        setStations(prev => [...prev, newStation]);
        setShowAdd(false);
        setForm({ name: "", lat: "", lng: "", status: "green" });
      })
      .catch(err => console.error(err));
  };

  return (
    <div style={{ height: "100vh", width: "100%", position: "relative", fontFamily: "sans-serif" }}>

      {/* Шапка */}
      <div style={{
        position: "absolute", top: 0, left: 0, right: 0, zIndex: 1000,
        background: "white", padding: "10px 16px",
        display: "flex", justifyContent: "space-between", alignItems: "center",
        boxShadow: "0 2px 8px rgba(0,0,0,0.15)"
      }}>
        <span style={{ fontWeight: "bold", fontSize: 18 }}>⛽ {t.title}</span>
        <button
          onClick={() => setLang(lang === "kz" ? "ru" : "kz")}
          style={{
            padding: "6px 14px", borderRadius: 20, border: "1px solid #ccc",
            cursor: "pointer", fontWeight: "bold", background: "#f5f5f5"
          }}
        >
          {lang === "kz" ? "RU" : "ҚЗ"}
        </button>
      </div>

      {/* Карта */}
      <Map stations={stations} />

      {/* Легенда */}
      <div style={{
        position: "absolute", bottom: 80, left: 12, zIndex: 1000,
        background: "white", borderRadius: 12, padding: "10px 14px",
        boxShadow: "0 2px 8px rgba(0,0,0,0.15)", fontSize: 13
      }}>
        <div>🟢 {t.available}</div>
        <div>🟡 {t.low}</div>
        <div>🔴 {t.unavailable}</div>
        <div>🟣 {t.unknown}</div>
      </div>

      {/* Нижняя навигация */}
      <div style={{
        position: "absolute", bottom: 0, left: 0, right: 0, zIndex: 1000,
        background: "white", display: "flex", justifyContent: "space-around",
        alignItems: "center", padding: "10px 0",
        boxShadow: "0 -2px 8px rgba(0,0,0,0.1)"
      }}>
        <button onClick={() => setShowAdd(false)} style={{ background: "none", border: "none", fontSize: 24, cursor: "pointer" }}>🗺️</button>
        <button
          onClick={() => setShowAdd(!showAdd)}
          style={{
            background: "#22c55e", border: "none", borderRadius: "50%",
            width: 52, height: 52, fontSize: 28, color: "white", cursor: "pointer",
            marginTop: -20, boxShadow: "0 4px 12px rgba(34,197,94,0.4)"
          }}
        >+</button>
        <button style={{ background: "none", border: "none", fontSize: 24, cursor: "pointer" }}>☰</button>
      </div>

      {/* Панель добавления */}
      {showAdd && (
        <div style={{
          position: "absolute", bottom: 70, left: 12, right: 12, zIndex: 1001,
          background: "white", borderRadius: 16, padding: 20,
          boxShadow: "0 4px 20px rgba(0,0,0,0.2)"
        }}>
          <h3 style={{ margin: "0 0 12px" }}>➕ {t.addStation}</h3>
          <input placeholder={t.name} value={form.name}
            onChange={e => setForm({ ...form, name: e.target.value })}
            style={{ width: "100%", padding: 8, marginBottom: 8, borderRadius: 8, border: "1px solid #ddd", boxSizing: "border-box" }} />
          <input placeholder={t.lat} value={form.lat}
            onChange={e => setForm({ ...form, lat: e.target.value })}
            style={{ width: "100%", padding: 8, marginBottom: 8, borderRadius: 8, border: "1px solid #ddd", boxSizing: "border-box" }} />
          <input placeholder={t.lng} value={form.lng}
            onChange={e => setForm({ ...form, lng: e.target.value })}
            style={{ width: "100%", padding: 8, marginBottom: 8, borderRadius: 8, border: "1px solid #ddd", boxSizing: "border-box" }} />
          <select value={form.status}
            onChange={e => setForm({ ...form, status: e.target.value })}
            style={{ width: "100%", padding: 8, marginBottom: 12, borderRadius: 8, border: "1px solid #ddd" }}>
            <option value="green">🟢 {t.available}</option>
            <option value="yellow">🟡 {t.low}</option>
            <option value="red">🔴 {t.unavailable}</option>
            <option value="purple">🟣 {t.unknown}</option>
          </select>
          <div style={{ display: "flex", gap: 8 }}>
            <button onClick={handleAdd} style={{
              flex: 1, padding: 10, background: "#22c55e", color: "white",
              border: "none", borderRadius: 8, cursor: "pointer", fontWeight: "bold"
            }}>{t.save}</button>
            <button onClick={() => setShowAdd(false)} style={{
              flex: 1, padding: 10, background: "#f5f5f5",
              border: "none", borderRadius: 8, cursor: "pointer"
            }}>{t.cancel}</button>
          </div>
        </div>
      )}
    </div>
  );
}