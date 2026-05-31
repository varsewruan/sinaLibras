/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html",
  ],
  theme: {
    extend: {
      // Shadcn semantic tokens — driven by CSS variables in index.css so we
      // can swap themes without changing component classNames.
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",

        // SINALibras-specific gamification palette (literal values, not vars,
        // because they don't switch with theme). Tuned for the Blue light
        // theme — saturations dialed to read on cool white without glare
        // and without losing legibility. Gamification icons keep their
        // semantic colors (gold = coin, orange = fire, purple = XP).
        glow: {
          DEFAULT: "#0446b0",
          soft: "rgba(141, 206, 240, 0.45)",
        },
        success: "#16A34A",   // forest green reads on white
        coin: "#CA8A04",      // ochre gold (legible on white)
        xp: "#7C3AED",        // royal purple deeper for white bg legibility
        streak: "#EA580C",    // warm orange — fire icon, no more coral
      },
      fontFamily: {
        sans: ["Nunito", "system-ui", "sans-serif"],
        display: ["Nunito", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      boxShadow: {
        // On a light canvas, "neon glow" reads as glare. Use soft cool-blue
        // drop-shadows tinted toward the brand primary so cards lift off
        // the page without producing a harsh halo.
        glow: "0 6px 24px -8px rgba(4, 70, 176, 0.40), 0 2px 6px -2px rgba(3, 31, 85, 0.10)",
        "glow-lg": "0 10px 32px -8px rgba(4, 70, 176, 0.50), 0 4px 10px -2px rgba(3, 31, 85, 0.12)",
        // Warm-orange-tinted lift for streak/fire accents (kept semantic).
        "glow-orange": "0 6px 24px -8px rgba(234, 88, 12, 0.45), 0 2px 6px -2px rgba(28, 20, 16, 0.08)",
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
        "fade-in-up": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "flame-pulse": {
          // Fire icon glow stays orange — semantic, not part of the brand palette.
          "0%, 100%": { transform: "scale(1) rotate(-2deg)", filter: "drop-shadow(0 0 6px #EA580C80)" },
          "50%":      { transform: "scale(1.1) rotate(2deg)", filter: "drop-shadow(0 0 12px #EA580Ccc)" },
        },
        "xp-burst": {
          "0%":   { opacity: "0", transform: "translateY(0) scale(0.8)" },
          "30%":  { opacity: "1", transform: "translateY(-12px) scale(1.1)" },
          "100%": { opacity: "0", transform: "translateY(-48px) scale(1)" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "fade-in-up": "fade-in-up 0.3s ease-out",
        "flame-pulse": "flame-pulse 1.8s ease-in-out infinite",
        "xp-burst": "xp-burst 1.2s ease-out forwards",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
