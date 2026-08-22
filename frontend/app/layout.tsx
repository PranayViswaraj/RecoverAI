import "./globals.css";

export const metadata = {
  title: "RecoverAI",
  description: "Autonomous Revenue Recovery Agent",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
