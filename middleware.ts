import {
  convexAuthNextjsMiddleware,
  createRouteMatcher,
  isAuthenticatedNextjs,
  nextjsMiddlewareRedirect,
} from "@convex-dev/auth/nextjs/server";

const isPublicRoute = createRouteMatcher([
  "/",
  "/login(.*)",
  "/api/webhook/tradingview(.*)",
  "/api/telegram/webhook(.*)",
  "/api/engine/run(.*)",
  "/api/status(.*)",
  "/api/debug(.*)",
  "/api/tv/balance(.*)",
  "/api/tv/account(.*)",
  "/api/setup(.*)",
]);

export default convexAuthNextjsMiddleware(async (request) => {
  if (!isPublicRoute(request) && !(await isAuthenticatedNextjs())) {
    return nextjsMiddlewareRedirect(request, "/login");
  }
});

export const config = {
  matcher: ["/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)", "/(api|trpc)(.*)"],
};
