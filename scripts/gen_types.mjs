// Generate visual_bench/generated/wire.ts from the Pydantic wire schemas.
//   npm run gen:types     regenerate
//   npm run check:types   fail if the committed file differs (drift check)
import { execFileSync } from "node:child_process";
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { compile } from "json-schema-to-typescript";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const out = resolve(root, "visual_bench/generated/wire.ts");
const python = resolve(root, ".venv/bin/python");
const schema = JSON.parse(execFileSync(python, ["-m", "visual_bench.wire_schema"], { cwd: root, encoding: "utf8" }));
// Expose every $defs entry as a named export.
schema.type = "object";
schema.properties = Object.fromEntries(Object.keys(schema.$defs).map((k) => [k, { $ref: `#/$defs/${k}` }]));
schema.additionalProperties = false;
const ts = (await compile(schema, "ActGuiWire", {
  bannerComment: "/* Generated from visual_bench/schemas.py by scripts/gen_types.mjs. Do not edit. */",
  additionalProperties: false,
  unreachableDefinitions: true,
  format: false,
})).replace(/[ \t]+$/gm, "");
if (process.argv.includes("--check")) {
  const current = existsSync(out) ? readFileSync(out, "utf8") : "";
  if (current !== ts) {
    console.error("wire.ts is out of date with visual_bench/schemas.py; run npm run gen:types");
    process.exit(1);
  }
  console.log("wire.ts matches visual_bench/schemas.py");
} else {
  mkdirSync(dirname(out), { recursive: true });
  writeFileSync(out, ts);
  console.log("wrote", out);
}
