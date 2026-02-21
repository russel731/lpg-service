"use client";

import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";

interface Props {
  stations: any[];
}

// фикс иконок leaflet
const icon = new L.Icon({
  iconUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

export default function Map({ stations }: Props) {
  return (
    <MapContainer
      center={[55.75, 37.61]}
      zoom={11}
      style={{ height: "600px", width: "100%" }}
    >
      <TileLayer
        attribution="© OpenStreetMap"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {stations.map((station) => (
        <Marker
          key={station.id}
          position={[station.lat, station.lng]}
          icon={icon}
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
  );
}