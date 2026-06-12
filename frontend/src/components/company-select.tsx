"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Company, Page } from "@/lib/types";
import { Select } from "./ui/primitives";

export function useCompanies() {
  return useQuery({
    queryKey: ["companies", "all"],
    queryFn: () => api<Page<Company>>("/companies?page_size=200"),
  });
}

/** Seletor de empresa com persistência da escolha (localStorage). */
export function useSelectedCompany() {
  const { data, isLoading } = useCompanies();
  const [companyId, setCompanyId] = useState<string>("");

  useEffect(() => {
    if (!data) return;
    const stored = localStorage.getItem("tb_company");
    const valid = data.items.find((company) => company.id === stored);
    if (valid) setCompanyId(valid.id);
    else if (data.items.length > 0) setCompanyId(data.items[0].id);
  }, [data]);

  const select = (id: string) => {
    setCompanyId(id);
    localStorage.setItem("tb_company", id);
  };

  return { companies: data?.items ?? [], companyId, select, isLoading };
}

export function CompanySelect({
  companies,
  value,
  onChange,
  allowAll,
}: {
  companies: Company[];
  value: string;
  onChange: (id: string) => void;
  allowAll?: boolean;
}) {
  return (
    <Select value={value} onChange={(event) => onChange(event.target.value)} className="w-auto min-w-[220px]">
      {allowAll && <option value="">Todas as empresas</option>}
      {companies.map((company) => (
        <option key={company.id} value={company.id}>
          {company.trade_name || company.legal_name} · {company.uf}
        </option>
      ))}
    </Select>
  );
}
