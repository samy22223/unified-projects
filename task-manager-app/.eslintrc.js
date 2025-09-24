module.exports = {
  root: true,
  ignorePatterns: ['client/**/*', 'node_modules/**/*'],
  env: {
    node: true,
    es2021: true,
    browser: true,
    jest: true
  },
  extends: [
    'eslint:recommended'
  ],
  parserOptions: {
    ecmaVersion: 12,
    sourceType: 'module'
  },
  rules: {
    'no-unused-vars': ['warn', { 'argsIgnorePattern': '^_' }],
    'no-console': 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'error' : 'off',
    'semi': ['error', 'always'],
    'quotes': ['error', 'single'],
    'indent': ['error', 2],
    'comma-dangle': ['error', 'never']
  },
  overrides: [
    {
      files: ['server/**/*.js'],
      env: {
        node: true,
        browser: false
      },
      rules: {
        // Node.js specific rules
      }
    }
  ]
};
