"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
  FieldLegend,
  FieldSet,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useCreateMember } from "@/hooks/use-library";
import { ApiError, type MemberPayload, type MemberStatus } from "@/lib/api";

type MemberInput = {
  name: keyof MemberPayload;
  label: string;
  type?: "text" | "email" | "tel" | "date";
  required?: boolean;
  maxLength?: number;
  autoComplete?: string;
  description?: string;
};

const fieldGroups: { title: string; fields: MemberInput[] }[] = [
  {
    title: "Personal details",
    fields: [
      {
        name: "card_number",
        label: "Card number",
        required: true,
        maxLength: 50,
      },
      {
        name: "first_name",
        label: "First name",
        required: true,
        maxLength: 100,
        autoComplete: "given-name",
      },
      {
        name: "last_name",
        label: "Last name",
        required: true,
        maxLength: 100,
        autoComplete: "family-name",
      },
      {
        name: "date_of_birth",
        label: "Date of birth",
        type: "date",
        autoComplete: "bday",
      },
    ],
  },
  {
    title: "Contact details",
    fields: [
      {
        name: "email",
        label: "Email",
        type: "email",
        maxLength: 255,
        autoComplete: "email",
      },
      {
        name: "phone",
        label: "Phone",
        type: "tel",
        maxLength: 50,
        autoComplete: "tel",
      },
      {
        name: "address_line_1",
        label: "Address line 1",
        maxLength: 255,
        autoComplete: "address-line1",
      },
      {
        name: "address_line_2",
        label: "Address line 2",
        maxLength: 255,
        autoComplete: "address-line2",
      },
      {
        name: "city",
        label: "City",
        maxLength: 100,
        autoComplete: "address-level2",
      },
      {
        name: "postal_code",
        label: "Postal code",
        maxLength: 20,
        autoComplete: "postal-code",
      },
    ],
  },
  {
    title: "Membership dates",
    fields: [
      {
        name: "joined_on",
        label: "Joining date",
        type: "date",
        description: "Leave blank to use today.",
      },
      { name: "expires_on", label: "Expiry date", type: "date" },
    ],
  },
];

const statusOptions: { value: MemberStatus; label: string }[] = [
  { value: "active", label: "Active" },
  { value: "suspended", label: "Suspended" },
  { value: "expired", label: "Expired" },
  { value: "inactive", label: "Inactive" },
];

export function MemberForm() {
  const router = useRouter();
  const createMemberMutation = useCreateMember();
  const [formError, setFormError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    const formData = new FormData(event.currentTarget);
    const getFieldValue = (name: keyof MemberPayload) =>
      String(formData.get(name) ?? "").trim();

    const payload: MemberPayload = {
      card_number: getFieldValue("card_number"),
      first_name: getFieldValue("first_name"),
      last_name: getFieldValue("last_name"),
      email: getFieldValue("email") || null,
      phone: getFieldValue("phone") || null,
      address_line_1: getFieldValue("address_line_1") || null,
      address_line_2: getFieldValue("address_line_2") || null,
      city: getFieldValue("city") || null,
      postal_code: getFieldValue("postal_code") || null,
      date_of_birth: getFieldValue("date_of_birth") || null,
      joined_on: getFieldValue("joined_on") || undefined,
      expires_on: getFieldValue("expires_on") || null,
      status: getFieldValue("status") as MemberStatus,
      notes: getFieldValue("notes") || null,
    };

    if (!payload.card_number || !payload.first_name || !payload.last_name) {
      setFormError("Card number, first name, and last name are required.");
      return;
    }

    try {
      const member = await createMemberMutation.mutateAsync(payload);
      router.push(`/members/${member.id}`);
    } catch (error) {
      setFormError(
        error instanceof ApiError
          ? error.message
          : "Could not create the member.",
      );
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Add a member</h1>
        <p className="text-muted-foreground text-sm">
          Fields marked * are required.
        </p>
      </header>

      {formError && <FieldError>{formError}</FieldError>}

      <FieldSet disabled={createMemberMutation.isPending} className="gap-6">
        {fieldGroups.map((group) => (
          <FieldSet key={group.title}>
            <FieldLegend>{group.title}</FieldLegend>
            <FieldGroup className="grid gap-5 sm:grid-cols-2">
              {group.fields.map(
                ({ name, label, description, ...inputProps }) => (
                  <Field key={name}>
                    <FieldLabel htmlFor={`member-${name}`}>
                      {label}
                      {inputProps.required ? " *" : ""}
                    </FieldLabel>
                    <Input
                      id={`member-${name}`}
                      name={name}
                      aria-describedby={
                        description ? `member-${name}-help` : undefined
                      }
                      {...inputProps}
                    />
                    {description && (
                      <FieldDescription id={`member-${name}-help`}>
                        {description}
                      </FieldDescription>
                    )}
                  </Field>
                ),
              )}
            </FieldGroup>
          </FieldSet>
        ))}

        <Field>
          <FieldLabel htmlFor="member-status">Status</FieldLabel>
          <Select name="status" items={statusOptions} defaultValue="active">
            <SelectTrigger id="member-status" className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {statusOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </Field>

        <Field>
          <FieldLabel htmlFor="member-notes">Notes</FieldLabel>
          <Textarea id="member-notes" name="notes" rows={4} />
        </Field>

        <div className="flex items-center gap-4">
          <Button type="submit" disabled={createMemberMutation.isPending}>
            {createMemberMutation.isPending ? "Saving..." : "Create member"}
          </Button>
          <Link
            href="/members"
            className="text-sm underline underline-offset-4"
          >
            Cancel
          </Link>
        </div>
      </FieldSet>
    </form>
  );
}
