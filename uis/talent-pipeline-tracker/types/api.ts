export interface ApiError {
  message: string;
  status?: number;
  details?: unknown;
}

export interface AsyncDataState<T> {
  loading: boolean;
  error: string | null;
  data: T | null;
}

export type QueryParams = Partial<
  Record<"status" | "stage" | "query" | "page" | "limit", string>
>;