"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import "leaflet/dist/leaflet.css";

type Station = {
  id: number;
  name: string;
  status: string;
  price?: number;
  latitude?: number;
  longitude?: number;
};

// динамическая загрузка leaflet (решает window is not defined)
const MapContainer = dynamic(
  async () => (await import("react-leaflet")).MapContainer,
  { ssr: false }
);

const TileLayer = dynamic(
  async () => (await import("react-leaflet")).TileLayer,
  { ssr: false }
);

const Marker = dynamic(
  async () => (await import("react-leaflet")).Marker,
  { ssr: false }
);

const Popup = dynamic(
  async () => (await import("react-leaflet")).Popup,
  { ssr: false }
);

export default function Map() {
  const [stations, setStations] = useState<Station[]>([]);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);

    fetch("http://127.0.0.1:8000/stations")
      .then((res) => res.json())
      .then((data) => setStations(data))
      .catch(() => console.log("Ошибка загрузки станций"));
  }, []);

  // важно: рендер только после монтирования (фикс Next + Leaflet)
  if (!mounted) return null;

  return (
    <div style={{ height: "600px", marginTop: "20px" }}>
      <MapContainer
        center={[55.75, 37.61]}
        zoom={10}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          attribution="&copy; OpenStreetMap"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {stations
          .filter(
            (station) =>
              station.latitude !== undefined &&
              station.longitude !== undefined
          )
          .map((station) => (
            <Marker
              key={station.id}
              position={[station.latitude!, station.longitude!]}
            >
              <Popup>
                <b>{station.name}</b>
                <br />
                Статус: {station.status}
                <br />
                Цена: {station.price ?? "Нет данных"}
              </Popup>
            </Marker>
          ))}
      </MapContainer>
    </div>
  );
}