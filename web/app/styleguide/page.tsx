import { Badge, StatusBadge, UrgencyBadge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Input } from "../../components/ui/Input";
import { Table, type TableColumn } from "../../components/ui/Table";
import { TextArea } from "../../components/ui/TextArea";
import { Toast } from "../../components/ui/Toast";
import { VitalsLine } from "../../components/ui/VitalsLine";

/**
 * Static style-guide page — Build Plan Chunk 4 "done when": renders
 * every component in every state with no real data behind it. Not
 * linked from any portal nav; visited directly at /styleguide.
 */

const COLOR_TOKENS: { name: string; varName: string }[] = [
  { name: "Ink", varName: "--color-ink" },
  { name: "Paper", varName: "--color-paper" },
  { name: "Sage", varName: "--color-sage" },
  { name: "Amber", varName: "--color-amber" },
  { name: "Coral", varName: "--color-coral" },
  { name: "Slate", varName: "--color-slate" },
];

interface SampleRow {
  id: number;
  time: string;
  patient: string;
  urgency: "Low" | "Medium" | "High";
}

const SAMPLE_ROWS: SampleRow[] = [
  { id: 1, time: "09:00", patient: "Riya Sharma", urgency: "High" },
  { id: 2, time: "09:20", patient: "Arjun Nair", urgency: "Low" },
  { id: 3, time: "10:00", patient: "Priya Iyer", urgency: "Medium" },
];

const SAMPLE_COLUMNS: TableColumn<SampleRow>[] = [
  { key: "time", header: "Time", render: (r) => r.time },
  { key: "patient", header: "Patient", render: (r) => r.patient },
  { key: "urgency", header: "Urgency", render: (r) => <UrgencyBadge level={r.urgency} /> },
];

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="styleguide-section">
      <h2>{title}</h2>
      {children}
    </section>
  );
}

export default function StyleGuidePage() {
  return (
    <main className="page">
      <h1>Design System — Style Guide</h1>
      <p>
        Chunk 4 deliverable: every base component in every state, with no real data behind it.
        Tokens come from Frontend Design Document §2.
      </p>

      <Section title="Color">
        <div className="styleguide-row">
          {COLOR_TOKENS.map((token) => (
            <div className="styleguide-swatch" key={token.varName}>
              <div
                className="styleguide-swatch-color"
                style={{ background: `var(${token.varName})` }}
              />
              <div className="styleguide-swatch-label">
                {token.name}
                <br />
                <code>{token.varName}</code>
              </div>
            </div>
          ))}
        </div>
      </Section>

      <Section title="Typography">
        <h1 style={{ margin: 0 }}>Display — Source Serif 4 (Aa 123)</h1>
        <p style={{ fontFamily: "var(--font-body)", margin: "0.5rem 0" }}>
          Body / UI — Inter. All body text, form labels, buttons, nav.
        </p>
        <p style={{ fontFamily: "var(--font-mono)", margin: 0 }}>
          Data / Utility — IBM Plex Mono — 09:40 · APT-0142 · 04:58
        </p>
      </Section>

      <Section title="Vitals line divider">
        <p>Static, per status tone:</p>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", maxWidth: 320 }}>
          <VitalsLine tone="ink" aria-label="Vitals line, ink" />
          <VitalsLine tone="sage" aria-label="Vitals line, sage" />
          <VitalsLine tone="amber" aria-label="Vitals line, amber" />
          <VitalsLine tone="coral" aria-label="Vitals line, coral" />
        </div>
        <p style={{ marginTop: "0.75rem" }}>One-shot draw-in (booking confirm / post-visit reveal):</p>
        <div style={{ maxWidth: 320 }}>
          <VitalsLine tone="sage" animate aria-label="Vitals line draw-in" />
        </div>
      </Section>

      <Section title="Button">
        <div className="styleguide-row">
          <Button variant="primary">Confirm appointment</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="destructive">Cancel appointment</Button>
          <Button variant="primary" disabled>
            Disabled
          </Button>
        </div>
        <div className="styleguide-row">
          <Button size="sm">Small</Button>
          <Button size="md">Medium</Button>
          <Button size="lg">Large</Button>
        </div>
      </Section>

      <Section title="Input">
        <div className="styleguide-row" style={{ alignItems: "flex-start" }}>
          <div style={{ width: 260 }}>
            <Input label="Email" placeholder="you@example.com" />
          </div>
          <div style={{ width: 260 }}>
            <Input label="Phone" placeholder="+91 98765 43210" hint="Used for appointment reminders" />
          </div>
          <div style={{ width: 260 }}>
            <Input label="Password" type="password" error="Password must be at least 8 characters" />
          </div>
          <div style={{ width: 260 }}>
            <Input label="Disabled" disabled placeholder="Not editable" />
          </div>
        </div>
      </Section>

      <Section title="TextArea">
        <div className="styleguide-row" style={{ alignItems: "flex-start" }}>
          <div style={{ width: 320 }}>
            <TextArea label="Symptoms" placeholder="Tell us what's going on…" />
          </div>
          <div style={{ width: 320 }}>
            <TextArea label="Clinical notes" error="Clinical notes can't be empty" />
          </div>
        </div>
      </Section>

      <Section title="Card">
        <div className="styleguide-row" style={{ alignItems: "flex-start" }}>
          <Card style={{ width: 260 }}>
            <strong>Default card</strong>
            <p style={{ margin: "0.5rem 0 0" }}>No shadow — the ordinary state.</p>
          </Card>
          <Card style={{ width: 260 }} elevated>
            <strong>Elevated card</strong>
            <p style={{ margin: "0.5rem 0 0" }}>Hold countdown / modal dialogs only.</p>
          </Card>
        </div>
      </Section>

      <Section title="Badge — urgency">
        <div className="styleguide-row">
          <UrgencyBadge level="Low" />
          <UrgencyBadge level="Medium" />
          <UrgencyBadge level="High" />
        </div>
      </Section>

      <Section title="Badge — status">
        <div className="styleguide-row">
          <StatusBadge status="confirmed" />
          <StatusBadge status="pending" />
          <StatusBadge status="held" />
          <StatusBadge status="cancelled" />
          <StatusBadge status="completed" />
          <StatusBadge status="failed" />
        </div>
        <div className="styleguide-row">
          <Badge tone="ink">Custom ink badge</Badge>
        </div>
      </Section>

      <Section title="Toast">
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", maxWidth: 420 }}>
          <Toast variant="success" title="Appointment confirmed">
            We&apos;ve sent a confirmation email and added it to your calendar.
          </Toast>
          <Toast variant="failed" title="We couldn't reach the calendar service">
            Your appointment is still booked. We&apos;ll add the calendar event automatically once
            it&apos;s back.
          </Toast>
          <Toast variant="info" title="AI summary unavailable">
            Read the patient&apos;s notes below.
          </Toast>
        </div>
      </Section>

      <Section title="Table — default">
        <Table columns={SAMPLE_COLUMNS} rows={SAMPLE_ROWS} rowKey={(r) => r.id} />
      </Section>

      <Section title="Table — row expanded">
        <Table
          columns={SAMPLE_COLUMNS}
          rows={SAMPLE_ROWS}
          rowKey={(r) => r.id}
          expandedRowKeys={[SAMPLE_ROWS[0].id]}
        />
      </Section>

      <Section title="Table — empty">
        <Table
          columns={SAMPLE_COLUMNS}
          rows={[]}
          rowKey={(r) => r.id}
          emptyTitle="No appointments today"
          emptyAction={<Button size="sm">Find a doctor</Button>}
        />
      </Section>

      <Section title="App shell / nav — per portal">
        <p>Portal nav bars (preview only — the live shell wraps each role&apos;s pages):</p>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          {(["Patient", "Doctor", "Admin"] as const).map((portal) => (
            <div className="app-nav" key={portal} style={{ borderRadius: "var(--radius-control)" }}>
              <span className="app-nav-brand">
                Healthcare Manager <span className="app-nav-portal">{portal}</span>
              </span>
              <nav className="app-nav-links">
                <span className="app-nav-link" data-active="true">
                  Home
                </span>
                <span className="app-nav-link">Second item</span>
              </nav>
              <Button variant="ghost" size="sm">
                Log out
              </Button>
            </div>
          ))}
        </div>
      </Section>
    </main>
  );
}
