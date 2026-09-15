import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  type BookPayload,
  createBook,
  createMember,
  getAuthors,
  getBook,
  getMember,
  getMembers,
  getPublishers,
  updateBook,
} from "@/lib/api";

const libraryQueryKeys = {
  authors: ["authors"] as const,
  publishers: ["publishers"] as const,
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
