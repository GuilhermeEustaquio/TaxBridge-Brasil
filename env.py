"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Spinner } from "@/components/ui/primitives";
import { tokenStore } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  useEffect(() => {
    router.replace(tokenStore.access ? "/dashboard" : "/login");
  }, [router]);
  return <Spinner />;
}
