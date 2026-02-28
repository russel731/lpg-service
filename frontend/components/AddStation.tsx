"use client";

import { useState } from "react";

export default function AddStation({ onAdd }: any) {
  const [active, setActive] = useState(false);

  return (
    <>
      <button
        onClick={() => setActive(!active)}
        className="absolute top-4 right-4 z-50 bg-green-600 text-white px-4 py-2 rounded-xl shadow-lg"
      >
        + Добавить АГЗС
      </button>

      {active && (
        <div className="absolute top-16 right-4 z-50 bg-white p-4 rounded-xl shadow-xl">
          <p>Нажмите на карту, чтобы выбрать место</p>
        </div>
      )}
    </>
  );
}