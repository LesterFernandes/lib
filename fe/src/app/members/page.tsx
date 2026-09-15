"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import { FieldError } from "@/components/ui/field";
import { useMembers } from "@/hooks/use-library";

export default function MembersPage() {
  const membersQuery = useMembers();

  return (
    <main className="mx-auto w-full max-w-3xl space-y-6 px-6 py-10">
      <header className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold tracking-tight">
          Active members
        </h1>
        <Link
          href="/members/add"
          className="text-sm underline underline-offset-4"
        >
          Add a member
        </Link>
      </header>

      {membersQuery.isPending ? (
        <p role="status" className="text-muted-foreground text-sm">
          Loading members...
        </p>
      ) : membersQuery.isError ? (
        <div className="space-y-3">
          <FieldError>{membersQuery.error.message}</FieldError>
          <Button variant="outline" onClick={() => membersQuery.refetch()}>
            Try again
          </Button>
        </div>
      ) : membersQuery.data.length === 0 ? (
        <p className="text-muted-foreground text-sm">No active members yet.</p>
      ) : (
        <ul className="divide-y">
          {membersQuery.data.map((member) => (
            <li
              key={member.id}
              className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 py-4"
            >
              <Link
                href={`/members/${member.id}`}
                className="font-medium underline underline-offset-4"
              >
                {member.first_name} {member.last_name}
              </Link>
              <span className="text-muted-foreground text-sm">
                Card {member.card_number}
              </span>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
