"use client";

import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

const VALID_STATUSES = ["green", "yellow", "red", "purple"];

function createIcon(status: string) {
  const safe = VALID_STATUSES.includes(status) ? status : "purple";
  return L.icon({
    iconUrl: `/markers/${safe}.png`,
    iconSize: [36, 36],
    iconAnchor: [18, 36],
    popupAnchor: [0, -36],
  });
}

type Station = {
  id: number;
  name?: string;
  lat?: number;
  lng?: number;
  lon?: number;
  latitude?: number;
  longitude?: number;
  status?: string;
  lastUpdated?: string;
};

export default function Map({ stations = [] }: { stations: Station[] }) {
  const center: [number, number] = [43.65, 51.17];

  const valid = stations
    .map((s) => ({
      ...s,
      lat: s.latitude ?? s.lat,
      lng: s.longitude ?? s.lng ?? s.lon,
    }))
    .filter((s) => typeof s.lat === "number" && typeof s.lng === "number");

  return (
    <MapContainer center={center} zoom={12} style={{ height: "100%", width: "100%" }}>
      <TileLayer
        attribution="© OpenStreetMap"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {valid.map((s) => (
        <Marker
          key={s.id}
          position={[s.lat!, s.lng!]}
          icon={createIcon(s.status || "purple")}
        >
          <Popup>
            <div style={{ minWidth: 160 }}>
              <strong style={{ fontSize: 14 }}>{s.name || "Станция"}</strong>
              <hr style={{ margin: "6px 0" }} />
              <div>
                Статус: <strong>{
                  s.status === "green" ? "🟢 Газ есть" :
                  s.status === "yellow" ? "🟡 Газ мало" :
                  s.status === "red" ? "🔴 Газа нет" :
                  "🟣 Нет данных"
                }</strong>
              </div>
              <div style={{ fontSize: 12, color: "#888", marginTop: 4 }}>
                {s.lastUpdated
                  ? `🕐 ${new Date(s.lastUpdated).toLocaleString("ru-RU")}`
                  : "🕐 Нет данных об обновлении"}
              </div>
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}