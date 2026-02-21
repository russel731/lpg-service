import React, { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";

function LocationSelector({ setLocation }) {
  useMapEvents({
    click(e) {
      setLocation(e.latlng);
    },
  });
  return null;
}

function App() {
  const [stations, setStations] = useState([]);
  const [name, setName] = useState("");
  const [location, setLocation] = useState(null);

  const loadStations = () => {
    fetch("http://localhost:8000/stations/")
      .then((res) => res.json())
      .then(setStations);
  };

  useEffect(() => {
    loadStations();
  }, []);

  const addStation = async () => {
    if (!location || !name) {
      alert("Введите название и выберите точку на карте");
      return;
    }

    await fetch("http://localhost:8000/stations", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name,
        lat: location.lat,
        lng: location.lng,
      }),
    });

    setName("");
    setLocation(null);
    loadStations();
  };

  return (
    <div>
      <div style={{ padding: 10 }}>
        <input
          placeholder="Название станции"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <button onClick={addStation}>Добавить</button>
      </div>

      <div style={{ height: "90vh" }}>
        <MapContainer
          center={[43.238949, 76.889709]}
          zoom={10}
          style={{ height: "100%" }}
        >
          <TileLayer
            attribution="&copy; OpenStreetMap"
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <LocationSelector setLocation={setLocation} />

          {stations.map((station) => (
            <Marker key={station.id} position={[station.lat, station.lng]}>
              <Popup>{station.name}</Popup>
            </Marker>
          ))}

          {location && (
            <Marker position={[location.lat, location.lng]}>
              <Popup>Новая станция</Popup>
            </Marker>
          )}
        </MapContainer>
      </div>
    </div>
  );
}

export default App;