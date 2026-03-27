"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";
import { createClient } from "@/lib/supabase/client";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const nextPath = useMemo(() => searchParams.get("next") || "/dashboard", [searchParams]);

  const onLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsLoading(true);

    const supabase = createClient();
    const { error: signInError } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    setIsLoading(false);

    if (signInError) {
      setError(signInError.message);
      return;
    }

    router.replace(nextPath);
    router.refresh();
  };

  const onOAuth = async (provider: "google" | "github") => {
    setError(null);
    const supabase = createClient();
    const redirectTo = `${window.location.origin}/auth/callback?next=${encodeURIComponent(nextPath)}`;

    const { error: oauthError } = await supabase.auth.signInWithOAuth({
      provider,
      options: { redirectTo },
    });

    if (oauthError) {
      setError(oauthError.message);
    }
  };

  return (
    <section className="card">
      <h1>Iniciar sesión</h1>
      <p>Accede con email/contraseña o con tu proveedor OAuth.</p>

      <form onSubmit={onLogin}>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          autoComplete="email"
        />

        <label htmlFor="password" style={{ marginTop: "0.75rem" }}>
          Contraseña
        </label>
        <input
          id="password"
          type="password"
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="current-password"
        />

        <button className="btn-primary" disabled={isLoading} style={{ marginTop: "1rem", width: "100%" }}>
          {isLoading ? "Ingresando..." : "Grabar audio"}
        </button>
      </form>

      <div className="row" style={{ marginTop: "1rem" }}>
        <button className="btn-secondary" onClick={() => onOAuth("google")}>
          Continuar con Google
        </button>
        <button className="btn-secondary" onClick={() => onOAuth("github")}>
          Continuar con GitHub
        </button>
      </div>

      {error ? <p className="error">{error}</p> : null}

      <p className="small" style={{ marginTop: "1rem" }}>
        ¿No tienes cuenta? <Link className="link" href="/register">Regístrate aquí</Link>
      </p>
    </section>
  );
}
