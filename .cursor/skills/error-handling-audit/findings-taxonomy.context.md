# Error handling findings taxonomy

**Source:** ErrorHandling Requirement.txt. Use these category names exactly.

For each file or module you review, identify and report:

1. MISSING TRY/CATCH — async operations (fetch, await, file I/O, JSON parsing) that have no error handling at all.
2. OVERLY BROAD CATCH — try/catch or try/except blocks that wrap entire functions or large sections of code instead of the specific dangerous operation.
3. SILENT FAILURES — caught errors that are swallowed (empty catch blocks, bare `except: pass`).
4. RAW ERROR EXPOSURE — places where a raw exception message, stack trace, or status code could reach the user interface or API response.
5. SENSITIVE DATA LEAKS — error outputs or logs that may include secrets, database connection strings, internal paths, or personal data.
6. MISSING LOADING/ERROR UI STATES — frontend components that fetch data but render nothing (or crash) when the request is loading or fails.
7. NO USER CALL TO ACTION — error states that display a message but offer no way forward (no retry, no navigation, no support contact).
8. MISSING sys.exit ON SCRIPT FAILURE — Python scripts that encounter a critical error but exit with code 0 or no explicit exit code.

For each finding, report:

- File path and line number (or range)
- Category (from the list above)
- A one-line description of the problem
- Suggested fix (brief — implementation is the developer's responsibility)

## HealthCore repo notes

When reporting, do not quote secrets, connection strings, member IDs, or clinical free text. Sample IDs such as `HC-*`, `CLM-*`, `APT-*`, `CLN-*` are synthetic; still flag PHI-shaped leaks.
