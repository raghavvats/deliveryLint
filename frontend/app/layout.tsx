import "./globals.css";

export const metadata = {
  title: "DeliveryLint",
  description: "Implementation document review assistant",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
