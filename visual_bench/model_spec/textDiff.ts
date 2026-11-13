// Word-level difference between a source sentence and one of its perturbed versions, for highlighting.
// Perturbed sentences come from NLTK tokens joined by spaces ("do n't", "MSSA ?"); detokenize first so that only
// real edits show.

export type DiffPart = { text: string; op: "same" | "add" | "del" };

const ATTACHED = /\s+([.,!?;:%)\]}]|n't|'s|'re|'ve|'ll|'d|'m)(?=\s|$)/g;

export function detokenize(s: string): string {
  return s.trim().replace(/\s+/g, " ").replace(ATTACHED, "$1").replace(/([([{$])\s+/g, "$1");
}

function words(s: string): string[] {
  const t = detokenize(s);
  return t ? t.split(" ") : [];
}

export function wordDiff(from: string, to: string): DiffPart[] {
  const a = words(from), b = words(to);
  const n = a.length, m = b.length;
  const lcs = Array.from({ length: n + 1 }, () => new Array<number>(m + 1).fill(0));
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      lcs[i]![j] = a[i] === b[j] ? lcs[i + 1]![j + 1]! + 1 : Math.max(lcs[i + 1]![j]!, lcs[i]![j + 1]!);
    }
  }
  const parts: DiffPart[] = [];
  const push = (text: string, op: DiffPart["op"]) => {
    const last = parts.at(-1);
    if (last && last.op === op) last.text += ` ${text}`;
    else parts.push({ text, op });
  };
  let i = 0, j = 0;
  while (i < n && j < m) {
    if (a[i] === b[j]) {
      push(a[i]!, "same");
      i++;
      j++;
    } else if (lcs[i + 1]![j]! >= lcs[i]![j + 1]!) push(a[i++]!, "del");
    else push(b[j++]!, "add");
  }
  while (i < n) push(a[i++]!, "del");
  while (j < m) push(b[j++]!, "add");
  return parts;
}
