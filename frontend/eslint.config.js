import babelParser from "@babel/eslint-parser";
import js from "@eslint/js";
import reactHooks from "eslint-plugin-react-hooks";
import globals from "globals";

const typescriptParserOptions = {
  requireConfigFile: false,
  babelOptions: {
    babelrc: false,
    configFile: false,
    parserOpts: {
      plugins: ["typescript", "jsx"],
    },
  },
  ecmaFeatures: {
    jsx: true,
  },
  sourceType: "module",
};

export default [
  {
    ignores: [
      "dist/**",
      "node_modules/**",
      "coverage/**",
    ],
  },
  {
    files: ["src/**/*.{ts,tsx}"],
    languageOptions: {
      parser: babelParser,
      parserOptions: typescriptParserOptions,
      globals: {
        ...globals.browser,
      },
    },
    plugins: {
      "react-hooks": reactHooks,
    },
    rules: {
      ...js.configs.recommended.rules,

      // TypeScript's compiler is the authoritative name/unused-symbol check.
      // Core ESLint rules do not understand the full TypeScript type space.
      "no-undef": "off",
      "no-unused-vars": "off",

      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "error",
    },
  },
  {
    files: ["vite.config.ts"],
    languageOptions: {
      parser: babelParser,
      parserOptions: typescriptParserOptions,
      globals: {
        ...globals.nodeBuiltin,
      },
    },
    rules: {
      ...js.configs.recommended.rules,
      "no-undef": "off",
      "no-unused-vars": "off",
    },
  },
];
