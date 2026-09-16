import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  type BookPayload,
  borrowBook,
  createBook,
  createMember,
  getAuthors,
  getBook,
  getBooks,
  getMember,
  getMembers,
  getPublishers,
  returnBook,
  updateBook,
} from "@/lib/api";

const libraryQueryKeys = {
  authors: ["authors"] as const,
  publishers: ["publishers"] as const,
  bookLists: ["books", "list"] as const,
  books: (includeLoans: boolean) =>
    ["books", "list", { includeLoans }] as const,
  book: (bookId: string) => ["books", bookId] as const,
  members: ["members"] as const,
  member: (memberId: string) => ["members", memberId] as const,
};

export function useAuthors() {
  return useQuery({
    queryKey: libraryQueryKeys.authors,
    queryFn: getAuthors,
  });
}

export function usePublishers() {
  return useQuery({
    queryKey: libraryQueryKeys.publishers,
    queryFn: getPublishers,
  });
}

type BooksQueryOptions = {
  enabled?: boolean;
  includeLoans?: boolean;
};

export function useBooks({
  enabled = true,
  includeLoans = false,
}: BooksQueryOptions = {}) {
  return useQuery({
    queryKey: libraryQueryKeys.books(includeLoans),
    queryFn: () => getBooks(includeLoans),
    enabled,
  });
}

export function useBook(bookId: string | undefined) {
  return useQuery({
    queryKey: libraryQueryKeys.book(bookId ?? ""),
    queryFn: () => getBook(bookId as string),
    enabled: Boolean(bookId),
  });
}

export function useCreateBook() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createBook,
    onSuccess: (book) => {
      queryClient.setQueryData(libraryQueryKeys.book(book.id), book);
      return queryClient.invalidateQueries({
        queryKey: libraryQueryKeys.bookLists,
      });
    },
  });
}

type UpdateBookVariables = {
  bookId: string;
  payload: Partial<BookPayload>;
};

export function useUpdateBook() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ bookId, payload }: UpdateBookVariables) =>
      updateBook(bookId, payload),
    onSuccess: (book) => {
      queryClient.setQueryData(libraryQueryKeys.book(book.id), book);
      return queryClient.invalidateQueries({
        queryKey: libraryQueryKeys.bookLists,
      });
    },
  });
}

export function useMembers() {
  return useQuery({
    queryKey: libraryQueryKeys.members,
    queryFn: getMembers,
  });
}

export function useMember(memberId: string) {
  return useQuery({
    queryKey: libraryQueryKeys.member(memberId),
    queryFn: () => getMember(memberId),
  });
}

export function useCreateMember() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createMember,
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: libraryQueryKeys.members }),
  });
}

export function useBorrowBook() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: borrowBook,
    onSuccess: (loan) =>
      Promise.all([
        queryClient.invalidateQueries({
          queryKey: libraryQueryKeys.member(loan.member_id),
          exact: true,
        }),
        queryClient.invalidateQueries({ queryKey: libraryQueryKeys.bookLists }),
      ]),
  });
}

export function useReturnBook() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: returnBook,
    onSuccess: (loan) =>
      Promise.all([
        queryClient.invalidateQueries({
          queryKey: libraryQueryKeys.member(loan.member_id),
          exact: true,
        }),
        queryClient.invalidateQueries({ queryKey: libraryQueryKeys.bookLists }),
      ]),
  });
}
