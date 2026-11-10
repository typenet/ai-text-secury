import { Badge } from "@/components/ui/badge";
import type { RiskBand, Severity } from "@/lib/api";

const BAND_LABEL: Record<RiskBand, string> = {
  safe: "Seguro",
  attention: "Atenção",
  high: "Alto risco",
  critical: "Crítico",
};

const SEVERITY_BAND: Record<Severity, RiskBand> = {
  LOW: "safe",
  MEDIUM: "attention",
  HIGH: "high",
  CRITICAL: "critical",
};

const SEVERITY_LABEL: Record<Severity, string> = {
  LOW: "Baixa",
  MEDIUM: "Média",
  HIGH: "Alta",
  CRITICAL: "Crítica",
};

export function RiskBadge({ band }: { band: RiskBand }) {
  return <Badge variant={band}>{BAND_LABEL[band]}</Badge>;
}

export function SeverityBadge({ severity }: { severity: Severity }) {
  return <Badge variant={SEVERITY_BAND[severity]}>{SEVERITY_LABEL[severity]}</Badge>;
}
