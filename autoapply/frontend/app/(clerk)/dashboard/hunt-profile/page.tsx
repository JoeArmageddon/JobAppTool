"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { ChevronRight, ChevronLeft, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { createHuntProfile, listHuntProfiles, updateHuntProfile } from "@/lib/api";
import { HuntProfile } from "@/lib/types";

const STEPS = [
  "Target Titles",
  "Industries",
  "Location",
  "Preferences",
  "Job Sources",
  "Blocklist",
  "Mode",
];

const JOB_SOURCES = ["linkedin", "indeed", "glassdoor", "zip_recruiter", "wellfound", "naukri"];
const INDUSTRIES = [
  "Technology", "Finance", "Healthcare", "E-commerce", "SaaS", "Fintech",
  "EdTech", "Media", "Gaming", "Consulting", "Government", "Nonprofit",
];
const SENIORITY = ["Entry", "Mid", "Senior", "Staff", "Principal", "Lead", "Manager", "Director"];
const COMPANY_SIZES = ["Startup (1–50)", "SMB (51–500)", "Mid-market (501–5000)", "Enterprise (5000+)"];

type FormState = Omit<HuntProfile, "id" | "user_id" | "is_active" | "created_at">;

const DEFAULT: FormState = {
  target_titles: [],
  industries: [],
  locations: [],
  remote_preference: "hybrid",
  seniority_level: undefined,
  salary_floor: undefined,
  company_size_pref: undefined,
  blacklisted_companies: [],
  job_sources: ["linkedin", "indeed"],
  daily_apply_limit: 10,
  auto_apply: false,
};

function TagInput({
  value,
  onChange,
  placeholder,
}: {
  value: string[];
  onChange: (v: string[]) => void;
  placeholder?: string;
}) {
  const [input, setInput] = useState("");
  const add = () => {
    const trimmed = input.trim();
    if (trimmed && !value.includes(trimmed)) onChange([...value, trimmed]);
    setInput("");
  };
  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), add())}
          placeholder={placeholder}
          className="flex-1 bg-surface border border-border rounded-md px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
        />
        <button
          onClick={add}
          type="button"
          className="px-3 py-2 bg-primary/10 border border-primary/30 text-primary text-sm rounded-md hover:bg-primary/20 transition-colors"
        >
          Add
        </button>
      </div>
      {value.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {value.map((v) => (
            <span
              key={v}
              className="flex items-center gap-1 text-xs bg-primary/10 border border-primary/30 text-primary px-2 py-0.5 rounded-full"
            >
              {v}
              <button onClick={() => onChange(value.filter((x) => x !== v))} className="hover:text-danger">
                ×
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default function HuntProfilePage() {
  const { getToken } = useAuth();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<FormState>(DEFAULT);
  const [existing, setExisting] = useState<HuntProfile | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    (async () => {
      const token = await getToken();
      if (!token) return;
      const profiles = await listHuntProfiles(token);
      if (profiles.length > 0) {
        setExisting(profiles[0]);
        const { id, user_id, is_active, created_at, ...rest } = profiles[0];
        setForm(rest as FormState);
      }
    })();
  }, [getToken]);

  const update = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const toggleMulti = (key: keyof FormState, item: string) => {
    const arr = (form[key] as string[]) ?? [];
    update(key, arr.includes(item) ? arr.filter((x) => x !== item) : ([...arr, item] as FormState[typeof key]));
  };

  const save = async () => {
    setSaving(true);
    const token = await getToken();
    if (!token) return;
    if (existing) {
      await updateHuntProfile(token, existing.id, form);
    } else {
      const created = await createHuntProfile(token, form);
      setExisting(created);
    }
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const stepContent = [
    // Step 0 — Target Titles
    <div key="titles" className="space-y-3">
      <p className="text-sm text-muted-foreground">
        What job titles are you targeting? Add each one separately.
      </p>
      <TagInput value={form.target_titles} onChange={(v) => update("target_titles", v)} placeholder="e.g. Senior Software Engineer" />
    </div>,

    // Step 1 — Industries
    <div key="industries" className="space-y-3">
      <p className="text-sm text-muted-foreground">Select the industries you want to work in.</p>
      <div className="flex flex-wrap gap-2">
        {INDUSTRIES.map((ind) => (
          <button
            key={ind}
            onClick={() => toggleMulti("industries", ind)}
            className={cn(
              "text-sm px-3 py-1.5 rounded-full border transition-colors",
              form.industries.includes(ind)
                ? "bg-primary/20 border-primary text-primary"
                : "border-border text-muted-foreground hover:border-primary/30"
            )}
          >
            {ind}
          </button>
        ))}
      </div>
    </div>,

    // Step 2 — Location
    <div key="location" className="space-y-4">
      <div className="space-y-2">
        <label className="text-sm font-medium text-foreground">Locations</label>
        <TagInput value={form.locations} onChange={(v) => update("locations", v)} placeholder="e.g. San Francisco, CA" />
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium text-foreground">Remote Preference</label>
        <div className="flex gap-2">
          {(["remote", "hybrid", "onsite"] as const).map((pref) => (
            <button
              key={pref}
              onClick={() => update("remote_preference", pref)}
              className={cn(
                "px-4 py-2 rounded-md text-sm border capitalize transition-colors",
                form.remote_preference === pref
                  ? "bg-primary/20 border-primary text-primary"
                  : "border-border text-muted-foreground hover:border-primary/30"
              )}
            >
              {pref}
            </button>
          ))}
        </div>
      </div>
    </div>,

    // Step 3 — Preferences
    <div key="prefs" className="space-y-4">
      <div className="space-y-2">
        <label className="text-sm font-medium text-foreground">Seniority Level</label>
        <div className="flex flex-wrap gap-2">
          {SENIORITY.map((s) => (
            <button
              key={s}
              onClick={() => update("seniority_level", form.seniority_level === s ? undefined : s)}
              className={cn(
                "text-sm px-3 py-1.5 rounded-full border transition-colors",
                form.seniority_level === s
                  ? "bg-primary/20 border-primary text-primary"
                  : "border-border text-muted-foreground hover:border-primary/30"
              )}
            >
              {s}
            </button>
          ))}
        </div>
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium text-foreground">
          Minimum Salary: ${((form.salary_floor ?? 0) / 1000).toFixed(0)}k
        </label>
        <input
          type="range" min={0} max={300000} step={5000}
          value={form.salary_floor ?? 0}
          onChange={(e) => update("salary_floor", Number(e.target.value) || undefined)}
          className="w-full accent-primary"
        />
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium text-foreground">Company Size</label>
        <div className="flex flex-wrap gap-2">
          {COMPANY_SIZES.map((s) => (
            <button
              key={s}
              onClick={() => update("company_size_pref", form.company_size_pref === s ? undefined : s)}
              className={cn(
                "text-sm px-3 py-1.5 rounded-full border transition-colors",
                form.company_size_pref === s
                  ? "bg-primary/20 border-primary text-primary"
                  : "border-border text-muted-foreground hover:border-primary/30"
              )}
            >
              {s}
            </button>
          ))}
        </div>
      </div>
    </div>,

    // Step 4 — Job Sources
    <div key="sources" className="space-y-3">
      <p className="text-sm text-muted-foreground">Choose which job boards to scrape.</p>
      <div className="flex flex-wrap gap-2">
        {JOB_SOURCES.map((src) => (
          <button
            key={src}
            onClick={() => toggleMulti("job_sources", src)}
            className={cn(
              "text-sm px-3 py-1.5 rounded-full border capitalize transition-colors",
              form.job_sources.includes(src)
                ? "bg-primary/20 border-primary text-primary"
                : "border-border text-muted-foreground hover:border-primary/30"
            )}
          >
            {src.replace("_", " ")}
          </button>
        ))}
      </div>
    </div>,

    // Step 5 — Blocklist
    <div key="blocklist" className="space-y-3">
      <p className="text-sm text-muted-foreground">
        Companies you never want to apply to, no matter the role.
      </p>
      <TagInput
        value={form.blacklisted_companies}
        onChange={(v) => update("blacklisted_companies", v)}
        placeholder="e.g. Acme Corp"
      />
    </div>,

    // Step 6 — Mode
    <div key="mode" className="space-y-6">
      <div className="space-y-2">
        <label className="text-sm font-medium text-foreground">
          Daily Apply Limit: {form.daily_apply_limit}
        </label>
        <input
          type="range" min={1} max={50} step={1}
          value={form.daily_apply_limit}
          onChange={(e) => update("daily_apply_limit", Number(e.target.value))}
          className="w-full accent-primary"
        />
        <p className="text-xs text-muted-foreground">Hard cap — never exceeded regardless of queue size.</p>
      </div>
      <div className="flex items-start gap-4">
        {[false, true].map((auto) => (
          <button
            key={String(auto)}
            onClick={() => update("auto_apply", auto)}
            className={cn(
              "flex-1 rounded-xl border p-4 text-left transition-colors",
              form.auto_apply === auto
                ? "border-primary bg-primary/10"
                : "border-border hover:border-primary/30"
            )}
          >
            <p className="text-sm font-medium text-foreground">
              {auto ? "Auto-Apply" : "Review Before Send"}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              {auto
                ? "AutoApply tailors and sends automatically within daily limit."
                : "Review each tailored resume + cover letter before submitting."}
            </p>
          </button>
        ))}
      </div>
    </div>,
  ];

  return (
    <div className="p-8 max-w-xl">
      <h1 className="text-2xl font-semibold text-foreground mb-1">Hunt Profile</h1>
      <p className="text-sm text-muted-foreground mb-8">
        Tell AutoApply what you're looking for.
      </p>

      {/* Step indicator */}
      <div className="flex items-center gap-1 mb-8">
        {STEPS.map((s, i) => (
          <div key={s} className="flex items-center gap-1">
            <button
              onClick={() => setStep(i)}
              className={cn(
                "w-6 h-6 rounded-full text-xs font-mono border transition-colors flex items-center justify-center",
                i === step
                  ? "bg-primary border-primary text-white"
                  : i < step
                  ? "bg-success/20 border-success text-success"
                  : "border-border text-muted-foreground"
              )}
            >
              {i < step ? <Check className="w-3 h-3" /> : i + 1}
            </button>
            {i < STEPS.length - 1 && (
              <div className={cn("h-px w-4", i < step ? "bg-success/40" : "bg-border")} />
            )}
          </div>
        ))}
      </div>

      <div className="bg-surface border border-border rounded-xl p-6 mb-6">
        <h2 className="text-sm font-semibold text-foreground mb-4">{STEPS[step]}</h2>
        {stepContent[step]}
      </div>

      <div className="flex items-center justify-between">
        <button
          onClick={() => setStep((s) => Math.max(0, s - 1))}
          disabled={step === 0}
          className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground disabled:opacity-30 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" /> Back
        </button>
        {step < STEPS.length - 1 ? (
          <button
            onClick={() => setStep((s) => s + 1)}
            className="flex items-center gap-1 text-sm bg-primary text-white px-4 py-2 rounded-md hover:bg-primary/90 transition-colors"
          >
            Next <ChevronRight className="w-4 h-4" />
          </button>
        ) : (
          <button
            onClick={save}
            disabled={saving}
            className="flex items-center gap-1 text-sm bg-success text-white px-4 py-2 rounded-md hover:bg-success/90 disabled:opacity-50 transition-colors"
          >
            {saved ? (
              <><Check className="w-4 h-4" /> Saved</>
            ) : saving ? (
              "Saving…"
            ) : (
              "Save Profile"
            )}
          </button>
        )}
      </div>
    </div>
  );
}
