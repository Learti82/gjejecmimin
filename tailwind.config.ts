import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Trust-tier accent colors, referenced by name so the UI stays consistent
        // whether a price came from an official index, a verified retailer, or the crowd.
        official: {
          bg: "#e0f2fe",
          fg: "#075985",
          ring: "#7dd3fc",
        },
        verified: {
          bg: "#dcfce7",
          fg: "#166534",
          ring: "#86efac",
        },
        crowd: {
          bg: "#fef3c7",
          fg: "#92400e",
          ring: "#fcd34d",
        },
      },
    },
  },
  plugins: [],
};

export default config;
