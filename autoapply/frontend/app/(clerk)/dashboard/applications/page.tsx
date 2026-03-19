"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { Loader2 } from "lucide-react";
import { KanbanBoard } from "@/components/applications/KanbanBoard";
import { listApplications, updateApplicationStatus } from "@/lib/api";
import { Application, ApplicationStatus } from "@/lib/types";

export default function ApplicationsPage() {
  const { getToken } = useAuth();
  const [apps, setApps] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const token = await getToken();
      if (!token) return;
      const data = await listApplications(token);
      setApps(data);
      setLoading(false);
    })();
  }, [getToken]);

  const handleStatusChange = async (id: string, status: ApplicationStatus) => {
    const token = await getToken();
    if (!token) return;
    const updated = await updateApplicationStatus(token, id, status);
    setApps((prev) => prev.map((a) => (a.id === id ? updated : a)));
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center gap-2 text-muted-foreground">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span className="text-sm">Loading applications…</span>
      </div>
    );
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-semibold text-foreground mb-1">Applications</h1>
      <p className="text-sm text-muted-foreground mb-6">
        {apps.length} total applications tracked
      </p>
      <KanbanBoard applications={apps} onStatusChange={handleStatusChange} />
    </div>
  );
}
