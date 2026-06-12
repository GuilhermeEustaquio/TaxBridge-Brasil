# API REST — v1

Base: `/api/v1` · Autenticação: `Authorization: Bearer <access_token>` · Swagger: `GET /docs` · OpenAPI: `GET /openapi.json`

Padrões: JSON; erros `{"detail": ...}`; paginação `?page=1&page_size=20` → `{items, total, page, page_size}`;
listas aceitam filtros específicos. Todas as rotas (exceto auth) são **escopadas pela organização do token**.

## Auth (`/auth`) — rate limit 10 req/min/IP
| Método | Rota | Descrição | Perfil |
|---|---|---|---|
| POST | `/auth/register` | Cria organização + usuário dono (aceite LGPD obrigatório) | público |
| POST | `/auth/login` | Retorna `access_token` + `refresh_token` | público |
| POST | `/auth/refresh` | Novo par de tokens a partir do refresh | público |
| GET | `/auth/me` | Usuário corrente + organização + permissões | qualquer |
| POST | `/auth/logout` | Registra logout em auditoria | qualquer |

## Organização e premissas (`/organizations`)
| GET | `/organizations/me` | Dados + premissas | qualquer |
| PUT | `/organizations/assumptions` | Atualiza premissas configuráveis | admin_global, dono_conta, contador |

## Empresas (`/companies`)
| GET/POST | `/companies` | Lista (filtros `search`, `uf`, `tax_regime`) / cria | leitura: todos · escrita: admin, dono, contador, fiscal |
| GET/PUT/DELETE | `/companies/{id}` | Detalhe / atualiza / soft delete | idem (delete: admin, dono) |
| GET/POST | `/companies/{id}/branches` | Filiais | idem |
| DELETE | `/companies/{id}/branches/{branch_id}` | Remove filial | admin, dono, contador |
| POST | `/companies/{id}/diagnostico` | ★ Diagnóstico 1-clique: roda simulação completa default | admin, dono, contador, fiscal |

## Usuários e perfis (`/users`, `/roles`)
| GET/POST | `/users` | Lista / convida (senha temporária retornada 1x) | admin, dono |
| PUT | `/users/{id}` | Papel, ativo/inativo, nome | admin, dono |
| GET | `/roles` | Perfis disponíveis | qualquer |

## Catálogo (`/products`, `/services`)
| GET/POST | `/products` | Filtros `company_id`, `search`, `ncm`, `uf` / cria | escrita: admin, dono, contador, fiscal |
| PUT/DELETE | `/products/{id}` | Atualiza / soft delete | idem |
| POST | `/products/import-csv` | Multipart `file` + `company_id`; valida linha a linha | idem |
| GET | `/products/csv-template` | Template CSV | qualquer |
| (idem) | `/services...` | Mesmo contrato com campos NBS/LC116 | idem |

## Motor tributário (`/tax-rules`, `/transition-years`)
| GET/POST | `/tax-rules` | Regras (filtros `company_id`, `item_kind`, `active`) | escrita: admin, dono, contador, fiscal |
| PUT/DELETE | `/tax-rules/{id}` | Atualiza / desativa | idem |
| GET | `/transition-years` | Fatores 2026–2033 da organização | qualquer |
| PUT | `/transition-years/{year}` | Edita fatores do ano (parametrização sem deploy) | admin, dono, contador |

## Simulações (`/simulations`)
| GET/POST | `/simulations` | Lista / **executa** (empresa, anos, cenário, overrides) | escrita: admin, dono, contador, fiscal, financeiro, consultor |
| GET | `/simulations/{id}` | Resumo por ano + premissas snapshot | qualquer |
| GET | `/simulations/{id}/items?year=&search=&page=` | Itens com memória de cálculo | qualquer |
| DELETE | `/simulations/{id}` | Soft delete | admin, dono, contador |
| GET | `/simulations/{id}/export.pdf` | ★ Relatório executivo PDF (registra em `reports`) | qualquer |
| GET | `/simulations/{id}/export.xlsx` / `.csv` | Planilhas detalhadas | qualquer |

## Compliance (`/compliance`)
| GET/POST | `/compliance/tasks` | Filtros `company_id`, `area`, `status` / cria | escrita: todos exceto leitor |
| PUT/DELETE | `/compliance/tasks/{id}` | Atualiza status/responsável/prazo / remove | idem |
| POST | `/compliance/apply-template` | Aplica checklist padrão da Reforma à empresa | admin, dono, contador |
| GET | `/compliance/summary?company_id=` | Maturidade % por área + atrasadas | qualquer |

## Monitor legislativo (`/legal-updates`)
| GET/POST | `/legal-updates` | Feed (filtros `impact`, `norm_type`, `search`) / cadastra | escrita: admin, dono, contador, fiscal |
| PUT/DELETE | `/legal-updates/{id}` | Atualiza / remove | idem |

## Dashboard (`/dashboard`)
| GET | `/dashboard?company_id=` | Payload consolidado: KPIs, série anual atual×futura, top itens impactados, alertas de risco, maturidade compliance, status de onboarding | qualquer |

## Relatórios (`/reports`)
| GET | `/reports` | Histórico de relatórios gerados (com premissas) | qualquer |

## IA assistente (`/ai`) — fase 4 (stub funcional)
| POST | `/ai/chat` | Pergunta sobre dados da org; responde com contexto de simulações/regras. Sem `ANTHROPIC_API_KEY`: resposta estruturada offline com disclaimers | todos exceto leitor |
| GET | `/ai/conversations` | Histórico | qualquer |

## Auditoria (`/audit-logs`)
| GET | `/audit-logs?user_id=&action=&entity_type=&date_from=&date_to=` | Trilha completa | admin, dono, contador |

## Integrações (`/api-keys`) — fundação da fase 5
| GET/POST | `/api-keys` | Lista / cria (segredo exibido 1x; hash armazenado) | admin, dono |
| DELETE | `/api-keys/{id}` | Revoga | admin, dono |

## Saúde
| GET | `/health` | Liveness/readiness (sem auth) | público |
