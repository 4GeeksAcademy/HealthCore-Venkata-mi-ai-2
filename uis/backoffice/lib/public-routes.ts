export const BACKOFFICE_PUBLIC_ROUTES = new Set([
  "/login",
  "/register",
  "/forgot-password",
  "/reset-password",
]);

export function isBackofficePublicPath(pathname: string | null): boolean {
  return Boolean(pathname && BACKOFFICE_PUBLIC_ROUTES.has(pathname));
}
