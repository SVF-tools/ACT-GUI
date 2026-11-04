/** Batch order kept, consecutive runs of 3+ folded (as sources.index_ranges). */
export function indexRanges(xs: number[]): string {
  const parts: string[] = [];
  for (let i = 0; i < xs.length;) {
    let j = i;
    while (j + 1 < xs.length && xs[j + 1] === xs[j]! + 1) j++;
    parts.push(j - i >= 2 ? `${xs[i]}–${xs[j]}` : xs.slice(i, j + 1).join(", "));
    i = j + 1;
  }
  return parts.join(", ");
}

/** Mirrors schemas.WireNumber: finite float or an explicit non-finite marker. */
export type WireNumber = number | "Infinity" | "-Infinity" | "NaN";

export function num(x: WireNumber): number {
  if (typeof x === "number") return x;
  return x === "Infinity" ? Infinity : x === "-Infinity" ? -Infinity : NaN;
}

export function fmt(x: number, digits = 4): string {
  if (!Number.isFinite(x)) return String(x);
  return Math.abs(x) >= 1e4 || (Math.abs(x) < 1e-3 && x !== 0) ? x.toExponential(2) : x.toFixed(digits);
}
