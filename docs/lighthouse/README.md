# Lighthouse lab artifacts

Desktop Lighthouse CLI **12.8.2**, `next dev` in Docker, 2026-09-16.

| File | What it shows |
|------|----------------|
| [healthcore-home-before.png](./healthcore-home-before.png) | Public home before webfont/signup split (Performance 99, LCP 0.9s) |
| [healthcore-home-after.png](./healthcore-home-after.png) | Public home after (Performance 99, LCP 0.8s) |
| [backoffice-login-after.png](./backoffice-login-after.png) | Backoffice login after AuthGuard/font/server heading work (Performance 100) |
| [scores.json](./scores.json) | Numeric extract from the CLI reports |

Full JSON reports are gitignored (large). Backoffice login **before** (~75) was a Chrome DevTools Lighthouse run earlier the same day; that PNG was not captured into the repo.
