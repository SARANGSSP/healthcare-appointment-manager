"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { getStoredRole, Role } from "./api";

// Chunk 3's "role-aware redirect after login": each portal home page
// calls this with its own role. A mismatched or missing session
// bounces to /login rather than rendering role-inappropriate content.
export function useRequireRole(role: Role): boolean {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (getStoredRole() !== role) {
      router.replace("/login");
      return;
    }
    setReady(true);
  }, [role, router]);

  return ready;
}
