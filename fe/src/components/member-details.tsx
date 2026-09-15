"use client";

import Link from "next/link";
import { ChevronDownIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { FieldError } from "@/components/ui/field";
import { useMember } from "@/hooks/use-library";
import { cn } from "@/lib/utils";

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
  const loans = [...member.loans].sort(
    (first, second) =>
      new Date(first.borrowed_at).getTime() -
        new Date(second.borrowed_at).getTime() ||
      first.id.localeCompare(second.id),
  );
  const currentLoanCount = loans.filter(
    (loan) => loan.returned_at === null,
  ).length;

  return (
    <div className="space-y-8">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">
          {member.first_name} {member.last_name}
        </h1>
        <p className="text-muted-foreground text-sm">
          Card {member.card_number}
        </p>
      </header>

      <Collapsible className="rounded-lg border">
        <h2>
          <CollapsibleTrigger className="group hover:bg-muted/50 focus-visible:ring-ring flex w-full items-center justify-between gap-4 rounded-lg p-4 text-left font-medium outline-none focus-visible:ring-2">
            Member details
            <ChevronDownIcon
              aria-hidden="true"
              className="size-4 shrink-0 transition-transform group-data-panel-open:rotate-180"
            />
          </CollapsibleTrigger>
        </h2>
        <CollapsibleContent>
          <dl className="grid gap-x-8 gap-y-5 border-t p-4 sm:grid-cols-2">
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
        </CollapsibleContent>
      </Collapsible>

      <section aria-labelledby="member-loans-heading" className="space-y-3">
        <header className="flex flex-wrap items-center justify-between gap-2">
          <div className="space-y-1">
            <h2 id="member-loans-heading" className="text-lg font-semibold">
              Borrowing history
            </h2>
            {loans.length > 0 && (
              <p className="text-muted-foreground text-sm">Oldest to newest</p>
            )}
          </div>
          <span
            className={cn(
              "rounded-full px-3 py-1 text-sm font-medium",
              currentLoanCount > 0
                ? "bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-200"
                : "bg-muted text-muted-foreground",
            )}
          >
            {currentLoanCount} current{" "}
            {currentLoanCount === 1 ? "loan" : "loans"}
          </span>
        </header>
        {loans.length === 0 ? (
          <p className="text-muted-foreground text-sm">
            No borrowing history yet.
          </p>
        ) : (
          <ol className="space-y-3">
            {loans.map((loan) => (
              <li
                key={loan.id}
                className={cn(
                  "space-y-2 rounded-lg border p-4",
                  loan.returned_at === null &&
                    "border-amber-300 bg-amber-50 dark:border-amber-800 dark:bg-amber-950/40",
                )}
              >
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <Link
                    href={`/books/${loan.book.id}`}
                    className="font-medium underline underline-offset-4"
                  >
                    {loan.book.title}
                  </Link>
                  <span
                    className={cn(
                      "text-sm font-medium",
                      loan.returned_at === null
                        ? "text-amber-900 dark:text-amber-200"
                        : "text-muted-foreground",
                    )}
                  >
                    {loan.returned_at === null ? "Current loan" : "Returned"}
                  </span>
                </div>
                <p className="text-muted-foreground text-sm">
                  Borrowed{" "}
                  <time dateTime={loan.borrowed_at}>
                    {new Date(loan.borrowed_at).toLocaleString()}
                  </time>
                </p>
                {loan.returned_at !== null && (
                  <p className="text-muted-foreground text-sm">
                    Returned{" "}
                    <time dateTime={loan.returned_at}>
                      {new Date(loan.returned_at).toLocaleString()}
                    </time>
                  </p>
                )}
              </li>
            ))}
          </ol>
        )}
      </section>
    </div>
  );
}
