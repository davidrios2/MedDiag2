"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { createClient } from "@/lib/supabase/client";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const onRegister = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setIsLoading(true);

    const supabase = createClient();
    const redirectTo = `${window.location.origin}/auth/callback?next=/dashboard`;

    const { error: signUpError } = await supabase.auth.signUp({
      email,
      password,
      options: { emailRedirectTo: redirectTo },
    });

    setIsLoading(false);

    if (signUpError) {
      setError(signUpError.message);
      return;
    }

    setMessage("Cuenta creada. Si tu proyecto exige verificación por email, revisa tu correo.");
    router.replace("/dashboard");
    router.refresh();
  };

  return (
    <section className="card">
      <h1>Crear cuenta</h1>
      <p>Regístrate para acceder a las rutas privadas de MedDiag.</p>

      <form onSubmit={onRegister}>
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
          minLength={6}
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="new-password"
        />

        <button className="btn-primary" disabled={isLoading} style={{ marginTop: "1rem", width: "100%" }}>
          {isLoading ? "Creando cuenta..." : "Registrarme"}
        </button>
      </form>

      {error ? <p className="error">{error}</p> : null}
      {message ? <p className="small">{message}</p> : null}

      <p className="small" style={{ marginTop: "1rem" }}>
        ¿Ya tienes cuenta? <Link className="link" href="/login">Inicia sesión</Link>
      </p>
    </section>
  );
}
