export type Author = {
  id: string;
  full_name: string;
  biography: string | null;
};

export type Publisher = {
  id: string;
  name: string;
  website: string | null;
  contact_email: string | null;
};

export type Book = {
  id: string;
  author_id: string | null;
  publisher_id: string | null;
  title: string;
  subtitle: string | null;
  description: string | null;
  language: string;
};

export type BookPayload = Omit<Book, "id">;

type ErrorBody = {
  error?: {
    message?: string;
  };
};

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ??
  "http://localhost:8000";

export class ApiError extends Error {}

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...init?.headers,
      },
    });
  } catch {
    throw new ApiError("Could not reach the library server.");
  }

  const body = (await response.json().catch(() => null)) as
    T | ErrorBody | null;
  if (!response.ok) {
    const message = (body as ErrorBody | null)?.error?.message;
    throw new ApiError(
      message ?? "The library server could not complete the request.",
    );
  }

  return body as T;
}

export function getAuthors(): Promise<Author[]> {
  return apiRequest<Author[]>("/authors");
}

export function getPublishers(): Promise<Publisher[]> {
  return apiRequest<Publisher[]>("/publishers");
}

export function getBook(bookId: string): Promise<Book> {
  return apiRequest<Book>(`/books/${bookId}`);
}

export function createBook(payload: BookPayload): Promise<Book> {
  return apiRequest<Book>("/books", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateBook(
  bookId: string,
  payload: Partial<BookPayload>,
): Promise<Book> {
  return apiRequest<Book>(`/books/${bookId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
