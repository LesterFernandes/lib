import { ArrowRightIcon, BookOpenIcon, UsersIcon } from "lucide-react";
import Link from "next/link";

const sections = [
  {
    href: "/books",
    title: "Books",
    description: "Browse the catalogue and add or update book records.",
    icon: BookOpenIcon,
  },
  {
    href: "/members",
    title: "Members",
    description: "Find members, manage loans, and review borrowing history.",
    icon: UsersIcon,
  },
];

export default function DashboardPage() {
  return (
    <main className="mx-auto w-full max-w-3xl space-y-8 px-6 py-10">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">
          Library dashboard
        </h1>
        <p className="text-muted-foreground text-sm">
          Manage your library&apos;s books and members.
        </p>
      </header>

      <nav aria-label="Library sections" className="grid gap-4 sm:grid-cols-2">
        {sections.map(({ href, title, description, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className="bg-card text-card-foreground hover:bg-muted/50 focus-visible:ring-ring rounded-lg border p-6 transition-colors outline-none focus-visible:ring-2 focus-visible:ring-offset-2"
          >
            <Icon
              aria-hidden="true"
              className="text-muted-foreground mb-5 size-6"
            />
            <div className="flex items-center justify-between gap-4">
              <h2 className="text-lg font-semibold">{title}</h2>
              <ArrowRightIcon aria-hidden="true" className="size-4 shrink-0" />
            </div>
            <p className="text-muted-foreground mt-2 text-sm leading-relaxed">
              {description}
            </p>
          </Link>
        ))}
      </nav>
    </main>
  );
}
