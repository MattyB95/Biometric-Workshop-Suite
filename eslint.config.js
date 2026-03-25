import html from "eslint-plugin-html";
import globals from "globals";

export default [
  {
    // Only lint the static version — templates/index.html has Jinja2
    // expressions inside <script> blocks that ESLint cannot parse as JS.
    files: ["docs/**/*.html"],
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
