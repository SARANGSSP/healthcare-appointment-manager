"use client";

import { useRouter } from "next/navigation";

import { clearSession } from "../../lib/api";
import { useRequireRole } from "../../lib/useRequireRole";

// Chunk 3's "done when": a patient lands here, empty, right after
// login/register. Real content ("upcoming appointment" + "Find a
// doctor") is Chunk 17 per Frontend Design Document §3.1.
export default function PatientHome() {
  const ready = useRequireRole("patient");
  const router = useRouter();

  if (!ready) return null;

  return (
    <main style={{ fontFamily: "sans-serif", padding: "2rem" }}>
      <h1>Patient home</h1>
      <p>You&apos;re logged in as a patient. Search and booking land in later chunks.</p>
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
