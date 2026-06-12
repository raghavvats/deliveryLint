export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "system-ui, sans-serif", margin: "2rem", maxWidth: 960 }}>
        <header style={{ marginBottom: "2rem" }}>
          <h1 style={{ margin: 0 }}>DeliveryLint</h1>
          <p style={{ color: "#555" }}>Implementation document review assistant</p>
        </header>
        {children}
      </body>
    </html>
  );
}
