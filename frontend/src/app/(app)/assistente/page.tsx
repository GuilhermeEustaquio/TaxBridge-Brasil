"use client";

import { useMutation } from "@tanstack/react-query";
import { Bot, Send, User as UserIcon } from "lucide-react";
import { useRef, useState } from "react";
import { CompanySelect, useSelectedCompany } from "@/components/company-select";
import { Button, Card, InlineAlert, Input, PageHeader } from "@/components/ui/primitives";
import { api } from "@/lib/api";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface ChatResponse {
  conversation_id: string;
  answer: string;
  disclaimer: string;
  model: string | null;
}

const SUGGESTIONS = [
  "Qual o impacto da reforma na minha empresa em 2033?",
  "Quais itens precisam de reajuste de preço?",
  "Explique o cálculo da CBS no ano-teste de 2026.",
  "O que falta no meu checklist de adequação?",
];

export default function AssistentePage() {
  const { companies, companyId, select } = useSelectedCompany();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [disclaimer, setDisclaimer] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const send = useMutation({
    mutationFn: (message: string) =>
      api<ChatResponse>("/ai/chat", {
        method: "POST",
        body: JSON.stringify({
          message,
          conversation_id: conversationId,
          company_id: companyId || null,
        }),
      }),
    onSuccess: (response) => {
      setConversationId(response.conversation_id);
      setDisclaimer(response.disclaimer);
      setMessages((current) => [...current, { role: "assistant", content: response.answer }]);
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
    },
    onError: (error: Error) =>
      setMessages((current) => [...current, { role: "assistant", content: `Erro: ${error.message}` }]),
  });

  function submit(text?: string) {
    const message = (text ?? input).trim();
    if (!message || send.isPending) return;
    setMessages((current) => [...current, { role: "user", content: message }]);
    setInput("");
    send.mutate(message);
  }

  return (
    <div>
      <PageHeader
        title="Assistente de IA tributário"
        description="Responde com base nos dados da SUA organização (simulações, regras, premissas e checklist). Não inventa legislação."
        actions={<CompanySelect companies={companies} value={companyId} onChange={select} />}
      />

      <Card className="flex h-[65vh] flex-col">
        <div className="flex-1 space-y-4 overflow-y-auto pr-1">
          {messages.length === 0 && (
            <div className="flex h-full flex-col items-center justify-center gap-4">
              <Bot className="h-10 w-10 text-slate-300" />
              <p className="text-sm text-slate-500">Pergunte sobre o impacto da reforma na sua operação.</p>
              <div className="flex max-w-xl flex-wrap justify-center gap-2">
                {SUGGESTIONS.map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => submit(suggestion)}
                    className="rounded-full border border-slate-200 px-3 py-1.5 text-xs text-slate-600 hover:border-brand-400 hover:text-brand-600 dark:border-slate-600 dark:text-slate-300"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((message, index) => (
            <div key={index} className={`flex gap-2 ${message.role === "user" ? "justify-end" : ""}`}>
              {message.role === "assistant" && (
                <div className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-600 text-white">
                  <Bot className="h-4 w-4" />
                </div>
              )}
              <div
                className={`max-w-[80%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                  message.role === "user"
                    ? "bg-brand-600 text-white"
                    : "bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-100"
                }`}
              >
                {message.content}
              </div>
              {message.role === "user" && (
                <div className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-300 text-slate-600 dark:bg-slate-600 dark:text-slate-200">
                  <UserIcon className="h-4 w-4" />
                </div>
              )}
            </div>
          ))}
          {send.isPending && (
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <Bot className="h-4 w-4 animate-pulse" /> analisando seus dados...
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {disclaimer && (
          <div className="mt-3">
            <InlineAlert tone="info">{disclaimer}</InlineAlert>
          </div>
        )}

        <form
          onSubmit={(event) => {
            event.preventDefault();
            submit();
          }}
          className="mt-3 flex gap-2"
        >
          <Input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ex.: Por que minha carga aumenta em 2027?"
          />
          <Button type="submit" loading={send.isPending} disabled={!input.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </Card>
    </div>
  );
}
