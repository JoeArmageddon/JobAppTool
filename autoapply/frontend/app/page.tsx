// Landing page is static — no auth, no dynamic export needed
"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  Zap, Github, Terminal, Shield, Clock, BarChart2,
  ArrowRight, Check, ChevronRight, Globe, Lock, Cpu,
} from "lucide-react";

// Animated terminal feed
const TERMINAL_LINES = [
  { delay: 0,    prefix: "$", text: "docker compose up -d", type: "cmd" },
  { delay: 800,  prefix: "✓", text: "postgres healthy", type: "ok" },
  { delay: 1200, prefix: "✓", text: "redis healthy", type: "ok" },
  { delay: 1600, prefix: "✓", text: "backend ready on :8000", type: "ok" },
  { delay: 2000, prefix: "✓", text: "frontend ready on :3000", type: "ok" },
  { delay: 2600, prefix: "→", text: "parsing resume: resume_2024.pdf", type: "info" },
  { delay: 3200, prefix: "✓", text: "ATS score: 82 | Impact: 71 | Complete: 95", type: "score" },
  { delay: 4000, prefix: "→", text: "scraping 4 job boards...", type: "info" },
  { delay: 5000, prefix: "✓", text: "found 47 matching jobs (min match 65%)", type: "ok" },
  { delay: 6000, prefix: "→", text: "tailoring: Senior Engineer @ Stripe [match: 91%]", type: "info" },
  { delay: 7000, prefix: "✓", text: "cover letter generated (261 words)", type: "ok" },
  { delay: 7800, prefix: "→", text: "applying via Greenhouse...", type: "info" },
  { delay: 9000, prefix: "✓", text: "applied ✦ screenshot saved", type: "applied" },
  { delay: 9600, prefix: "→", text: "tailoring: Staff Eng @ Linear [match: 88%]", type: "info" },
  { delay: 10600, prefix: "✓", text: "applied ✦ 2 of 10 daily limit used", type: "applied" },
  { delay: 11400, prefix: "◉", text: "queue: 8 remaining | limit resets in 14h", type: "status" },
];

function TerminalWindow() {
  const [visibleCount, setVisibleCount] = useState(0);
  const [cursor, setCursor] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timers = TERMINAL_LINES.map((line, i) =>
      setTimeout(() => {
        setVisibleCount(i + 1);
        if (containerRef.current) {
          containerRef.current.scrollTop = containerRef.current.scrollHeight;
        }
      }, line.delay)
    );
    const loop = setTimeout(() => {
      // Loop
      const resetTimer = setInterval(() => {
        setVisibleCount(0);
        setTimeout(() => {
          setVisibleCount(1);
        }, 200);
      }, 15000);
      return () => clearInterval(resetTimer);
    }, 12000);

    const cursorInterval = setInterval(() => setCursor((v) => !v), 500);
    return () => {
      timers.forEach(clearTimeout);
      clearTimeout(loop);
      clearInterval(cursorInterval);
    };
  }, []);

  const typeColor = (type: string) => {
    switch (type) {
      case "ok": return "text-emerald-400";
      case "applied": return "text-emerald-300";
      case "score": return "text-indigo-300";
      case "info": return "text-slate-300";
      case "status": return "text-amber-400";
      case "cmd": return "text-white";
      default: return "text-slate-400";
    }
  };

  const prefixColor = (type: string) => {
    switch (type) {
      case "ok": return "text-emerald-500";
      case "applied": return "text-emerald-400";
      case "cmd": return "text-indigo-400";
      case "info": return "text-indigo-300";
      case "score": return "text-indigo-400";
      case "status": return "text-amber-500";
      default: return "text-slate-500";
    }
  };

  return (
    <div
      className="rounded-xl overflow-hidden border border-indigo-500/20"
      style={{
        background: "linear-gradient(135deg, #0d0d16 0%, #080810 100%)",
        boxShadow: "0 0 60px rgba(99,102,241,0.15), 0 0 120px rgba(99,102,241,0.05), inset 0 1px 0 rgba(255,255,255,0.05)",
      }}
    >
      {/* Title bar */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5">
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-rose-500/70" />
          <div className="w-3 h-3 rounded-full bg-amber-500/70" />
          <div className="w-3 h-3 rounded-full bg-emerald-500/70" />
        </div>
        <span className="ml-2 text-xs font-mono text-slate-500">autoapply — live feed</span>
      </div>

      {/* Terminal body */}
      <div
        ref={containerRef}
        className="p-5 h-72 overflow-hidden font-mono text-xs space-y-1 leading-relaxed"
      >
        {TERMINAL_LINES.slice(0, visibleCount).map((line, i) => (
          <div key={i} className="flex gap-2.5 items-start">
            <span className={`shrink-0 w-4 text-center ${prefixColor(line.type)}`}>
              {line.prefix}
            </span>
            <span className={typeColor(line.type)}>{line.text}</span>
          </div>
        ))}
        {visibleCount < TERMINAL_LINES.length && (
          <div className="flex gap-2.5">
            <span className="shrink-0 w-4 text-center text-indigo-400">$</span>
            <span className="text-white">
              {cursor ? "▋" : " "}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

const FEATURES = [
  {
    icon: Cpu,
    title: "AI Resume Tailoring",
    desc: "Gap analysis + keyword-matched rewrites for every job. Facts only — zero hallucination.",
    color: "text-indigo-400",
    border: "border-indigo-500/20",
    glow: "rgba(99,102,241,0.08)",
  },
  {
    icon: Globe,
    title: "Multi-Board Scraping",
    desc: "LinkedIn, Indeed, Glassdoor, ZipRecruiter — scraped every 6 hours, matched to your profile.",
    color: "text-emerald-400",
    border: "border-emerald-500/20",
    glow: "rgba(16,185,129,0.08)",
  },
  {
    icon: Zap,
    title: "Playwright Auto-Apply",
    desc: "Greenhouse, Lever adapters with stealth mode and screenshot confirmation. More adapters coming.",
    color: "text-amber-400",
    border: "border-amber-500/20",
    glow: "rgba(245,158,11,0.08)",
  },
  {
    icon: BarChart2,
    title: "Application Tracker",
    desc: "Kanban board. Response rate analytics. Full audit trail — exact resume + cover letter per application.",
    color: "text-indigo-300",
    border: "border-indigo-500/20",
    glow: "rgba(99,102,241,0.08)",
  },
  {
    icon: Lock,
    title: "Self-Hosted & Private",
    desc: "One docker compose up. Your resume and credentials never leave your own infrastructure.",
    color: "text-emerald-300",
    border: "border-emerald-500/20",
    glow: "rgba(16,185,129,0.08)",
  },
  {
    icon: Shield,
    title: "Hard Daily Limits",
    desc: "You set the cap (1–50). The worker never exceeds it, regardless of queue size. No surprises.",
    color: "text-rose-400",
    border: "border-rose-500/20",
    glow: "rgba(244,63,94,0.08)",
  },
];

const STACK = [
  "Next.js 14", "FastAPI", "Claude API",
  "PostgreSQL", "Redis + Celery", "Playwright",
  "WeasyPrint", "Docker Compose",
];

export default function LandingPage() {
  return (
    <div
      className="min-h-screen font-sans"
      style={{ background: "#0a0a0f", color: "#f8fafc" }}
    >
      {/* Nav */}
      <nav className="sticky top-0 z-50 flex items-center justify-between px-6 py-4 border-b border-white/5 backdrop-blur-xl"
        style={{ background: "rgba(10,10,15,0.85)" }}
      >
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-indigo-500 flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="font-semibold text-sm tracking-tight">AutoApply</span>
          <span className="text-xs font-mono text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-1.5 py-0.5 rounded ml-1">
            open-source
          </span>
        </div>
        <div className="flex items-center gap-4">
          <a
            href="https://github.com/JoeArmageddon/JobAppTool"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors"
          >
            <Github className="w-4 h-4" />
            <span className="hidden sm:block">GitHub</span>
          </a>
          <Link
            href="/sign-in"
            className="text-xs font-medium bg-indigo-500 hover:bg-indigo-400 text-white px-3 py-1.5 rounded-md transition-colors"
          >
            Get Started
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden px-6 pt-20 pb-16 max-w-6xl mx-auto">
        {/* Background glow */}
        <div
          className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] rounded-full opacity-20 pointer-events-none"
          style={{
            background: "radial-gradient(circle, #6366f1 0%, transparent 70%)",
            filter: "blur(80px)",
          }}
        />

        <div className="relative grid lg:grid-cols-2 gap-12 items-center">
          <div>
            {/* Badge */}
            <div className="inline-flex items-center gap-2 text-xs font-mono bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-3 py-1.5 rounded-full mb-6">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Self-hostable · Zero data sharing · 100% yours
            </div>

            <h1 className="text-4xl lg:text-5xl font-bold leading-tight tracking-tight mb-5">
              Your resume.{" "}
              <span
                className="text-transparent bg-clip-text"
                style={{
                  backgroundImage: "linear-gradient(135deg, #6366f1 0%, #818cf8 50%, #c084fc 100%)",
                }}
              >
                Every job.
              </span>
              <br />
              Automatically.
            </h1>

            <p className="text-slate-400 text-base leading-relaxed mb-8 max-w-lg">
              AutoApply is an open-source AI agent that scrapes matching jobs, tailors your
              resume with Claude, writes targeted cover letters, and applies — all on your
              own server. One command to deploy.
            </p>

            {/* CTA */}
            <div className="flex flex-wrap items-center gap-3 mb-8">
              <div
                className="flex items-center gap-2 bg-surface border border-indigo-500/30 rounded-lg px-4 py-2.5 font-mono text-sm cursor-pointer group"
                style={{ background: "#12121a" }}
                onClick={() => navigator.clipboard?.writeText("docker compose up -d")}
              >
                <Terminal className="w-4 h-4 text-indigo-400" />
                <span className="text-slate-300">docker compose up <span className="text-indigo-400">-d</span></span>
                <span className="text-xs text-slate-600 group-hover:text-slate-400 transition-colors ml-2">copy</span>
              </div>
              <Link
                href="/sign-up"
                className="flex items-center gap-1.5 bg-indigo-500 hover:bg-indigo-400 text-white text-sm font-medium px-4 py-2.5 rounded-lg transition-colors"
              >
                Try it now <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            {/* Stats */}
            <div className="flex gap-6">
              {[
                { value: "5", label: "ATS adapters" },
                { value: "4", label: "Job boards" },
                { value: "∞", label: "Resumes saved" },
              ].map(({ value, label }) => (
                <div key={label}>
                  <div className="text-xl font-mono font-bold text-indigo-300">{value}</div>
                  <div className="text-xs text-slate-500">{label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Terminal */}
          <div className="lg:block">
            <TerminalWindow />
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="px-6 py-16 max-w-6xl mx-auto">
        <div className="text-center mb-10">
          <h2 className="text-2xl font-bold tracking-tight mb-2">Everything you need. Nothing you don&apos;t.</h2>
          <p className="text-sm text-slate-400">Built for engineers who know exactly what they want.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {FEATURES.map(({ icon: Icon, title, desc, color, border, glow }) => (
            <div
              key={title}
              className={`rounded-xl border p-5 ${border} transition-all hover:scale-[1.01]`}
              style={{
                background: `linear-gradient(135deg, ${glow} 0%, transparent 60%), #12121a`,
              }}
            >
              <Icon className={`w-5 h-5 ${color} mb-3`} />
              <h3 className="text-sm font-semibold text-white mb-1.5">{title}</h3>
              <p className="text-xs text-slate-400 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Resume integrity callout */}
      <section className="px-6 py-10 max-w-6xl mx-auto">
        <div
          className="rounded-xl border border-indigo-500/20 p-6 flex flex-col md:flex-row items-start gap-4"
          style={{ background: "linear-gradient(135deg, rgba(99,102,241,0.07) 0%, transparent 100%), #12121a" }}
        >
          <div className="w-10 h-10 rounded-lg bg-indigo-500/15 border border-indigo-500/30 flex items-center justify-center shrink-0">
            <Shield className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white mb-1">Resume Integrity — Non-Negotiable</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              AutoApply&apos;s AI rewrites are constrained by your actual resume. It will never add skills you
              don&apos;t have, invent experience, or fabricate credentials. Every rewrite prompt includes
              an explicit constraint: <span className="font-mono text-indigo-300 text-xs">use ONLY facts from the original resume</span>.
              Your integrity is the product.
            </p>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="px-6 py-16 max-w-6xl mx-auto">
        <h2 className="text-2xl font-bold tracking-tight mb-8 text-center">How it works</h2>
        <div className="grid md:grid-cols-4 gap-4">
          {[
            { n: "01", title: "Upload Resume", desc: "Get an AI score across ATS, impact, and completeness with actionable fixes." },
            { n: "02", title: "Set Hunt Profile", desc: "Define target titles, locations, salary floor, sources, and daily apply limit." },
            { n: "03", title: "Jobs Appear", desc: "Scraped every 6 hours from 4 boards. Match-scored against your resume automatically." },
            { n: "04", title: "Applied", desc: "AutoApply tailors each resume, writes the cover letter, and applies via Playwright. Or queue for review." },
          ].map(({ n, title, desc }) => (
            <div key={n} className="relative">
              <div className="text-5xl font-mono font-bold text-white/5 mb-2 leading-none">{n}</div>
              <h3 className="text-sm font-semibold text-white mb-1">{title}</h3>
              <p className="text-xs text-slate-400 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Tech stack */}
      <section className="px-6 py-10 max-w-6xl mx-auto border-t border-white/5">
        <p className="text-xs text-slate-500 text-center mb-4 uppercase tracking-widest font-mono">Built with</p>
        <div className="flex flex-wrap justify-center gap-2">
          {STACK.map((tech) => (
            <span
              key={tech}
              className="text-xs font-mono text-slate-400 bg-white/3 border border-white/8 px-3 py-1.5 rounded-full"
            >
              {tech}
            </span>
          ))}
        </div>
      </section>

      {/* Final CTA */}
      <section className="px-6 py-20 text-center">
        <div
          className="max-w-2xl mx-auto rounded-2xl border border-indigo-500/20 p-10"
          style={{
            background: "linear-gradient(135deg, rgba(99,102,241,0.1) 0%, rgba(99,102,241,0.03) 100%), #12121a",
            boxShadow: "0 0 60px rgba(99,102,241,0.1)",
          }}
        >
          <h2 className="text-2xl font-bold mb-3">Ready to automate your job search?</h2>
          <p className="text-sm text-slate-400 mb-6">
            Open-source. Self-hosted. Your data stays yours.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <div
              className="font-mono text-sm bg-black/40 border border-white/10 px-4 py-2.5 rounded-lg text-slate-300"
            >
              git clone https://github.com/JoeArmageddon/JobAppTool
            </div>
            <Link
              href="/sign-up"
              className="flex items-center gap-1.5 bg-indigo-500 hover:bg-indigo-400 text-white text-sm font-medium px-5 py-2.5 rounded-lg transition-colors"
            >
              Launch Dashboard <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="flex justify-center gap-4 mt-6">
            {["No usage limits", "Apache 2.0 License", "Self-hostable"].map((item) => (
              <span key={item} className="flex items-center gap-1 text-xs text-slate-500">
                <Check className="w-3 h-3 text-emerald-500" />
                {item}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-6 border-t border-white/5 flex items-center justify-between max-w-6xl mx-auto">
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-indigo-400" />
          <span className="text-xs text-slate-500 font-mono">AutoApply</span>
        </div>
        <div className="flex items-center gap-4 text-xs text-slate-600">
          <a href="https://github.com/JoeArmageddon/JobAppTool" target="_blank" rel="noopener noreferrer" className="hover:text-slate-400 transition-colors flex items-center gap-1">
            <Github className="w-3 h-3" /> GitHub
          </a>
          <span>Apache 2.0</span>
        </div>
      </footer>
    </div>
  );
}
