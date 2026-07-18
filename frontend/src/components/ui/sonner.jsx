import { Toaster as Sonner, toast } from "sonner"

// Pinned to dark, not read from next-themes. The app has no ThemeProvider
// (and never sets `.dark` — see CLAUDE.md), so `useTheme()` resolved to
// "system" and followed the OS: anyone on a light desktop got white toasts
// floating over a permanently-navy app. The theme here is not a user choice,
// so neither is this.
const Toaster = ({
  ...props
}) => {
  return (
    <Sonner
      theme="dark"
      className="toaster group"
      toastOptions={{
        classNames: {
          toast:
            "group toast group-[.toaster]:bg-background group-[.toaster]:text-foreground group-[.toaster]:border-border group-[.toaster]:shadow-lg",
          description: "group-[.toast]:text-muted-foreground",
          actionButton:
            "group-[.toast]:bg-primary group-[.toast]:text-primary-foreground",
          cancelButton:
            "group-[.toast]:bg-muted group-[.toast]:text-muted-foreground",
        },
      }}
      {...props} />
  );
}

export { Toaster, toast }
