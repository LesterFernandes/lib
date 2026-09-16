import Link from "next/link";

import { BookForm } from "@/components/book-form";

type EditBookPageProps = {
  params: Promise<{ bookId: string }>;
};

export default async function EditBookPage({ params }: EditBookPageProps) {
  const { bookId } = await params;

  return (
    <main className="px-6 py-10 sm:px-10">
      <nav
        aria-label="Book navigation"
        className="mx-auto mb-6 w-full max-w-2xl"
      >
        <Link href="/books" className="text-sm underline underline-offset-4">
          Back to books
        </Link>
      </nav>
      <BookForm key={bookId} bookId={bookId} />
    </main>
  );
}
