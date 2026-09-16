"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { FieldError } from "@/components/ui/field";
import { useBooks, useBorrowBook } from "@/hooks/use-library";
import { type BookListItem } from "@/lib/api";
import { cn } from "@/lib/utils";

type BorrowBookDialogProps = {
  memberId: string;
  disabled?: boolean;
  onBorrowed: (book: BookListItem) => void;
};

export function BorrowBookDialog({
  memberId,
  disabled,
  onBorrowed,
}: BorrowBookDialogProps) {
  const [open, setOpen] = useState(false);
  const booksQuery = useBooks(open);
  const borrowMutation = useBorrowBook();

  function handleOpenChange(nextOpen: boolean) {
    if (borrowMutation.isPending) return;
    if (nextOpen) borrowMutation.reset();
    setOpen(nextOpen);
  }

  function handleBorrow(book: BookListItem) {
    borrowMutation.mutate(
      { member_id: memberId, book_id: book.id },
      {
        onSuccess: () => {
          setOpen(false);
          onBorrowed(book);
        },
      },
    );
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger disabled={disabled} render={<Button />}>
        Borrow book
      </DialogTrigger>
      <DialogContent className="max-h-[80dvh] overflow-y-auto sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Borrow book</DialogTitle>
          <DialogDescription>
            Choose a book to loan to this member.
          </DialogDescription>
        </DialogHeader>

        {borrowMutation.isError && (
          <FieldError>{borrowMutation.error.message}</FieldError>
        )}

        <div className="max-h-[55dvh] overflow-y-auto">
          {booksQuery.isPending ? (
            <p role="status" className="text-muted-foreground py-4 text-sm">
              Loading books...
            </p>
          ) : booksQuery.isError ? (
            <div className="space-y-3 py-4">
              <FieldError>{booksQuery.error.message}</FieldError>
              <Button variant="outline" onClick={() => booksQuery.refetch()}>
                Try again
              </Button>
            </div>
          ) : booksQuery.data.length === 0 ? (
            <p className="text-muted-foreground py-4 text-sm">No books yet.</p>
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
                    size="sm"
                    aria-label={`Borrow ${book.title}`}
                    disabled={borrowMutation.isPending}
                    onClick={() => handleBorrow(book)}
                    className={cn(
                      "shrink-0 transition-opacity",
                      !borrowMutation.isPending &&
                        "[@media(hover:hover)]:opacity-0 [@media(hover:hover)]:group-focus-within:opacity-100 [@media(hover:hover)]:group-hover:opacity-100",
                    )}
                  >
                    {borrowMutation.isPending &&
                    borrowMutation.variables.book_id === book.id
                      ? "Borrowing..."
                      : "Borrow"}
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
