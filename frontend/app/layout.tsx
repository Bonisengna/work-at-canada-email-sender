import Link from "next/link";
import "./globals.css";
export const metadata = { title: "Employ Research", description: "Busca e candidatura a vagas" };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="pt-BR"><body><main><nav className="nav" aria-label="Navegação principal">
    <Link href="/">Entrar</Link><Link href="/onboarding">Onboarding</Link>
    <Link href="/dashboard">Dashboard</Link><Link href="/ajustes">Ajustes</Link>
  </nav>{children}</main></body></html>;
}

