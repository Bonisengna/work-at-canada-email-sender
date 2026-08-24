"use client";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState(""); const [password, setPassword] = useState("");
  const [message, setMessage] = useState(""); const [loading, setLoading] = useState(false);
  async function authenticate(mode: "login" | "register", event: FormEvent) {
    event.preventDefault(); setLoading(true); setMessage("");
    try {
      const response = await fetch(`${API_URL}/auth/${mode}`, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({email, password})});
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ?? "Não foi possível autenticar.");
      localStorage.setItem("employ_research_access_token", data.access_token);
      router.push(mode === "register" ? "/onboarding" : "/dashboard");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Erro inesperado."); }
    finally { setLoading(false); }
  }
  return <section className="card"><h1>Employ Research</h1><p>Entre ou crie sua conta para começar.</p>
    <form className="stack"><label>E-mail<input type="email" value={email} onChange={e => setEmail(e.target.value)} required /></label>
    <label>Senha<input type="password" minLength={8} value={password} onChange={e => setPassword(e.target.value)} required /></label>
    {message && <p className="error" role="alert">{message}</p>}<div className="actions">
    <button disabled={loading} onClick={e => authenticate("login", e)}>Entrar</button>
    <button disabled={loading} className="secondary" onClick={e => authenticate("register", e)}>Criar conta</button>
    </div></form></section>;
}

