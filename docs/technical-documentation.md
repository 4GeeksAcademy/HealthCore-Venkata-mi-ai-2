# Healthcore Landing Page Technical Documentation

## 1. System Overview
This implementation is a static, client-rendered landing page built with semantic HTML and Tailwind CSS (CDN), enhanced with JavaScript for:
- dynamic language switching (English and Spanish), and
- client-side form validation.

There is no backend dependency in the current architecture.

## 2. Project Artifacts
- `index.html`: Main document structure and UI markup.
- `scripts/main.js`: Runtime logic for i18n and form validation.
- `Language/en.json`: English localization dictionary.
- `Language/es.json`: Spanish localization dictionary.
- `Documents/diagram/healthcore-architecture.png`: architecture diagram.

## 3. Frontend Architecture
### 3.1 Presentation Layer
`index.html` defines:
- Top utility ribbon (includes language selector).
- Main navigation and action items.
- Hero and service sections.
- About section.
- Patient sign-up form.
- Footer and policy links.

Tailwind utility classes are used for responsive layout and styling.

### 3.2 Behavior Layer
`scripts/main.js` handles:
- language file loading with `fetch` from `Language/*.json`,
- applying translations to all elements with `data-i18n`,
- setting document language attribute (`document.documentElement.lang`),
- language dropdown change events,
- form validation and error rendering.

### 3.3 Localization Layer
Localization content is decoupled from UI logic:
- `Language/en.json`
- `Language/es.json`

Each key maps to text used in markup (`data-i18n`).

## 4. Data Flow
### 4.1 Language Flow
1. Page initializes JavaScript.
2. Default language is set to English.
3. `main.js` fetches the selected dictionary JSON.
4. DOM text is updated by matching `data-i18n` keys.
5. On dropdown change, language is reloaded and reapplied.

### 4.2 Form Validation Flow
1. User submits the form.
2. Validation runs for all fields:
   - Full name length.
   - Email format.
   - Phone pattern.
   - Concerns minimum length.
3. Errors are displayed inline with ARIA invalid states.
4. On success, success banner appears and form resets.

## 5. Validation Rules (Current)
- `fullName`: minimum 3 characters.
- `email`: standard email regex check.
- `phone`: numeric/toll format regex, 7-20 chars.
- `concerns`: minimum 20 characters.

## 6. Accessibility Notes
- Semantic HTML sections and headings are used.
- Skip link is included for keyboard users.
- Form errors use `aria-invalid` and error containers.
- Language switch updates HTML `lang` attribute.

## 7. SEO and Structured Data
`index.html` includes:
- meta description and social tags,
- Schema.org JSON-LD (`MedicalBusiness`) for organization metadata.

## 8. Technical Constraints
- Tailwind is loaded via CDN (runtime dependency).
- Localization files must be served by HTTP (fetch requires hosted context).
- No server-side rendering or API integration is currently implemented.

## 9. Extension Points
- Add new language by creating another JSON dictionary and adding it to `languageFiles` in `scripts/main.js`.
- Externalize validation messages into localization files for fully translated form errors.
- Move constants/config into dedicated JS modules if build tooling is introduced.

## 10. Folder Placement Summary
- Diagram location: `Documents/diagram/healthcore-architecture.md`
- Technical document location: `documents/technical-documentation.md`
