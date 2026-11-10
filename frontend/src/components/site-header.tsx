import Link from "next/link";

import { Logo } from "@/components/brand/logo";
import { ThemeToggle } from "@/components/theme-toggle";
import { Badge } from "@/components/ui/badge";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b bg-background/85 backdrop-blur supports-[backdrop-filter]:bg-background/70">
      <div className="mx-auto flex h-14 max-w-5xl items-center gap-3 px-4">
        <Link href="/" aria-label="Início" className="rounded-md outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50">
          <Logo />
        </Link>
        <Badge variant="outline" className="hidden sm:inline-flex">
          MVP
        </Badge>
        <nav className="ml-auto flex items-center gap-1 text-sm">
          <Link
            href="/"
            className="rounded-md px-3 py-2 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          >
            Novo scan
          </Link>
          <Link
            href="/design"
            className="hidden rounded-md px-3 py-2 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground sm:block"
          >
            Design system
          </Link>
          <ThemeToggle />
        </nav>
      </div>
    </header>
  );
}
