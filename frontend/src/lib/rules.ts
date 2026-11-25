/** Nomes e explicações das regras do motor, para leigos. Chave = `finding.rule` da API. */
export const RULES: Record<string, { label: string; description: string }> = {
  WHITE_TEXT: { label: "Texto branco", description: "Texto na mesma cor do fundo: invisível para pessoas, lido pela IA." },
  TRANSPARENT_TEXT: { label: "Texto transparente", description: "Texto com opacidade zero ou modo de renderização invisível." },
  TINY_FONT: { label: "Fonte minúscula", description: "Texto em tamanho tão pequeno que não é legível na tela ou impresso." },
  OFF_PAGE_TEXT: { label: "Texto fora da página", description: "Texto posicionado fora da área visível da página." },
  TEXT_UNDER_IMAGE: { label: "Texto sob imagem", description: "Texto escondido atrás de uma imagem ou forma." },
  HIDDEN_LAYER: { label: "Camada oculta", description: "Conteúdo em camada (OCG) desligada por padrão." },
  HIDDEN_FORM_FIELD: { label: "Campo de formulário oculto", description: "Campo de formulário invisível com conteúdo." },
  HIDDEN_COMMENT: { label: "Comentário oculto", description: "Anotação ou comentário escondido no documento." },
  HIDDEN_DOCX_TEXT: { label: "Texto oculto (Word)", description: "Texto marcado como oculto, vanish ou em cor invisível no DOCX." },
  INVISIBLE_UNICODE: { label: "Caracteres invisíveis", description: "Caracteres Unicode de largura zero ou tags que escondem instruções." },
  BIDI_CONTROL: { label: "Controle bidirecional", description: "Caracteres que invertem a ordem do texto exibido (Trojan Source)." },
  PROMPT_INJECTION: { label: "Prompt injection", description: "Instruções dirigidas a modelos de IA para mudar o comportamento deles." },
  SENSITIVE_DATA: { label: "Dado sensível", description: "CPF, CNPJ, cartão, e-mail ou outro dado pessoal (LGPD)." },
  SUSPICIOUS_METADATA: { label: "Metadado suspeito", description: "Metadados com instruções, scripts ou conteúdo anômalo." },
  EMBEDDED_JAVASCRIPT: { label: "JavaScript embutido", description: "Código JavaScript dentro do PDF." },
  OPEN_ACTION: { label: "Ação automática", description: "Ação executada automaticamente ao abrir o documento." },
  EMBEDDED_FILE: { label: "Arquivo embutido", description: "Outro arquivo anexado dentro do documento." },
};

export function ruleInfo(rule: string) {
  return RULES[rule] ?? { label: rule.replaceAll("_", " ").toLowerCase(), description: "" };
}
