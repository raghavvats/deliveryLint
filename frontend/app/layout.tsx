import "./globals.css";

import { ToastHost } from "@/components/ui/toast-host";

export const metadata = {
  title: "DeliveryLint",
  description: "Implementation document review assistant",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ToastHost>{children}</ToastHost>
      </body>
    </html>
  );
}
