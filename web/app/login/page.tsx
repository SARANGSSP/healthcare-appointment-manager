"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Input } from "../../components/ui/Input";
import { Toast } from "../../components/ui/Toast";
import { VitalsLine } from "../../components/ui/VitalsLine";
import { login, roleHomePath, storeSession } from "../../lib/api";

// Chunk 3 built the flow; Chunk 4 restyles it with the shared
// component library / design tokens (see the note this comment used
// to carry) — every screen built before Chunk 4 gets this pass.
export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const auth = await login({ email, password });
      storeSession(auth);
      router.push(roleHomePath(auth.role));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't log in. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="page app-main-narrow">
      <VitalsLine tone="ink" />
      <Card>
        <h1>Log in</h1>
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <Input
            type="email"
            label="Email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Input
            type="password"
            label="Password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {error && (
            <Toast variant="failed" title="Couldn't log in">
              {error}
            </Toast>
          )}
          <Button type="submit" disabled={submitting}>
            {submitting ? "Logging in…" : "Log in"}
          </Button>
        </form>
        <p style={{ marginTop: "1rem", marginBottom: 0 }}>
          Don&apos;t have an account? <Link href="/register">Register</Link>
        </p>
      </Card>
    </main>
  );
}
