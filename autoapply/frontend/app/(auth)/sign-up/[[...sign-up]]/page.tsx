import { SignUp } from "@clerk/nextjs";

export default function SignUpPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <SignUp
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
