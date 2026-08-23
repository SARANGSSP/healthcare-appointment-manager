import "../styles/globals.css";

export const metadata = {
  title: "Healthcare Appointment & Follow-up Manager",
  description: "Patient, Doctor, and Admin appointment portal",
};

// Frontend Design Document §2.2: Source Serif 4 (display), Inter
// (body/UI), IBM Plex Mono (data/utility — timestamps, slot times,
// countdowns). Loaded once here so every portal shares the same
// three typefaces from Chunk 4 onward.
const FONT_HREF =
  "https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link rel="stylesheet" href={FONT_HREF} />
      </head>
      <body>{children}</body>
    </html>
  );
}
