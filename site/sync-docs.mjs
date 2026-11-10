// Copy the repository's developer Markdown into content/ at the same relative paths, so the site
// serves the repository's own files and their relative links resolve unchanged. The copies are
// build outputs (git-ignored); edit the originals.
import { cpSync, globSync, mkdirSync, rmSync } from "node:fs";
import path from "node:path";

const repo = path.resolve(import.meta.dirname, "..");
const content = path.join(import.meta.dirname, "content");
const SOURCES = [
  "README.md",
  "AGENTS.md",
  "fuzzingGuide.gif",
  "docs/*.md",
  "visual_bench/**/*.md",
  "engine_bridge/**/*.md",
  "site/README.md",
];
const exclude = (file) => file.includes("node_modules");

for (const dir of ["docs", "visual_bench", "engine_bridge", "site"]) {
  rmSync(path.join(content, dir), { recursive: true, force: true });
}
for (const file of SOURCES.flatMap((pattern) => globSync(pattern, { cwd: repo, exclude }))) {
  mkdirSync(path.dirname(path.join(content, file)), { recursive: true });
  cpSync(path.join(repo, file), path.join(content, file));
}
