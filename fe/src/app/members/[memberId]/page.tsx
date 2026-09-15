import Link from "next/link";

import { MemberDetails } from "@/components/member-details";

type MemberPageProps = {
  params: Promise<{ memberId: string }>;
};

export default async function MemberPage({ params }: MemberPageProps) {
  const { memberId } = await params;

  return (
    <main className="mx-auto w-full max-w-3xl space-y-6 px-6 py-10">
      <Link href="/members" className="text-sm underline underline-offset-4">
        Back to members
      </Link>
      <MemberDetails key={memberId} memberId={memberId} />
    </main>
  );
}
