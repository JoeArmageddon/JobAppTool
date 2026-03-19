import { auth } from "@clerk/nextjs/server";
import { FileText, Briefcase, KanbanSquare, TrendingUp } from "lucide-react";

export default async function DashboardPage() {
  const { userId } = auth();

  const stats = [
    { label: "Resume Score", value: "—", icon: FileText, color: "text-primary" },
    { label: "Jobs Found", value: "—", icon: Briefcase, color: "text-success" },
    { label: "Applications", value: "—", icon: KanbanSquare, color: "text-warning" },
    { label: "Response Rate", value: "—", icon: TrendingUp, color: "text-success" },
  ];

  return (
    <div className="p-8">
      <h1 className="text-2xl font-semibold text-foreground mb-1">Dashboard</h1>
      <p className="text-sm text-muted-foreground mb-8">
        Your job search at a glance.
      </p>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
        {stats.map(({ label, value, icon: Icon, color }) => (
          <div
            key={label}
            className="bg-surface border border-border rounded-lg p-4"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs text-muted-foreground uppercase tracking-wide">
                {label}
              </span>
              <Icon className={`w-4 h-4 ${color}`} />
            </div>
            <div className="text-2xl font-mono font-semibold text-foreground">
              {value}
            </div>
          </div>
        ))}
      </div>

      <div className="bg-surface border border-border rounded-lg p-6">
        <h2 className="text-sm font-semibold text-foreground mb-2">Getting Started</h2>
        <ol className="space-y-2 text-sm text-muted-foreground list-decimal list-inside">
          <li>
            <span className="text-foreground">Upload your resume</span> — get an AI score + improvement tips
          </li>
          <li>
            <span className="text-foreground">Set up your Hunt Profile</span> — target titles, locations, salary
          </li>
          <li>
            <span className="text-foreground">Let AutoApply find jobs</span> — scraped every 6 hours
          </li>
          <li>
            <span className="text-foreground">Review tailored applications</span> — or enable auto-apply
          </li>
        </ol>
      </div>
    </div>
  );
}
