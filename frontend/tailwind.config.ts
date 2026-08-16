import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Calm clinical palette - deliberately not the generic
        // "cream + terracotta" or "black + neon" AI-default look.
        ink: "#1B2430",        // near-black text, slightly blue
        paper: "#F4F7F6",      // soft clinical off-white background
        sage: "#3F6C5E",       // deep sage green - primary/brand
        sageLight: "#E4EEE9",  // light sage for cards/badges
        alert: "#B3441E",      // muted clay-red for SOS/alerts only
        gold: "#C79A3B",       // muted gold for "upcoming" accents
        steel: "#3E6480",      // muted steel blue for vitals accents
      },
      fontFamily: {
        display: ["'Source Serif 4'", "Georgia", "serif"],
        body: ["'Inter'", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
