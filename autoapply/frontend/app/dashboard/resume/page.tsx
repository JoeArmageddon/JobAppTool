import { ResumeUpload } from "@/components/resume/ResumeUpload";

export default function ResumePage() {
  return (
    <div className="p-8 max-w-2xl">
      <h1 className="text-2xl font-semibold text-foreground mb-1">Resume</h1>
      <p className="text-sm text-muted-foreground mb-8">
        Upload your resume to get an AI-powered score and improvement suggestions.
      </p>
      <ResumeUpload />
    </div>
  );
}
