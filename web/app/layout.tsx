export const metadata = {
  title: "Healthcare Appointment & Follow-up Manager",
  description: "Patient, Doctor, and Admin appointment portal",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
