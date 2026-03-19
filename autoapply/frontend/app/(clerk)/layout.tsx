import { ClerkProvider } from "@clerk/nextjs";

export default function ClerkLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider
      appearance={{
        variables: {
          colorBackground: "#12121a",
          colorText: "#f8fafc",
          colorPrimary: "#6366f1",
          colorInputBackground: "#1e1e2e",
          colorInputText: "#f8fafc",
        },
      }}
    >
      {children}
    </ClerkProvider>
  );
}
