import { cn } from "@/lib/utils";

/** Marca: escudo com linhas de documento e uma linha de varredura (o "scan"). */
export function LogoMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" aria-hidden className={cn("size-7", className)}>
      <path
        d="M16 2.5 4.5 6.8v8.4c0 7 4.8 12.4 11.5 14.3 6.7-1.9 11.5-7.3 11.5-14.3V6.8L16 2.5Z"
        className="fill-primary"
      />
      <path d="M10.5 11h11M10.5 15h11M10.5 19h7" className="stroke-primary-foreground/70" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M7.5 23.2h17" className="stroke-brand" strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  );
}

export function Logo({ className }: { className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <LogoMark />
      <span className="text-[15px] font-semibold tracking-tight">
        AI Text <span className="text-brand">Secury</span>
      </span>
    </span>
  );
}
