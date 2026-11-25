"use client";

import { useId, useRef, useState } from "react";
import { FileText, UploadCloud, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const ACCEPT = ".pdf,.docx,.txt,application/pdf,text/plain,application/vnd.openxmlformats-officedocument.wordprocessingml.document";

export function formatBytes(n: number) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(0)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

/** Área de arrastar-e-soltar com fallback de clique e teclado (é um <label> do input). */
export function Dropzone({
  file,
  onFile,
  disabled,
}: {
  file: File | null;
  onFile: (f: File | null) => void;
  disabled?: boolean;
}) {
  const id = useId();
  const input = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);

  if (file) {
    return (
      <div className="flex items-center gap-3 rounded-lg border bg-muted/50 p-3">
        <span className="grid size-10 shrink-0 place-items-center rounded-md bg-brand-soft text-brand">
          <FileText className="size-5" aria-hidden />
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">{file.name}</p>
          <p className="text-xs text-muted-foreground">{formatBytes(file.size)}</p>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          aria-label="Remover arquivo"
          disabled={disabled}
          onClick={() => {
            onFile(null);
            if (input.current) input.current.value = "";
          }}
        >
          <X />
        </Button>
      </div>
    );
  }

  return (
    <label
      htmlFor={id}
      onDragOver={(e) => {
        e.preventDefault();
        setOver(true);
      }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setOver(false);
        const f = e.dataTransfer.files?.[0];
        if (f) onFile(f);
      }}
      className={cn(
        "flex cursor-pointer flex-col items-center gap-3 rounded-lg border border-dashed border-input px-4 py-10 text-center transition-colors",
        "hover:border-brand/60 hover:bg-brand-soft/40 has-[:focus-visible]:border-ring has-[:focus-visible]:ring-[3px] has-[:focus-visible]:ring-ring/30",
        over && "border-brand bg-brand-soft/60",
      )}
    >
      <span className="grid size-11 place-items-center rounded-full bg-brand-soft text-brand">
        <UploadCloud className="size-5" aria-hidden />
      </span>
      <span className="grid gap-1">
        <span className="text-sm font-medium">
          Arraste o arquivo aqui ou <span className="text-brand underline underline-offset-4">escolha no computador</span>
        </span>
        <span className="text-xs text-muted-foreground">PDF, DOCX ou TXT · até 50 MB</span>
      </span>
      <input
        ref={input}
        id={id}
        type="file"
        accept={ACCEPT}
        className="sr-only"
        disabled={disabled}
        onChange={(e) => onFile(e.target.files?.[0] ?? null)}
      />
    </label>
  );
}
