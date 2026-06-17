import Sidebar from "./Sidebar";

interface AppShellProps {
  children: React.ReactNode;
  title?: string;
}

export default function AppShell({ children, title }: AppShellProps) {
  return (
    <div className="flex flex-1">
      <Sidebar />
      <main className="flex-1 overflow-auto p-6">
        {title && (
          <h1 className="mb-6 text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
            {title}
          </h1>
        )}
        {children}
      </main>
    </div>
  );
}
