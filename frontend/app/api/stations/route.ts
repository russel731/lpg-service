export async function GET() {
  try {
    const res = await fetch(
      "https://nonconversationally-vestibular-pia.ngrok-free.dev/stations",
      { cache: "no-store" }
    );

    const data = await res.json();

    return Response.json(data);
  } catch (error) {
    return Response.json({ error: "Failed to fetch stations" }, { status: 500 });
  }
}