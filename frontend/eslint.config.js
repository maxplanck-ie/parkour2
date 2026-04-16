import js from "@eslint/js";
import globals from "globals";
import pluginVue from "eslint-plugin-vue";
import vueParser from "vue-eslint-parser";

export default [
  {
    ignores: ["dist/**", "node_modules/**"]
  },
  {
    files: ["**/*.{js,vue}"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      parser: vueParser,
      globals: {
        ...globals.browser,
        ...globals.node
      }
    },
    plugins: {
      vue: pluginVue
    },
    rules: {
      ...js.configs.recommended.rules,
      ...pluginVue.configs["flat/recommended"].reduce(
        (acc, config) => ({ ...acc, ...(config.rules || {}) }),
        {}
      )
    }
  }
];
