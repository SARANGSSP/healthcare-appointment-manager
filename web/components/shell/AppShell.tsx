"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { Button } from "../ui/Button";
import type { Role } from "../../lib/api";

export interface NavItem {
  label: string;
  href: string;
}

const PORTAL_LABEL: Record<Role, string> = {
  patient: "Patient",
  doctor: "Doctor",
  admin: "Admin",
};

/**
 * Information architecture per portal — Frontend Design Document §3.
 * Routes beyond each portal's home page land in later chunks; the
 * nav is scaffolded now so Chunk 4 delivers "app shell/nav per
 * portal" per the Build Plan, and later chunks only add pages, not
 * navigation structure.
 */
const PORTAL_NAV: Record<Role, NavItem[]> = {
  patient: [
    { label: "Home", href: "/patient" },
    { label: "Search", href: "/patient/search" },
    { label: "Account", href: "/patient/account" },
  ],
  doctor: [
    { label: "Today", href: "/doctor" },
    { label: "Schedule", href: "/doctor/schedule" },
  ],
  admin: [
    { label: "Doctors", href: "/admin" },
    { label: "Notifications", href: "/admin/notifications" },
    { label: "Overview", href: "/admin/overview" },
  ],
};

export interface AppShellProps {
  role: Role;
  onLogout?: () => void;
  /** Patient portal is intentionally narrower and linear (§3.1). */
  narrow?: boolean;
  children: ReactNode;
}

/**
 * Shared app shell + nav — Build Plan Chunk 4.
 * One shell across all three portals; only the nav items and the
 * narrow/wide content column differ per role (Frontend Design
 * Document §3.1-§3.3, §2.3).
 */
export function AppShell({ role, onLogout, narrow = false, children }: AppShellProps) {
  const pathname = usePathname();
  const navItems = PORTAL_NAV[role];

  return (
    <div className="app-shell">
      <header className="app-nav">
        <Link href={`/${role}`} className="app-nav-brand">
          Healthcare Manager <span className="app-nav-portal">{PORTAL_LABEL[role]}</span>
        </Link>
        <nav className="app-nav-links" aria-label={`${PORTAL_LABEL[role]} portal navigation`}>
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="app-nav-link"
              data-active={pathname === item.href}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        {onLogout && (
          <Button variant="ghost" size="sm" onClick={onLogout}>
            Log out
          </Button>
        )}
      </header>
      <main className={narrow ? "app-main app-main-narrow" : "app-main page"}>{children}</main>
    </div>
  );
}
