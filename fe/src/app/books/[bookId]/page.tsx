import { BookForm } from "@/components/book-form";

type EditBookPageProps = {
  params: Promise<{ bookId: string }>;
};

export default async function EditBookPage({ params }: EditBookPageProps) {
  const { bookId } = await params;

  return (
    <main className="px-6 py-10 sm:px-10">
      <BookForm key={bookId} bookId={bookId} />
    </main>
  );
}
