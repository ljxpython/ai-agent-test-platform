"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type UseResizableColumnsOptions = {
  minWidth?: number;
  storageKey?: string;
};

export function useResizableColumns(initialWidths: number[], options?: UseResizableColumnsOptions) {
  const minWidth = options?.minWidth ?? 96;
  const storageKey = options?.storageKey;

  const [columnWidths, setColumnWidths] = useState<number[]>(() => {
    if (!storageKey || typeof window === "undefined") {
      return initialWidths;
    }
    try {
      const raw = window.localStorage.getItem(storageKey);
      if (!raw) {
        return initialWidths;
      }
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed) || parsed.length !== initialWidths.length) {
        return initialWidths;
      }
      const normalized = parsed.map((value) => Number(value));
      if (normalized.some((value) => !Number.isFinite(value))) {
        return initialWidths;
      }
      return normalized;
    } catch {
      return initialWidths;
    }
  });
  const [resizingColumnIndex, setResizingColumnIndex] = useState<number | null>(null);

  const widthRef = useRef(columnWidths);
  const defaultWidthsRef = useRef(initialWidths);
  useEffect(() => {
    widthRef.current = columnWidths;
    if (!storageKey) {
      return;
    }
    window.localStorage.setItem(storageKey, JSON.stringify(columnWidths));
  }, [columnWidths, storageKey]);

  useEffect(() => {
    if (resizingColumnIndex === null) {
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      return;
    }
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    return () => {
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
  }, [resizingColumnIndex]);

  const startResize = useCallback(
    (columnIndex: number, event: React.MouseEvent<HTMLButtonElement>) => {
      event.preventDefault();
      const startX = event.clientX;
      const startWidth = widthRef.current[columnIndex] ?? minWidth;
      setResizingColumnIndex(columnIndex);

      const onMove = (moveEvent: MouseEvent) => {
        const delta = moveEvent.clientX - startX;
        const nextWidth = Math.max(minWidth, Math.round(startWidth + delta));
        setColumnWidths((prev) => {
          const next = [...prev];
          next[columnIndex] = nextWidth;
          return next;
        });
      };

      const onUp = () => {
        window.removeEventListener("mousemove", onMove);
        window.removeEventListener("mouseup", onUp);
        setResizingColumnIndex(null);
      };

      window.addEventListener("mousemove", onMove);
      window.addEventListener("mouseup", onUp);
    },
    [minWidth],
  );

  const resetColumnWidth = useCallback(
    (columnIndex: number) => {
      const defaultWidth = defaultWidthsRef.current[columnIndex] ?? minWidth;
      const normalized = Math.max(minWidth, Math.round(defaultWidth));
      setColumnWidths((prev) => {
        const next = [...prev];
        next[columnIndex] = normalized;
        return next;
      });
    },
    [minWidth],
  );

  return { columnWidths, startResize, resetColumnWidth, resizingColumnIndex };
}

export function ColumnResizeHandle({
  active = false,
  onDoubleClick,
  onMouseDown,
}: {
  active?: boolean;
  onDoubleClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onMouseDown: (event: React.MouseEvent<HTMLButtonElement>) => void;
}) {
  return (
    <button
      type="button"
      tabIndex={-1}
      aria-label="Resize column"
      className={`absolute right-0 top-0 h-full w-2 cursor-col-resize transition-colors ${active ? "bg-primary/45" : "bg-transparent hover:bg-primary/25"}`}
      onMouseDown={onMouseDown}
      onDoubleClick={onDoubleClick}
    />
  );
}
