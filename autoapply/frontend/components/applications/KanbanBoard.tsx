"use client";

import { useState } from "react";
import { Application, ApplicationStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

const COLUMNS: { status: ApplicationStatus; label: string; color: string }[] = [
  { status: "queued", label: "Queued", color: "border-border" },
  { status: "applying", label: "Applying", color: "border-primary/40" },
  { status: "applied", label: "Applied", color: "border-primary" },
  { status: "viewed", label: "Viewed", color: "border-warning/60" },
  { status: "interview", label: "Interview", color: "border-success/60" },
  { status: "rejected", label: "Rejected", color: "border-danger/40" },
  { status: "offer", label: "Offer", color: "border-success" },
];

interface KanbanBoardProps {
  applications: Application[];
  onStatusChange?: (id: string, status: ApplicationStatus) => void;
}

function ApplicationCard({
  app,
  onStatusChange,
}: {
  app: Application;
  onStatusChange?: (id: string, status: ApplicationStatus) => void;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className="bg-background border border-border rounded-lg p-3 cursor-pointer
                 hover:border-primary/30 transition-colors"
      onClick={() => setExpanded((v) => !v)}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-xs font-medium text-foreground leading-tight">
            {app.job?.title ?? "Unknown Role"}
          </p>
          <p className="text-xs text-muted-foreground mt-0.5">{app.job?.company}</p>
        </div>
        {app.job?.match_score != null && (
          <span className="text-xs font-mono text-primary shrink-0">
            {Math.round(app.job.match_score)}%
          </span>
        )}
      </div>

      {expanded && (
        <div className="mt-3 pt-3 border-t border-border space-y-2">
          {app.cover_letter_text && (
            <div>
              <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">
                Cover Letter
              </p>
              <p className="text-xs text-foreground line-clamp-4">
                {app.cover_letter_text}
              </p>
            </div>
          )}
          <div className="flex flex-wrap gap-1 pt-1">
            {COLUMNS.map(({ status, label }) => (
              <button
                key={status}
                onClick={(e) => {
                  e.stopPropagation();
                  onStatusChange?.(app.id, status);
                }}
                className={cn(
                  "text-xs px-2 py-0.5 rounded border transition-colors",
                  app.status === status
                    ? "border-primary bg-primary/20 text-primary"
                    : "border-border text-muted-foreground hover:border-primary/30"
                )}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function KanbanBoard({ applications, onStatusChange }: KanbanBoardProps) {
  const byStatus = (status: ApplicationStatus) =>
    applications.filter((a) => a.status === status);

  return (
    <div className="flex gap-3 overflow-x-auto pb-4">
      {COLUMNS.map(({ status, label, color }) => {
        const apps = byStatus(status);
        return (
          <div
            key={status}
            className={cn(
              "shrink-0 w-52 rounded-lg border-t-2 bg-surface",
              color
            )}
          >
            <div className="px-3 py-2.5 border-b border-border flex items-center justify-between">
              <span className="text-xs font-medium text-foreground">{label}</span>
              <span className="text-xs font-mono text-muted-foreground bg-background px-1.5 py-0.5 rounded border border-border">
                {apps.length}
              </span>
            </div>
            <div className="p-2 space-y-2 min-h-[120px]">
              {apps.map((app) => (
                <ApplicationCard
                  key={app.id}
                  app={app}
                  onStatusChange={onStatusChange}
                />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
