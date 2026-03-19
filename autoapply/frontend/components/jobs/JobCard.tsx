"use client";

import { useState } from "react";
import Image from "next/image";
import { MapPin, ExternalLink, Zap, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Job } from "@/lib/types";

interface JobCardProps {
  job: Job;
  onIgnore?: (id: string) => void;
  onTailor?: (job: Job) => void;
}

function ScoreBadge({ score }: { score?: number }) {
  if (score == null) return null;
  const color =
    score >= 80 ? "text-success bg-success/10 border-success/30"
    : score >= 60 ? "text-primary bg-primary/10 border-primary/30"
    : score >= 40 ? "text-warning bg-warning/10 border-warning/30"
    : "text-muted-foreground bg-white/5 border-border";
  return (
    <span className={cn("text-xs font-mono font-semibold px-1.5 py-0.5 rounded border", color)}>
      {Math.round(score)}%
    </span>
  );
}

export function JobCard({ job, onIgnore, onTailor }: JobCardProps) {
  const [loading, setLoading] = useState(false);

  const handleTailor = async () => {
    setLoading(true);
    await onTailor?.(job);
    setLoading(false);
  };

  return (
    <div className="bg-surface border border-border rounded-lg p-4 hover:border-primary/30 transition-colors group">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0">
          {/* Company logo */}
          <div className="w-9 h-9 rounded-md bg-background border border-border flex items-center justify-center shrink-0 overflow-hidden">
            <Image
              src={`https://logo.clearbit.com/${encodeURIComponent(job.company.toLowerCase().replace(/\s+/g, "") + ".com")}`}
              alt={job.company}
              width={36}
              height={36}
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = "none";
              }}
              unoptimized
            />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-medium text-foreground truncate">{job.title}</h3>
              <ScoreBadge score={job.match_score} />
            </div>
            <p className="text-xs text-muted-foreground">{job.company}</p>
          </div>
        </div>

        <div className="flex items-center gap-1 shrink-0">
          {job.source_url && (
            <a
              href={job.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="p-1.5 rounded hover:bg-white/5 text-muted-foreground hover:text-foreground transition-colors"
            >
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
          <button
            onClick={() => onIgnore?.(job.id)}
            className="p-1.5 rounded hover:bg-danger/10 text-muted-foreground hover:text-danger transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <div className="flex items-center gap-3 mt-3 text-xs text-muted-foreground">
        {job.location && (
          <span className="flex items-center gap-1">
            <MapPin className="w-3 h-3" />
            {job.location}
          </span>
        )}
        {(job.salary_min || job.salary_max) && (
          <span>
            {job.salary_min ? `$${(job.salary_min / 1000).toFixed(0)}k` : ""}
            {job.salary_max ? ` – $${(job.salary_max / 1000).toFixed(0)}k` : ""}
          </span>
        )}
        {job.source && (
          <span className="ml-auto font-mono bg-background px-1.5 py-0.5 rounded border border-border capitalize">
            {job.source}
          </span>
        )}
      </div>

      <button
        onClick={handleTailor}
        disabled={loading}
        className="mt-3 w-full flex items-center justify-center gap-1.5 text-xs font-medium
                   bg-primary/10 hover:bg-primary/20 text-primary border border-primary/30
                   rounded-md py-1.5 transition-colors disabled:opacity-50"
      >
        <Zap className="w-3 h-3" />
        {loading ? "Tailoring…" : "Tailor & Queue"}
      </button>
    </div>
  );
}
