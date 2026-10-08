// ESLint revisa errores y malas prácticas; el formato es de Prettier (fase 2 del plan).
import js from '@eslint/js';
import globals from 'globals';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import prettier from 'eslint-config-prettier';

export default [
  { ignores: ['dist/', 'coverage/'] },
  js.configs.recommended,
  react.configs.flat.recommended,
  // JSX moderno: no hace falta importar React en cada archivo.
  react.configs.flat['jsx-runtime'],
  {
    files: ['**/*.{js,jsx}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: { ...globals.browser },
    },
    settings: { react: { version: 'detect' } },
    plugins: { 'react-hooks': reactHooks },
    rules: {
      // Solo las dos reglas clásicas de los hooks: el preset completo de la versión 7
      // trae reglas del React Compiler, que el proyecto no usa.
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
      // El proyecto no usa PropTypes.
      'react/prop-types': 'off',
    },
  },
  {
    // Pruebas (Vitest) y archivos de configuración que corren en Node.
    files: ['**/*.test.{js,jsx}', 'src/test/**', '*.config.js'],
    languageOptions: { globals: { ...globals.node, ...globals.vitest } },
  },
  // Al final: apaga las reglas de estilo que chocarían con Prettier.
  prettier,
];
