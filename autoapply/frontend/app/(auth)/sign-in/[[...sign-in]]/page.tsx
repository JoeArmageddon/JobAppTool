import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <SignIn
        appearance={{
          variables: {
            colorBackground: "#12121a",
            colorText: "#f8fafc",
            colorPrimary: "#6366f1",
            colorInputBackground: "#1e1e2e",
            colorInputText: "#f8fafc",
          },
        }}
      />
    </div>
  );
}
