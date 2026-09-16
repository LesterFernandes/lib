"use client";

import { type FormEvent, useState } from "react";

import { ApiError, type Book, type BookPayload } from "@/lib/api";
import {
  useAuthors,
  useBook,
  useCreateBook,
  usePublishers,
  useUpdateBook,
} from "@/hooks/use-library";
import { Button } from "@/components/ui/button";
import {
  Field,
  FieldError,
  FieldGroup,
  FieldLabel,
  FieldSet,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

type BookFormProps = {
  bookId?: string;
};

type FormValues = {
  title: string;
  subtitle: string;
  description: string;
  language: string;
  authorId: string | null;
  publisherId: string | null;
};

const noAuthorValue = "__no_author__";
const noPublisherValue = "__no_publisher__";

const emptyForm: FormValues = {
  title: "",
  subtitle: "",
  description: "",
  language: "en",
  authorId: null,
  publisherId: null,
};

function bookToFormValues(book: Book): FormValues {
  return {
    title: book.title,
    subtitle: book.subtitle ?? "",
    description: book.description ?? "",
    language: book.language,
    authorId: book.author_id,
    publisherId: book.publisher_id,
  };
}

export function BookForm({ bookId }: BookFormProps) {
  const isEditing = Boolean(bookId);
  const authorsQuery = useAuthors();
  const publishersQuery = usePublishers();
  const bookQuery = useBook(bookId);
  const createBookMutation = useCreateBook();
  const updateBookMutation = useUpdateBook();
  const [draftValues, setDraftValues] = useState<FormValues | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const values =
    draftValues ??
    (bookQuery.data ? bookToFormValues(bookQuery.data) : emptyForm);

  const authors = authorsQuery.data ?? [];
  const publishers = publishersQuery.data ?? [];
  const isLoading =
    authorsQuery.isPending ||
    publishersQuery.isPending ||
    (isEditing && bookQuery.isPending);
  const isSubmitting =
    createBookMutation.isPending || updateBookMutation.isPending;
  const queryError =
    authorsQuery.error ??
    publishersQuery.error ??
    (isEditing ? bookQuery.error : null);
  const error =
    formError ??
    (queryError instanceof ApiError
      ? queryError.message
      : queryError
        ? "Could not load the book form."
        : null);

  function updateValues(update: Partial<FormValues>) {
    setDraftValues((currentValues) => ({
      ...(currentValues ?? values),
      ...update,
    }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    setSuccessMessage(null);

    const title = values.title.trim();
    if (!title) {
      setFormError("A book title is required.");
      return;
    }

    const payload: BookPayload = {
      title,
      subtitle: values.subtitle.trim() || null,
      description: values.description.trim() || null,
      language: values.language.trim() || "en",
      author_id: values.authorId,
      publisher_id: values.publisherId,
    };

    try {
      if (bookId) {
        await updateBookMutation.mutateAsync({ bookId, payload });
        setSuccessMessage("Book updated successfully.");
      } else {
        const createdBook = await createBookMutation.mutateAsync(payload);
        setSuccessMessage(`Book created successfully: ${createdBook.title}.`);
      }
      setDraftValues(null);
    } catch (submitError) {
      setFormError(
        submitError instanceof ApiError
          ? submitError.message
          : "Could not save the book.",
      );
    }
  }

  return (
    <form
      className="mx-auto w-full max-w-2xl space-y-6"
      onSubmit={handleSubmit}
    >
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">
          {isEditing ? "Edit book" : "Add a book"}
        </h1>
        <p className="text-muted-foreground text-sm">
          {isEditing
            ? "Update the catalogue record and save your changes."
            : "Create a catalogue record for a library book."}
        </p>
      </header>

      {error && <FieldError>{error}</FieldError>}
      {successMessage && (
        <p
          role="status"
          className="text-sm text-emerald-700 dark:text-emerald-400"
        >
          {successMessage}
        </p>
      )}

      <FieldSet disabled={isLoading || isSubmitting}>
        <FieldGroup>
          <Field>
            <FieldLabel htmlFor="book-title">Title</FieldLabel>
            <Input
              id="book-title"
              value={values.title}
              onChange={(event) => updateValues({ title: event.target.value })}
              placeholder="Book title"
              maxLength={500}
              required
            />
          </Field>

          <Field>
            <FieldLabel htmlFor="book-subtitle">Subtitle</FieldLabel>
            <Input
              id="book-subtitle"
              value={values.subtitle}
              onChange={(event) =>
                updateValues({ subtitle: event.target.value })
              }
              placeholder="Optional subtitle"
              maxLength={500}
            />
          </Field>

          <Field>
            <FieldLabel htmlFor="book-description">Description</FieldLabel>
            <Textarea
              id="book-description"
              value={values.description}
              onChange={(event) =>
                updateValues({ description: event.target.value })
              }
              placeholder="Optional book description"
            />
          </Field>

          <div className="grid gap-5 sm:grid-cols-2">
            <Field>
              <FieldLabel htmlFor="book-language">Language</FieldLabel>
              <Input
                id="book-language"
                value={values.language}
                onChange={(event) =>
                  updateValues({ language: event.target.value })
                }
                placeholder="en"
                maxLength={10}
                required
              />
            </Field>

            <Field>
              <FieldLabel htmlFor="book-publisher">Publisher</FieldLabel>
              <Select
                items={[
                  { value: noPublisherValue, label: "No publisher" },
                  ...publishers.map((publisher) => ({
                    value: publisher.id,
                    label: publisher.name,
                  })),
                ]}
                value={values.publisherId ?? noPublisherValue}
                onValueChange={(value) =>
                  updateValues({
                    publisherId: value === noPublisherValue ? null : value,
                  })
                }
              >
                <SelectTrigger id="book-publisher" className="w-full">
                  <SelectValue placeholder="Choose a publisher" />
                </SelectTrigger>
                <SelectContent>
                  <SelectGroup>
                    <SelectItem value={noPublisherValue}>
                      No publisher
                    </SelectItem>
                    {publishers.map((publisher) => (
                      <SelectItem key={publisher.id} value={publisher.id}>
                        {publisher.name}
                      </SelectItem>
                    ))}
                  </SelectGroup>
                </SelectContent>
              </Select>
            </Field>
          </div>

          <Field>
            <FieldLabel htmlFor="book-author">Author</FieldLabel>
            <Select
              items={[
                { value: noAuthorValue, label: "No author" },
                ...authors.map((author) => ({
                  value: author.id,
                  label: author.full_name,
                })),
              ]}
              value={values.authorId ?? noAuthorValue}
              onValueChange={(value) =>
                updateValues({
                  authorId: value === noAuthorValue ? null : value,
                })
              }
            >
              <SelectTrigger id="book-author" className="w-full">
                <SelectValue placeholder="Choose an author" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  <SelectItem value={noAuthorValue}>No author</SelectItem>
                  {authors.map((author) => (
                    <SelectItem key={author.id} value={author.id}>
                      {author.full_name}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>
          </Field>
        </FieldGroup>

        <Button type="submit" disabled={isLoading || isSubmitting}>
          {isSubmitting
            ? "Saving…"
            : isEditing
              ? "Save changes"
              : "Create book"}
        </Button>
      </FieldSet>
    </form>
  );
}
