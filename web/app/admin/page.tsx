"use client";

import { useRouter } from "next/navigation";

import { clearSession } from "../../lib/api";
import { useRequireRole } from "../../lib/useRequireRole";

// Real content (doctors table, notifications, overview) is Chunk 5
// onward per Frontend Design Document §3.3.
export default function AdminHome() {
  const ready = useRequireRole("admin");
  const router = useRouter();

  if (!ready) return null;

  return (
    <main style={{ fontFamily: "sans-serif", padding: "2rem" }}>
      <h1>Admin home</h1>
      <p>You&apos;re logged in as an admin. Doctor management lands in a later chunk.</p>
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
