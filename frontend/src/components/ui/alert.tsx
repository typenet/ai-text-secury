import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const alertVariants = cva(
  "relative grid w-full grid-cols-[0_1fr] items-start gap-y-0.5 rounded-lg border px-4 py-3 text-sm has-[>svg]:grid-cols-[calc(var(--spacing)*4)_1fr] has-[>svg]:gap-x-3 [&>svg]:size-4 [&>svg]:translate-y-0.5 [&>svg]:text-current",
  {
    variants: {
      variant: {
        default: "bg-card text-card-foreground",
        brand: "border-brand/25 bg-brand-soft text-foreground [&>svg]:text-brand",
        destructive: "border-risk-critical/30 bg-risk-critical-soft text-risk-critical-fg",
        safe: "border-risk-safe/30 bg-risk-safe-soft text-risk-safe-fg",
        attention: "border-risk-attention/40 bg-risk-attention-soft text-risk-attention-fg",
        high: "border-risk-high/30 bg-risk-high-soft text-risk-high-fg",
        critical: "border-risk-critical/30 bg-risk-critical-soft text-risk-critical-fg",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

function Alert({ className, variant, ...props }: React.ComponentProps<"div"> & VariantProps<typeof alertVariants>) {
  return <div data-slot="alert" role="alert" className={cn(alertVariants({ variant }), className)} {...props} />;
}

function AlertTitle({ className, ...props }: React.ComponentProps<"div">) {
  return <div data-slot="alert-title" className={cn("col-start-2 font-medium leading-snug", className)} {...props} />;
}

function AlertDescription({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div data-slot="alert-description" className={cn("col-start-2 grid gap-1 text-sm opacity-90", className)} {...props} />
  );
}

export { Alert, AlertDescription, AlertTitle };
