"use client";

import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { useEffect, useState } from "react";

// фикс иконок
delete (L.Icon.Default.prototype as any)._getIconUrl;

L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

type Station = {
  id: number;
  name: string;
  lat: number;
  lon: number;
};

export default function MapInner() {
  const [stations, setStations] = useState<Station[]>([]);

  useEffect(() => {
    async function loadStations() {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/stations`
        );
        const data = await res.json();
        setStations(data);
      } catch (e) {
        console.error(e);
      }
    }

    loadStations();
  }, []);

  return (
    <MapContainer
      center={[43.65, 51.16]}
      zoom={12}
      className="w-full h-full"
    >
      <TileLayer
        attribution="© OpenStreetMap"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {stations.map((s) => (
        <Marker key={s.id} position={[s.lat, s.lon]}>
          <Popup>{s.name}</Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}