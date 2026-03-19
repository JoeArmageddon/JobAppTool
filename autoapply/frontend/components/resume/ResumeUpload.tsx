"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useAuth } from "@clerk/nextjs";
import { Upload, FileText, Loader2, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { uploadResume } from "@/lib/api";
import { Resume } from "@/lib/types";
import { ScoreRing } from "./ScoreRing";

interface ResumeUploadProps {
  onUploaded?: (resume: Resume) => void;
}

export function ResumeUpload({ onUploaded }: ResumeUploadProps) {
  const { getToken } = useAuth();
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Resume | null>(null);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (!file) return;
      setError(null);
      setUploading(true);
      try {
        const token = await getToken();
        if (!token) throw new Error("Not authenticated");
        const resume = await uploadResume(token, file);
        setResult(resume);
        onUploaded?.(resume);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Upload failed");
      } finally {
        setUploading(false);
      }
    },
    [getToken, onUploaded]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    },
    maxFiles: 1,
    disabled: uploading,
  });

  return (
    <div className="space-y-6">
      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={cn(
          "border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all",
          isDragActive
            ? "border-primary bg-primary/5 glow-indigo"
            : "border-border hover:border-primary/50 hover:bg-white/2",
          uploading && "opacity-50 cursor-not-allowed"
        )}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-3">
          {uploading ? (
            <>
              <Loader2 className="w-8 h-8 text-primary animate-spin" />
              <p className="text-sm text-muted-foreground">
                Parsing and scoring your resume…
              </p>
            </>
          ) : (
            <>
              <Upload className="w-8 h-8 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium text-foreground">
                  {isDragActive ? "Drop it here" : "Drop your resume or click to browse"}
                </p>
                <p className="text-xs text-muted-foreground mt-1">PDF or DOCX · max 10 MB</p>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-start gap-2 bg-danger/10 border border-danger/30 rounded-lg p-3">
          <AlertCircle className="w-4 h-4 text-danger shrink-0 mt-0.5" />
          <p className="text-sm text-danger">{error}</p>
        </div>
      )}

      {/* Score display */}
      {result && (
        <div className="bg-surface border border-border rounded-xl p-6">
          <div className="flex items-center gap-2 mb-5">
            <FileText className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium text-foreground">
              {result.original_filename}
            </span>
          </div>

          <div className="flex items-center justify-around mb-6">
            <ScoreRing score={result.overall_score ?? 0} label="Overall" size={100} />
            <ScoreRing score={result.ats_score ?? 0} label="ATS" size={80} />
            <ScoreRing score={result.impact_score ?? 0} label="Impact" size={80} />
            <ScoreRing score={result.completeness_score ?? 0} label="Complete" size={80} />
          </div>

          {result.suggestions_json && result.suggestions_json.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
                Suggestions
              </h3>
              <div className="space-y-2">
                {result.suggestions_json.map((s, i) => (
                  <div
                    key={i}
                    className="bg-background rounded-lg p-3 border border-border"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-mono bg-primary/20 text-primary px-1.5 py-0.5 rounded">
                        {s.category}
                      </span>
                      <span className="text-xs text-muted-foreground">{s.issue}</span>
                    </div>
                    <p className="text-xs text-foreground">{s.fix}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
