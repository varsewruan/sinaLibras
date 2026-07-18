import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva } from "class-variance-authority";

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground shadow hover:bg-primary/90",
        // Duolingo-style press effect: a 4px "front-face" border that
        // collapses when active, giving the button a physical depth feel.
        default3d:
          "bg-primary text-primary-foreground rounded-xl border-b-4 border-primary/40 hover:brightness-110 active:border-b-0 active:translate-y-1 transition-all",
        // Same 3D feel, blue-glow variant for hero CTAs.
        glow3d:
          "bg-primary text-primary-foreground rounded-xl border-b-4 border-primary/40 shadow-glow hover:shadow-glow-lg hover:brightness-110 active:border-b-0 active:translate-y-1 transition-all",
        // Accent variant (light blue) — used sparingly for secondary CTAs.
        accent3d:
          "bg-accent text-accent-foreground rounded-xl border-b-4 border-accent/40 shadow-glow hover:brightness-110 active:border-b-0 active:translate-y-1 transition-all",
        // Brand yellow, same 3D press. The "this is the reward / do this now"
        // button — one per screen, otherwise the yellow stops meaning anything.
        yellow3d:
          "bg-brand-yellow text-[#0d1c3d] rounded-xl border-b-4 border-brand-yellow-dark shadow-glow-yellow hover:brightness-105 active:border-b-0 active:translate-y-1 transition-all",
        destructive:
          "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90",
        outline:
          "border border-input shadow-sm hover:bg-accent hover:text-accent-foreground",
        secondary:
          "bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-8",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

const Button = React.forwardRef(({ className, variant, size, asChild = false, ...props }, ref) => {
  const Comp = asChild ? Slot : "button"
  return (
    <Comp
      className={cn(buttonVariants({ variant, size, className }))}
      ref={ref}
      {...props} />
  );
})
Button.displayName = "Button"

export { Button, buttonVariants }
