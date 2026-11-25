import { cn } from "@/lib/utils";

/** Barra simples (0-100). `indicatorClassName` define a cor, ex.: "bg-risk-high". */
function Progress({
  value,
  className,
  indicatorClassName,
  ...props
}: React.ComponentProps<"div"> & { value: number; indicatorClassName?: string }) {
  const v = Math.max(0, Math.min(100, value));
  return (
    <div
      data-slot="progress"
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={v}
      className={cn("h-1.5 w-full overflow-hidden rounded-full bg-muted", className)}
      {...props}
    >
      <div className={cn("h-full rounded-full bg-primary transition-[width]", indicatorClassName)} style={{ width: `${v}%` }} />
    </div>
  );
}

export { Progress };
