import Link from "next/link";

import { MemberForm } from "@/components/member-form";

export default function AddMemberPage() {
  return (
    <main className="mx-auto w-full max-w-3xl space-y-6 px-6 py-10">
      <Link href="/members" className="text-sm underline underline-offset-4">
        Back to members
      </Link>
      <MemberForm />
    </main>
  );
}
