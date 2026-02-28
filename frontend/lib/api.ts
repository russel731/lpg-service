const API_URL =
  typeof window !== "undefined" &&
  window.location.hostname !== "localhost"
    ? "https://ТВОЙ-БУДУЩИЙ-ДОМЕН.com"
    : "http://localhost:8000";

export default API_URL;