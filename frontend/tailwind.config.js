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
        // because they don't switch with theme). Tuned for the Blue DARK
        // theme — bright, saturated hues that glow against deep navy.
        // Currencies: star/gold = XP, cyan gem = gems, orange = streak fire.
        glow: {
          DEFAULT: "#2f7ff0",
          soft: "rgba(47, 127, 240, 0.45)",
        },
        success: "#34D399",   // emerald reads bright on navy
        coin: "#FBBF24",      // gold coin
        star: "#FBBF24",      // gold star (XP badge in the top bar)
        gem: "#38BDF8",       // cyan gem (gems currency)
        xp: "#A78BFA",        // lively violet for XP accents
        streak: "#FB923C",    // warm orange — fire icon
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
        // On the navy canvas a real neon-blue glow reads well — cards and
        // CTAs float above the page with a bright halo plus depth shadow.
        glow: "0 0 0 1px rgba(47,127,240,0.20), 0 8px 28px -6px rgba(47, 127, 240, 0.45), 0 4px 12px -4px rgba(0, 0, 0, 0.45)",
        "glow-lg": "0 0 0 1px rgba(47,127,240,0.28), 0 14px 40px -6px rgba(47, 127, 240, 0.60), 0 6px 16px -4px rgba(0, 0, 0, 0.50)",
        // Warm-orange-tinted lift for streak/fire accents (kept semantic).
        "glow-orange": "0 8px 28px -6px rgba(251, 146, 60, 0.50), 0 4px 12px -4px rgba(0, 0, 0, 0.45)",
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
