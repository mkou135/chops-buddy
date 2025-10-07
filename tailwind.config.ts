import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#3C6E71",
          dark: "#284B63",
          light: "#D9D9D9",
        },
      },
    },
  },
  plugins: [],
};

export default config;
