"use client";

import { useRouter } from "next/navigation";

import { clearSession } from "../../lib/api";
import { useRequireRole } from "../../lib/useRequireRole";

// Real content (today's queue, urgency badges) is Chunk 12 per
// Frontend Design Document §3.2.
export default function DoctorHome() {
  const ready = useRequireRole("doctor");
  const router = useRouter();

  if (!ready) return null;

  return (
    <main style={{ fontFamily: "sans-serif", padding: "2rem" }}>
      <h1>Doctor home</h1>
      <p>You&apos;re logged in as a doctor. Today&apos;s queue lands in a later chunk.</p>
      <button
        onClick={() => {
          clearSession();
          router.push("/login");
        }}
      >
        Log out
      </button>
    </main>
  );
}
