/** @type {import("jest").Config} */
const config = {
  testEnvironment: "jsdom",
  roots: ["<rootDir>/__tests__"],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/$1",
  },
  transform: {
    "^.+\\.tsx?$": [
      "ts-jest",
      {
        tsconfig: {
          module: "commonjs",
          moduleResolution: "node",
          esModuleInterop: true,
          isolatedModules: true,
          jsx: "react-jsx",
          strict: true,
          target: "ES2017",
        },
      },
    ],
  },
  collectCoverageFrom: [
    "lib/validators.ts",
    "lib/user-facing-error.ts",
    "lib/auth-storage.ts",
  ],
};

module.exports = config;
