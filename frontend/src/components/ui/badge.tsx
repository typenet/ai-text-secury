import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center justify-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium whitespace-nowrap [&_svg]:size-3",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground",
        secondary: "border-transparent bg-secondary text-secondary-foreground",
        outline: "text-muted-foreground",
        brand: "border-brand/25 bg-brand-soft text-brand",
        safe: "border-risk-safe/30 bg-risk-safe-soft text-risk-safe-fg",
        attention: "border-risk-attention/40 bg-risk-attention-soft text-risk-attention-fg",
        high: "border-risk-high/30 bg-risk-high-soft text-risk-high-fg",
        critical: "border-risk-critical/30 bg-risk-critical-soft text-risk-critical-fg",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

function Badge({ className, variant, ...props }: React.ComponentProps<"span"> & VariantProps<typeof badgeVariants>) {
  return <span data-slot="badge" className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
