"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

// Chunk 1 scope only: prove the page is live on a public URL and can
// optionally reach the API's health endpoint. Role-based routing,
// the shared component library, and real screens land in Chunks 3-4+.
export default function Home() {
  const [apiStatus, setApiStatus] = useState<string>("not checked");

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    if (!apiUrl) {
      setApiStatus("NEXT_PUBLIC_API_URL not set");
      return;
    }
    fetch(`${apiUrl}/api/v1/health`)
      .then((res) => res.json())
      .then((data) => setApiStatus(data.status === "ok" ? "connected" : "unexpected response"))
      .catch(() => setApiStatus("unreachable"));
  }, []);

  return (
    <main style={{ fontFamily: "sans-serif", padding: "2rem" }}>
      <h1>Healthcare Appointment &amp; Follow-up Manager</h1>
      <p>Repo scaffold is live (Chunk 1).</p>
      <p>API status: {apiStatus}</p>
      <p>
        <Link href="/login">Log in</Link> · <Link href="/register">Register</Link>
      </p>
    </main>
  );
}
