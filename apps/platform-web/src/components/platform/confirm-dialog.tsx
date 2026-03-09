import type { ReactNode } from "react";

type ConfirmDialogProps = {
  open: boolean;
  title: string;
  description?: ReactNode;
  confirmLabel?: string;
  confirmLabelLoading?: string;
  cancelLabel?: string;
  loading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
};

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = "Confirm",
  confirmLabelLoading = "Processing...",
  cancelLabel = "Cancel",
  loading = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="w-full max-w-md rounded-lg border border-border bg-card p-4 shadow-xl"
      >
        <h3 className="text-base font-semibold">{title}</h3>
        {description ? <div className="text-muted-foreground mt-2 text-sm">{description}</div> : null}
        <div className="mt-4 flex items-center justify-end gap-2">
          <button
            type="button"
            className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-background px-3 text-sm"
            onClick={onCancel}
            disabled={loading}
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            className="inline-flex h-9 items-center justify-center rounded-md border border-destructive/40 bg-destructive/5 px-3 text-sm font-medium text-destructive disabled:opacity-50"
            onClick={onConfirm}
            disabled={loading}
          >
            {loading ? confirmLabelLoading : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
