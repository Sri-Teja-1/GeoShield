import type { Config } from "tailwindcss";

// All design tokens are CSS custom properties defined in src/styles/globals.css
// (sourced from DESIGN.md §3, §4, §5). Tailwind utilities reference them via
// var(--token) so there is a single source of truth and no raw hex in components.
const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Core palette
        primary: "var(--primary)",
        "primary-container": "var(--primary-container)",
        "on-primary": "var(--on-primary)",
        secondary: "var(--secondary)",
        "on-secondary": "var(--on-secondary)",
        tertiary: "var(--tertiary)",
        "on-tertiary": "var(--on-tertiary)",
        // Surface hierarchy
        "surface-container-lowest": "var(--surface-container-lowest)",
        surface: "var(--surface)",
        "surface-container-low": "var(--surface-container-low)",
        "surface-container": "var(--surface-container)",
        "surface-container-high": "var(--surface-container-high)",
        "surface-container-highest": "var(--surface-container-highest)",
        "surface-variant": "var(--surface-variant)",
        // On-surface text
        "on-surface": "var(--on-surface)",
        "on-surface-variant": "var(--on-surface-variant)",
        outline: "var(--outline)",
        "outline-variant": "var(--outline-variant)",
        // Semantic
        success: "var(--success)",
        warning: "var(--warning)",
        danger: "var(--danger)",
      },
      fontFamily: {
        display: "var(--font-display)",
        body: "var(--font-body)",
        mono: "var(--font-mono)",
      },
      fontSize: {
        "display-lg": ["var(--display-lg-size)", { lineHeight: "var(--display-lg-leading)", fontWeight: "var(--display-lg-weight)" }],
        "display-md": ["var(--display-md-size)", { lineHeight: "var(--display-md-leading)", fontWeight: "var(--display-md-weight)" }],
        "display-sm": ["var(--display-sm-size)", { lineHeight: "var(--display-sm-leading)", fontWeight: "var(--display-sm-weight)" }],
        "headline-lg": ["var(--headline-lg-size)", { lineHeight: "var(--headline-lg-leading)", fontWeight: "var(--headline-lg-weight)" }],
        "headline-md": ["var(--headline-md-size)", { lineHeight: "var(--headline-md-leading)", fontWeight: "var(--headline-md-weight)" }],
        "headline-sm": ["var(--headline-sm-size)", { lineHeight: "var(--headline-sm-leading)", fontWeight: "var(--headline-sm-weight)" }],
        "body-lg": ["var(--body-lg-size)", { lineHeight: "var(--body-lg-leading)", fontWeight: "var(--body-lg-weight)" }],
        "body-md": ["var(--body-md-size)", { lineHeight: "var(--body-md-leading)", fontWeight: "var(--body-md-weight)" }],
        "body-sm": ["var(--body-sm-size)", { lineHeight: "var(--body-sm-leading)", fontWeight: "var(--body-sm-weight)" }],
        "label-lg": ["var(--label-lg-size)", { lineHeight: "var(--label-lg-leading)", fontWeight: "var(--label-lg-weight)" }],
        "label-md": ["var(--label-md-size)", { lineHeight: "var(--label-md-leading)", fontWeight: "var(--label-md-weight)" }],
        "label-sm": ["var(--label-sm-size)", { lineHeight: "var(--label-sm-leading)", fontWeight: "var(--label-sm-weight)" }],
        "mono-md": ["var(--mono-md-size)", { lineHeight: "var(--mono-md-leading)", fontWeight: "var(--mono-md-weight)" }],
        "mono-sm": ["var(--mono-sm-size)", { lineHeight: "var(--mono-sm-leading)", fontWeight: "var(--mono-sm-weight)" }],
      },
      spacing: {
        xs: "var(--space-xs)",
        sm: "var(--space-sm)",
        md: "var(--space-md)",
        lg: "var(--space-lg)",
        xl: "var(--space-xl)",
        "2xl": "var(--space-2xl)",
        "3xl": "var(--space-3xl)",
      },
      borderRadius: {
        sm: "var(--radius-sm)",
        md: "var(--radius-md)",
      },
      boxShadow: {
        card: "var(--shadow-card)",
        modal: "var(--shadow-modal)",
      },
      backdropBlur: {
        glass: "32px",
      },
      transitionTimingFunction: {
        layout: "cubic-bezier(0.2, 0, 0, 1)",
      },
    },
  },
  plugins: [],
};

export default config;
