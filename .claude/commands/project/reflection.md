You are an expert prompt engineer specializing in AI coding assistant optimization.
Your job is to analyze this session and improve the CLAUDE.md instructions so future
sessions go better.

---

## Phase 1 — Load Context

Read the current instructions:
@CLAUDE.md

Then review the full chat history in your context window. Note every moment where:
- You misunderstood what was asked
- You had to ask a clarifying question that a better-instructed Claude wouldn't need
- You made a wrong assumption about the project's stack, conventions, or tools
- The user had to correct or redirect you
- You were slow to act because context was missing (MCP servers, file locations, team processes, etc.)

---

## Phase 2 — Prioritized Gap Analysis

Present your findings as a numbered list. For each gap, assign a severity:

🔴 HIGH — causes repeated friction or wrong outputs  
🟡 MEDIUM — causes slowdowns or extra back-and-forth  
🟢 LOW — minor polish or edge-case handling

Format each item as:
```
N. [SEVERITY] Title
   - What happened in this session
   - Why the current CLAUDE.md doesn't prevent it
   - Proposed fix (one clear paragraph or section to add/edit)
```

Stop after listing all gaps. Wait for my response before proceeding.

---

## Phase 3 — Iterative Approval

For each item I approve (I'll say "yes", "skip", or give feedback):
- YES → queue it for implementation
- SKIP → move on
- Feedback → revise and re-propose before queuing

Do not implement anything until I say "implement all" or "implement N, M, ..."

---

## Phase 4 — Implementation

For each approved change, output:
```
### Change N: [Title]
**Section:** [new section name OR existing section being edited]
**Action:** [ADD / EDIT / REMOVE]

[Full text of the new/modified section, ready to paste into CLAUDE.md]

**Why this helps:** [One sentence]
```

After all changes, output a complete updated CLAUDE.md wrapped in a code block,
incorporating every approved change. Do not summarize — output the full file.

---

## Constraints

- Never remove existing instructions unless I explicitly approve it
- Keep additions concise — prefer bullet points over paragraphs
- If you're unsure whether something belongs in CLAUDE.md or a separate file (e.g. `.mcp.json`, `AGENTS.md`), flag it rather than guessing
- Bias toward specificity: "use `npm run dev`" beats "run the dev server"