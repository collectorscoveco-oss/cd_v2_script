export declare const GITHUB_LATEST_RELEASE_URL: string
export declare function summarizeUpdateFailure(
  error: unknown,
  apiBase: string,
  locationLike?: { port?: string | number | null | undefined } | null | undefined,
): { message: string; releaseUrl: string }
