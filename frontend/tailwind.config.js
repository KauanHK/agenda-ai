/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        surface: "var(--surface)",
        "bg-muted": "var(--bg-muted)",
        text: "var(--text)",
        "text-dim": "var(--text-dim)",
        border: "var(--border)",
        primary: "var(--color-primary)",
        "primary-deep": "var(--color-primary-deep)",
        "primary-soft": "var(--color-primary-soft)",
      },
      fontFamily: {
        display: ["Instrument Serif", "Georgia", "serif"],
        body: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
