"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { Loader2, Briefcase } from "lucide-react";
import { JobCard } from "@/components/jobs/JobCard";
import { ignoreJob, listJobs, listResumes, tailorApplication } from "@/lib/api";
import { Job, Resume } from "@/lib/types";

export default function JobsPage() {
  const { getToken } = useAuth();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [minScore, setMinScore] = useState(0);

  useEffect(() => {
    (async () => {
      try {
        const token = await getToken();
        if (!token) return;
        const [jobsData, resumesData] = await Promise.all([
          listJobs(token, { min_score: minScore }),
          listResumes(token),
        ]);
        setJobs(jobsData);
        setResumes(resumesData);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load jobs");
      } finally {
        setLoading(false);
      }
    })();
  }, [getToken, minScore]);

  const handleIgnore = async (id: string) => {
    const token = await getToken();
    if (!token) return;
    await ignoreJob(token, id);
    setJobs((prev) => prev.filter((j) => j.id !== id));
  };

  const handleTailor = async (job: Job) => {
    const token = await getToken();
    if (!token || resumes.length === 0) return;
    await tailorApplication(token, job.id, resumes[0].id);
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center gap-2 text-muted-foreground">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span className="text-sm">Loading jobs…</span>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-foreground mb-1">Jobs</h1>
          <p className="text-sm text-muted-foreground">{jobs.length} matching jobs found</p>
        </div>
        <div className="flex items-center gap-3">
          <label className="text-xs text-muted-foreground">Min match:</label>
          <input
            type="range"
            min={0}
            max={100}
            step={5}
            value={minScore}
            onChange={(e) => setMinScore(Number(e.target.value))}
            className="w-24 accent-primary"
          />
          <span className="text-xs font-mono text-foreground w-8">{minScore}%</span>
        </div>
      </div>

      {error && (
        <p className="text-sm text-danger mb-4">{error}</p>
      )}

      {jobs.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <Briefcase className="w-10 h-10 text-muted-foreground/30 mb-3" />
          <p className="text-sm font-medium text-foreground">No jobs found yet</p>
          <p className="text-xs text-muted-foreground mt-1">
            Set up your Hunt Profile to start finding jobs. Scraping runs every 6 hours.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {jobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              onIgnore={handleIgnore}
              onTailor={handleTailor}
            />
          ))}
        </div>
      )}
    </div>
  );
}
