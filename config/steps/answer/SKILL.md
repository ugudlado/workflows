---
name: answer
description: "Answer one question from the project's own files and the web, with a source for every claim. Use for the ask workflow."
user-invocable: true
---

# Answer

**Intent:** Give the person a direct answer to the question in `User direction`,
built from the project's own material first and the web second, where every
claim names the file or page it came from. This is one answer, not a study:
for a storyline and deliverables there is the `research` workflow.

## Verify

- `{out.answer}` exists and opens with the answer itself, in at most five
  sentences, before any detail.
- Every claim in it carries a source you opened in this run: a project file
  (path, and the line or section) or a web page (title and URL).
- What the sources do not settle is listed under `## Not known`, not guessed.
- `source_count` equals the number of distinct sources listed.

## Instructions

1. Read `User direction` from the brief: it is the question. Standing
   instructions for the project, when the brief or the working directory has
   them (`instructions.md`, `CLAUDE.md`, `AGENTS.md`), apply to how you answer.
2. If the question cannot be answered as asked (empty, or it could mean two
   different things and the project's files do not decide which): report
   `answer_status: await_input` with one focused `ask`. Write nothing.
3. Look in the project first: list the working directory, search it for the
   question's terms, and read the files that match. A fact the project states
   outranks the web's general answer; when they disagree, say so and cite both.
4. Use the web for what the project does not cover, with the search, browse or
   fetch tools this agent has (`curl` for a known URL). Open each page; a search
   snippet is not a source. Prefer primary and official pages, check the date,
   and drop a page that does not load or does not say what the snippet claimed.
   If you have no way to reach the web, say so under `## Not known` and answer
   from the project alone.
5. Write `{out.answer}`:
   - `# <the question, as asked>`
   - The answer, directly, in at most five sentences.
   - `## Detail`: only what the person needs to act on or check the answer,
     each claim followed by its source marker, e.g. `[1]`.
   - `## Not known`: what the sources leave open, and what would settle it.
     Omit the section when nothing is open.
   - `## Sources`: numbered; a project file as its path (with line or section),
     a page as title, publisher, date when given, and URL.
6. Report `answer_status: complete`, `answer` and `source_count`.

## Rules

- Never cite a file or URL you did not open in this run, and never invent one.
- Do not change project files, commit, or push: this step only writes `{out.answer}`.
- Keep it short: the answer and what supports it. No background the question
  did not ask for.
- On re-entry after `await_input`, treat the new `User direction` as the
  clarified question.
