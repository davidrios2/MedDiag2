import { redirect } from "next/navigation";
import { LogoutButton } from "@/components/logout-button";
import { getMyAudio } from "@/lib/api";
import { createClient } from "@/lib/supabase/server";

export default async function DashboardPage() {
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  const {
    data: { session },
  } = await supabase.auth.getSession();

  let audioError: string | null = null;
  let audioItems: Awaited<ReturnType<typeof getMyAudio>>["items"] = [];

  if (session?.access_token) {
    try {
      const audio = await getMyAudio(session.access_token);
      audioItems = audio.items;
    } catch (error) {
      audioError = error instanceof Error ? error.message : "No se pudo cargar /audio/me";
    }
  }

  return (
    <section className="card">
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1>Dashboard privado</h1>
          <p>Sesión activa: {user.email}</p>
        </div>
        <LogoutButton />
      </div>

      <h3 style={{ marginTop: "1.5rem" }}>Audio del usuario (/audio/me)</h3>
      {audioError ? <p className="error">{audioError}</p> : null}
      {!audioError && audioItems.length === 0 ? <p>No hay audios aún.</p> : null}

      {audioItems.length > 0 ? (
        <table className="table" aria-label="audio-records">
          <thead>
            <tr>
              <th>ID</th>
              <th>Archivo</th>
              <th>Estado</th>
              <th>Fecha</th>
            </tr>
          </thead>
          <tbody>
            {audioItems.map((item) => (
              <tr key={item.id}>
                <td>{item.id}</td>
                <td>{item.original_filename}</td>
                <td>{item.status}</td>
                <td>{new Date(item.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </section>
  );
}
