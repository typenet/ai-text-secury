import { OctagonAlert, TriangleAlert, ShieldAlert, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { RiskBand, Severity } from "@/lib/api";

/** Tudo o que a interface precisa saber sobre cada faixa de risco, num lugar só. */
export const BANDS: Record<
  RiskBand,
  { label: string; range: string; verdict: string; action: string; icon: typeof ShieldCheck }
> = {
  safe: {
    label: "Seguro",
    range: "0–20",
    verdict: "Nenhum risco relevante encontrado",
    action: "Pode seguir para indexação ou uso pela IA.",
    icon: ShieldCheck,
  },
  attention: {
    label: "Atenção",
    range: "21–50",
    verdict: "Há sinais que merecem revisão",
    action: "Revise os achados antes de liberar o documento.",
    icon: TriangleAlert,
  },
  high: {
    label: "Alto risco",
    range: "51–80",
    verdict: "Conteúdo oculto ou manipulação provável",
    action: "Não envie para a IA sem tratar os achados.",
    icon: ShieldAlert,
  },
  critical: {
    label: "Crítico",
    range: "81–100",
    verdict: "Documento com ataque ou risco grave",
    action: "Bloqueie o documento e acione a equipe de segurança.",
    icon: OctagonAlert,
  },
};

export const BAND_ORDER: RiskBand[] = ["safe", "attention", "high", "critical"];

export const SEVERITY_BAND: Record<Severity, RiskBand> = {
  LOW: "safe",
  MEDIUM: "attention",
  HIGH: "high",
  CRITICAL: "critical",
};

export const SEVERITY_LABEL: Record<Severity, string> = {
  LOW: "Baixa",
  MEDIUM: "Média",
  HIGH: "Alta",
  CRITICAL: "Crítica",
};

export const SEVERITY_ORDER: Severity[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];

/** Classe de cor sólida (bg-*) por faixa — escrita por extenso para o Tailwind encontrar. */
export const BAND_BG: Record<RiskBand, string> = {
  safe: "bg-risk-safe",
  attention: "bg-risk-attention",
  high: "bg-risk-high",
  critical: "bg-risk-critical",
};

export function bandFor(score: number): RiskBand {
  if (score <= 20) return "safe";
  if (score <= 50) return "attention";
  if (score <= 80) return "high";
  return "critical";
}

export function RiskBadge({ band, className }: { band: RiskBand; className?: string }) {
  const Icon = BANDS[band].icon;
  return (
    <Badge variant={band} className={className}>
      <Icon aria-hidden />
      {BANDS[band].label}
    </Badge>
  );
}

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <Badge variant={SEVERITY_BAND[severity]}>
      <span aria-hidden className={`size-1.5 rounded-full ${BAND_BG[SEVERITY_BAND[severity]]}`} />
      {SEVERITY_LABEL[severity]}
    </Badge>
  );
}
