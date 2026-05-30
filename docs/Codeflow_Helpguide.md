<div align="center">
	<h1 style="font-size:2.5em; font-family: 'Segoe UI', Arial, sans-serif; font-weight:700; margin-bottom:0.2em;">Healthcore</h1>
	<h2 style="font-size:1.5em; font-family: 'Segoe UI', Arial, sans-serif; font-weight:600; margin-top:0;">Healthcare Provider Site</h2>
</div>

---

## Project Overview

| Type      | Simple, static landing page |
|-----------|----------------------------|
| Backend   | None (frontend only)       |
| Tech Stack| HTML, Tailwind CSS, JavaScript |

---

## Core Files

- **index.html**: Page structure
- **main.js**: Logic for language switching and form validation
- **en.json / es.json**: Translation files for English and Spanish
- **Diagram**: Architecture layout. [2, 3]

---

## Page Sections

- Navigation
- Hero
- Services
- About
- Sign-up form
- Footer

---

## JavaScript Functionality

- Loads the correct language JSON file based on user selection
- Updates page text dynamically when the language changes
- Validates form fields before submission

---

## Form Validation Rules

- **Name**: Minimum 3 characters
- **Email**: Valid format check
- **Phone**: 7 to 20 digits
- **Concerns**: Minimum 20 characters

---

## Optimization & Accessibility

- **Accessibility**: Semantic HTML, skip links, ARIA attributes for errors, and dynamic HTML lang attribute updates
- **SEO**: Meta tags and structured data for search engines

---

## System Limitations

- Tailwind CSS is loaded via CDN
- Localization JSON files require an HTTP server to load
- No backend or API integration. [4]

---

## Scalability

- Easy to add new languages by creating new JSON files
- Simple to update validation rules inside the JavaScript logic
