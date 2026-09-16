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

export type BookListItem = Pick<
  Book,
  "id" | "title" | "author_id" | "publisher_id"
> & {
  loans?: BookLoan[];
};

export type MemberStatus = "active" | "suspended" | "expired" | "inactive";

export type MemberListItem = {
  id: string;
  card_number: string;
  first_name: string;
  last_name: string;
};

export type Member = MemberListItem & {
  email: string | null;
  phone: string | null;
  address_line_1: string | null;
  address_line_2: string | null;
  city: string | null;
  postal_code: string | null;
  date_of_birth: string | null;
  joined_on: string;
  expires_on: string | null;
  status: MemberStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type MemberPayload = Omit<
  Member,
  "id" | "joined_on" | "created_at" | "updated_at"
> & {
  joined_on?: string;
};

export type Loan = {
  id: string;
  book_id: string;
  member_id: string;
  borrowed_at: string;
  returned_at: string | null;
  created_at: string;
  updated_at: string;
};

export type LoanPayload = Pick<Loan, "book_id" | "member_id">;

export type BookLoan = Loan & {
  member: MemberListItem;
};

export type MemberLoan = Loan & {
  book: Pick<Book, "id" | "title">;
};

export type MemberDetails = Member & {
  loans: MemberLoan[];
};

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

export function getBooks(includeLoans = false): Promise<BookListItem[]> {
  return apiRequest<BookListItem[]>(
    includeLoans ? "/books?include_loans=true" : "/books",
  );
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

export function getMembers(): Promise<MemberListItem[]> {
  return apiRequest<MemberListItem[]>("/members");
}

export function getMember(memberId: string): Promise<MemberDetails> {
  return apiRequest<MemberDetails>(`/members/${memberId}`);
}

export function createMember(payload: MemberPayload): Promise<Member> {
  return apiRequest<Member>("/members", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function borrowBook(payload: LoanPayload): Promise<Loan> {
  return apiRequest<Loan>("/loans", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function returnBook(loanId: string): Promise<Loan> {
  return apiRequest<Loan>(`/loans/${loanId}/return`, {
    method: "POST",
  });
}
