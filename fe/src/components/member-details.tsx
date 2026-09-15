"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import { FieldError } from "@/components/ui/field";
import { useMember } from "@/hooks/use-library";

export function MemberDetails({ memberId }: { memberId: string }) {
  const memberQuery = useMember(memberId);

  if (memberQuery.isPending) {
    return (
      <p role="status" className="text-muted-foreground text-sm">
        Loading member...
      </p>
    );
  }

  if (memberQuery.isError) {
    return (
      <div className="space-y-3">
        <FieldError>{memberQuery.error.message}</FieldError>
        <Button variant="outline" onClick={() => memberQuery.refetch()}>
          Try again
        </Button>
      </div>
    );
  }

  const member = memberQuery.data;
  const details = [
    ["Card number", member.card_number],
    ["Status", member.status],
    ["Email", member.email],
    ["Phone", member.phone],
    ["Address line 1", member.address_line_1],
    ["Address line 2", member.address_line_2],
    ["City", member.city],
    ["Postal code", member.postal_code],
    ["Date of birth", member.date_of_birth],
    ["Joining date", member.joined_on],
    ["Expiry date", member.expires_on],
  ];
  const loans = [...member.loans].sort((first, second) =>
    second.borrowed_at.localeCompare(first.borrowed_at),
  );

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold tracking-tight">
        {member.first_name} {member.last_name}
      </h1>

      <dl className="grid gap-x-8 gap-y-5 sm:grid-cols-2">
        {details.map(([label, value]) => (
          <div key={label}>
            <dt className="text-muted-foreground text-sm">{label}</dt>
            <dd className="mt-1 break-words">{value || "—"}</dd>
          </div>
        ))}
        <div className="sm:col-span-2">
          <dt className="text-muted-foreground text-sm">Notes</dt>
          <dd className="mt-1 break-words whitespace-pre-wrap">
            {member.notes || "—"}
          </dd>
        </div>
      </dl>

      <section aria-labelledby="member-loans-heading" className="space-y-3">
        <h2 id="member-loans-heading" className="text-lg font-semibold">
          Loans
        </h2>
        {loans.length === 0 ? (
          <p className="text-muted-foreground text-sm">No loans yet.</p>
        ) : (
          <ul className="divide-y">
            {loans.map((loan) => (
              <li key={loan.id} className="space-y-1 py-4">
                <Link
                  href={`/books/${loan.book_id}`}
                  className="font-medium underline underline-offset-4"
                >
                  {loan.book.title}
                </Link>
                <p className="text-muted-foreground text-sm">
                  Borrowed {new Date(loan.borrowed_at).toLocaleString()}
                </p>
                <p className="text-sm">
                  {loan.returned_at
                    ? `Returned ${new Date(loan.returned_at).toLocaleString()}`
                    : "On loan"}
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
