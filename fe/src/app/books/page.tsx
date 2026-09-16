"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { PenLine } from "lucide-react";

import { Button } from "@/components/ui/button";
import { FieldError } from "@/components/ui/field";
import { useBooks } from "@/hooks/use-library";
import { cn } from "@/lib/utils";

export default function BooksPage() {
  const booksQuery = useBooks({ includeLoans: true });
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
        <ul className="space-y-2">
          {booksQuery.data.map((book) => {
            const currentLoan = book.loans?.[0];

            return (
              <li
                key={book.id}
                className={cn(
                  "group flex items-start justify-between gap-4 rounded-lg border px-3 py-4",
                  currentLoan
                    ? "border-amber-300 bg-amber-50 dark:border-amber-800 dark:bg-amber-950/40"
                    : "hover:bg-muted/50 focus-within:bg-muted/50 border-transparent",
                )}
              >
                <div className="min-w-0 space-y-2">
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                    <span className="min-w-0 font-medium break-words">
                      {book.title}
                    </span>
                    {currentLoan && (
                      <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-900 dark:bg-amber-950 dark:text-amber-200">
                        Current loan
                      </span>
                    )}
                  </div>
                  {currentLoan && (
                    <div className="text-muted-foreground space-y-1 text-sm">
                      <p className="break-words">
                        Borrowed by{" "}
                        <Link
                          href={`/members/${currentLoan.member.id}`}
                          className="underline underline-offset-4"
                        >
                          {currentLoan.member.first_name}{" "}
                          {currentLoan.member.last_name}
                        </Link>{" "}
                        (Card {currentLoan.member.card_number})
                      </p>
                      <p>
                        Borrowed{" "}
                        <time dateTime={currentLoan.borrowed_at}>
                          {new Date(currentLoan.borrowed_at).toLocaleString()}
                        </time>
                      </p>
                    </div>
                  )}
                </div>
                <Button
                  variant="ghost"
                  aria-label={`Edit ${book.title}`}
                  className="shrink-0 transition-opacity [@media(hover:hover)]:opacity-0 [@media(hover:hover)]:group-focus-within:opacity-100 [@media(hover:hover)]:group-hover:opacity-100"
                  onClick={() => router.push(`/books/${book.id}`)}
                >
                  <PenLine aria-hidden="true" className="size-4 shrink-0" />
                </Button>
              </li>
            );
          })}
        </ul>
      )}
    </main>
  );
}
