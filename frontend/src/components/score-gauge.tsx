import { BANDS, bandFor } from "@/components/risk";
import { cn } from "@/lib/utils";

const STROKE: Record<string, string> = {
  safe: "stroke-risk-safe",
  attention: "stroke-risk-attention",
  high: "stroke-risk-high",
  critical: "stroke-risk-critical",
};

/**
 * Anel de 270° com o score 0-100. Marcas nos limites das faixas (20, 50, 80)
 * ajudam a ler "quão perto" o documento está da próxima faixa.
 */
export function ScoreGauge({ score, size = 168, className }: { score: number; size?: number; className?: string }) {
  const band = bandFor(score);
  const r = 44;
  const c = 2 * Math.PI * r;
  const arc = c * 0.75; // 270°
  const value = Math.max(0, Math.min(100, score));
  const tick = (v: number) => {
    const a = ((135 + (v / 100) * 270) * Math.PI) / 180;
    return { x1: 50 + 38 * Math.cos(a), y1: 50 + 38 * Math.sin(a), x2: 50 + 34.5 * Math.cos(a), y2: 50 + 34.5 * Math.sin(a) };
  };

  return (
    <div
      className={cn("relative grid place-items-center", className)}
      style={{ width: size, height: size }}
      role="img"
      aria-label={`Score de risco ${value} de 100, faixa ${BANDS[band].label}`}
    >
      <svg viewBox="0 0 100 100" className="absolute inset-0 size-full">
        <circle
          cx="50"
          cy="50"
          r={r}
          fill="none"
          strokeWidth="8"
          strokeLinecap="round"
          className="stroke-muted"
          strokeDasharray={`${arc} ${c}`}
          transform="rotate(135 50 50)"
        />
        <circle
          cx="50"
          cy="50"
          r={r}
          fill="none"
          strokeWidth="8"
          strokeLinecap="round"
          className={cn(STROKE[band], "transition-[stroke-dasharray] duration-700 ease-out")}
          strokeDasharray={`${Math.max(0.01, (value / 100) * arc)} ${c}`}
          transform="rotate(135 50 50)"
        />
        {[20, 50, 80].map((v) => (
          <line key={v} {...tick(v)} className="stroke-border" strokeWidth="1.5" strokeLinecap="round" />
        ))}
      </svg>
      <div className="grid justify-items-center leading-none">
        <span className="text-5xl font-semibold tracking-tight tabular-nums">{value}</span>
        <span className="mt-1.5 text-xs text-muted-foreground">de 100</span>
      </div>
    </div>
  );
}
