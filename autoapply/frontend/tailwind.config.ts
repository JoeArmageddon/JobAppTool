import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: { "2xl": "1400px" },
    },
    extend: {
      colors: {
        background: "#0a0a0f",
        surface: "#12121a",
        primary: {
          DEFAULT: "#6366f1",
          foreground: "#f8fafc",
        },
        success: "#10b981",
        danger: "#f43f5e",
        warning: "#f59e0b",
        border: "rgba(99, 102, 241, 0.15)",
        foreground: "#f8fafc",
        muted: {
          DEFAULT: "#94a3b8",
          foreground: "#94a3b8",
        },
        card: {
          DEFAULT: "#12121a",
          foreground: "#f8fafc",
        },
        popover: {
          DEFAULT: "#12121a",
          foreground: "#f8fafc",
        },
        secondary: {
          DEFAULT: "#1e1e2e",
          foreground: "#f8fafc",
        },
        accent: {
          DEFAULT: "#1e1e2e",
          foreground: "#f8fafc",
        },
        destructive: {
          DEFAULT: "#f43f5e",
          foreground: "#f8fafc",
        },
        input: "#1e1e2e",
        ring: "#6366f1",
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)"],
        mono: ["var(--font-geist-mono)"],
      },
      borderRadius: {
        lg: "0.5rem",
        md: "calc(0.5rem - 2px)",
        sm: "calc(0.5rem - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "spin-slow": {
          from: { transform: "rotate(0deg)" },
          to: { transform: "rotate(360deg)" },
        },
        "pulse-glow": {
          "0%, 100%": { boxShadow: "0 0 8px rgba(99,102,241,0.3)" },
          "50%": { boxShadow: "0 0 20px rgba(99,102,241,0.7)" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "spin-slow": "spin-slow 8s linear infinite",
        "pulse-glow": "pulse-glow 2s ease-in-out infinite",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
