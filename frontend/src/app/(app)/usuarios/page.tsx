"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, UserCheck, UserX } from "lucide-react";
import { useState } from "react";
import { Modal } from "@/components/ui/modal";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  Field,
  InlineAlert,
  Input,
  PageHeader,
  Select,
  Spinner,
} from "@/components/ui/primitives";
import { Table, TBody, Td, Th, THead } from "@/components/ui/table";
import { api } from "@/lib/api";
import { fmtDateTime } from "@/lib/format";
import { useAuth } from "@/lib/auth";
import type { Role, User } from "@/lib/types";

export default function UsuariosPage() {
  const queryClient = useQueryClient();
  const { user: currentUser } = useAuth();
  const [inviteOpen, setInviteOpen] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", role_slug: "fiscal" });
  const [tempPassword, setTempPassword] = useState("");
  const [error, setError] = useState("");

  const { data: users, isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: () => api<User[]>("/users"),
  });
  const { data: roles } = useQuery({
    queryKey: ["roles"],
    queryFn: () => api<Role[]>("/roles"),
  });

  const invite = useMutation({
    mutationFn: () =>
      api<{ user: User; temporary_password: string }>("/users", { method: "POST", body: JSON.stringify(form) }),
    onSuccess: (result) => {
      setTempPassword(result.temporary_password);
      setForm({ name: "", email: "", role_slug: "fiscal" });
      setError("");
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (err: Error) => setError(err.message),
  });

  const update = useMutation({
    mutationFn: ({ id, body }: { id: string; body: Record<string, unknown> }) =>
      api(`/users/${id}`, { method: "PUT", body: JSON.stringify(body) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users"] }),
  });

  const assignableRoles = (roles ?? []).filter((role) => role.slug !== "admin_global");

  return (
    <div>
      <PageHeader
        title="Usuários e permissões"
        description="Perfis com níveis de acesso: Dono da Conta, Contador, Fiscal, Financeiro, Consultor e Leitor."
        actions={
          <Button onClick={() => { setInviteOpen(true); setTempPassword(""); setError(""); }}>
            <Plus className="h-4 w-4" /> Convidar usuário
          </Button>
        }
      />

      <Card>
        {isLoading ? (
          <Spinner />
        ) : !users || users.length === 0 ? (
          <EmptyState title="Nenhum usuário" />
        ) : (
          <Table>
            <THead>
              <Th>Usuário</Th>
              <Th>E-mail</Th>
              <Th>Perfil</Th>
              <Th>Último acesso</Th>
              <Th>Status</Th>
              <Th right>Ações</Th>
            </THead>
            <TBody>
              {users.map((user) => (
                <tr key={user.id}>
                  <Td className="font-medium">
                    {user.name} {user.id === currentUser?.id && <Badge variant="info">você</Badge>}
                  </Td>
                  <Td className="text-xs">{user.email}</Td>
                  <Td>
                    <Select
                      value={user.role.slug}
                      onChange={(event) => update.mutate({ id: user.id, body: { role_slug: event.target.value } })}
                      disabled={user.id === currentUser?.id}
                      className="w-auto py-1 text-xs"
                    >
                      {assignableRoles.map((role) => (
                        <option key={role.slug} value={role.slug}>
                          {role.name}
                        </option>
                      ))}
                    </Select>
                  </Td>
                  <Td className="text-xs">{fmtDateTime(user.last_login_at)}</Td>
                  <Td>
                    <Badge variant={user.is_active ? "success" : "critico"}>
                      {user.is_active ? "Ativo" : "Inativo"}
                    </Badge>
                  </Td>
                  <Td right>
                    {user.id !== currentUser?.id && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => update.mutate({ id: user.id, body: { is_active: !user.is_active } })}
                        title={user.is_active ? "Desativar" : "Reativar"}
                      >
                        {user.is_active ? (
                          <UserX className="h-4 w-4 text-red-500" />
                        ) : (
                          <UserCheck className="h-4 w-4 text-emerald-500" />
                        )}
                      </Button>
                    )}
                  </Td>
                </tr>
              ))}
            </TBody>
          </Table>
        )}
      </Card>

      <Modal open={inviteOpen} onClose={() => setInviteOpen(false)} title="Convidar usuário">
        {tempPassword ? (
          <div className="space-y-3">
            <InlineAlert tone="success">
              Usuário criado! Compartilhe a senha temporária — ela é exibida <b>uma única vez</b>:
            </InlineAlert>
            <p className="rounded-lg bg-slate-100 p-3 text-center font-mono text-sm font-bold dark:bg-slate-900">
              {tempPassword}
            </p>
            <div className="flex justify-end">
              <Button onClick={() => setInviteOpen(false)}>Concluir</Button>
            </div>
          </div>
        ) : (
          <form
            onSubmit={(event) => {
              event.preventDefault();
              invite.mutate();
            }}
            className="space-y-3"
          >
            <Field label="Nome">
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
            </Field>
            <Field label="E-mail">
              <Input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
            </Field>
            <Field label="Perfil de acesso">
              <Select value={form.role_slug} onChange={(e) => setForm({ ...form, role_slug: e.target.value })}>
                {assignableRoles.map((role) => (
                  <option key={role.slug} value={role.slug}>
                    {role.name}
                  </option>
                ))}
              </Select>
            </Field>
            {error && <InlineAlert>{error}</InlineAlert>}
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="secondary" onClick={() => setInviteOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" loading={invite.isPending}>
                Convidar
              </Button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
}
