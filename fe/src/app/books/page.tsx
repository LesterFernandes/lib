"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { FieldError } from "@/components/ui/field";
import { useBooks } from "@/hooks/use-library";
import { PenLine } from "lucide-react";
import { cn } from "@/lib/utils";

export default function BooksPage() {
  const booksQuery = useBooks();
  const router = useRouter();

  return (
    <main className="mx-auto w-full max-w-3xl space-y-6 px-6 py-10">
      <Link href="/" className="text-sm underline underline-offset-4">
        Back to dashboard
      </Link>
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
            <li
              key={book.id}

              className="group hover:bg-muted/50 focus-within:bg-muted/50 flex items-center justify-between gap-4 rounded-md px-2 py-3"
            >
              <span className="min-w-0 font-medium break-words">
                {book.title}
              </span>
              <Button
                variant="ghost"
                className={cn(
                  "shrink-0 transition-opacity [@media(hover:hover)]:opacity-0 [@media(hover:hover)]:group-focus-within:opacity-100 [@media(hover:hover)]:group-hover:opacity-100",
                )}
                onClick={() => router.push(`/books/${book.id}`)}
              >
                <PenLine aria-hidden="true" className="size-4 shrink-0" />
              </Button>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
