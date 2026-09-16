"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import { FieldError } from "@/components/ui/field";
import { useBooks } from "@/hooks/use-library";

export default function BooksPage() {
  const booksQuery = useBooks();

  return (
    <main className="mx-auto w-full max-w-3xl space-y-6 px-6 py-10">
      <header className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold tracking-tight">Books</h1>
        <Link
          href="/books/add"
          className="text-sm underline underline-offset-4"
        >
          Add a book
        </Link>
      </header>

      {booksQuery.isPending ? (
        <p role="status" className="text-muted-foreground text-sm">
          Loading books...
        </p>
      ) : booksQuery.isError ? (
        <div className="space-y-3">
          <FieldError>{booksQuery.error.message}</FieldError>
          <Button variant="outline" onClick={() => booksQuery.refetch()}>
            Try again
          </Button>
        </div>
      ) : booksQuery.data.length === 0 ? (
        <p className="text-muted-foreground text-sm">No books yet.</p>
      ) : (
        <ul className="divide-y">
          {booksQuery.data.map((book) => (
            <li key={book.id} className="py-4">
              <Link
                href={`/books/${book.id}`}
                className="font-medium break-words underline underline-offset-4"
              >
                {book.title}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
