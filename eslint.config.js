import html from "eslint-plugin-html";
import globals from "globals";

export default [
  {
    // Lint all docs/ HTML and templates that contain pure JS (no Jinja2).
    // templates/keystroke.html is excluded — Jinja2 {{ }} inside <script> breaks the parser.
    files: ["docs/**/*.html", "templates/face.html", "templates/home.html"],
    plugins: { html },
    languageOptions: {
      ecmaVersion: 2022,
      globals: {
        ...globals.browser,
        Chart: "readonly", // loaded from Chart.js CDN
      },
    },
    rules: {
      eqeqeq: ["error", "always"],
      "no-var": "error",
      "no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
      "no-undef": "error",
      "prefer-const": "warn",
      "no-console": "warn",
    },
  },
];
