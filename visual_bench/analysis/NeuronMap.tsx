import { useEffect, useMemo, useRef, useState } from "react";
import { binStatuses, statusClass, statusLabel } from "./propagation";

const TOKENS = { active: "--good", inactive: "--violet", unstable: "--warn", unknown: "--muted" };

/** One canvas per channel; bins preserve every cell and click zooms to exact values. */
export function NeuronMap({ statuses, shape, selected, onSelect }: {
  statuses: (number | undefined)[]; shape: number[]; selected: number | null; onSelect: (n: number) => void;
}) {
  const [range, setRange] = useState<{ start: number; end: number } | null>(null);
  const conv = shape.length === 4 && shape[1]! * shape[2]! * shape[3]! === statuses.length;
  const channels = conv && !range ? shape[1]! : 1;
  const perChannel = conv ? shape[2]! * shape[3]! : statuses.length;
  const [channelPage, setChannelPage] = useState(0);
  const pages = Math.max(1, Math.ceil(channels / 16));
  const page = Math.min(channelPage, pages - 1);
  return <div className="neuron-map">
    <div className="prop-controls">
      <label>Neuron <input type="number" min={0} max={Math.max(0, statuses.length - 1)} value={selected ?? ""}
        placeholder="Index" onChange={(e) => { const n = e.target.valueAsNumber; if (Number.isInteger(n) && n >= 0 && n < statuses.length) onSelect(n); }} /></label>
      {range && <button className="secondary" onClick={() => setRange(null)}>All neurons</button>}
      {pages > 1 && <label>Channels <select value={page} onChange={(e) => setChannelPage(Number(e.target.value))}>
        {Array.from({ length: pages }, (_, p) => <option value={p} key={p}>{p * 16}–{Math.min(channels, (p + 1) * 16) - 1}</option>)}
      </select></label>}
    </div>
    <div className={conv && !range ? "neuron-channels" : "neuron-dense"}>
      {Array.from({ length: Math.min(16, channels - page * 16) }, (_, j) => {
        const channel = page * 16 + j;
        const start = range?.start ?? channel * perChannel;
        const end = range?.end ?? Math.min(statuses.length, start + perChannel);
        return <MapCanvas key={`${start}-${end}`} values={statuses.slice(start, end)} start={start}
          columns={conv && !range ? shape[3] : undefined} selected={selected}
          label={conv && !range ? `Channel ${channel} · ${shape[2]} × ${shape[3]}` : `Neurons ${start}–${end - 1}`}
          limit={conv && !range ? Math.max(1, Math.floor(4096 / Math.min(channels, 16))) : 4096}
          onPick={(a, b) => b - a > 1 ? setRange({ start: a, end: b }) : onSelect(a)} />;
      })}
    </div>
    <p className="note">All {statuses.length.toLocaleString()} neurons. Grouped cells use unstable-first coloring; select a group to zoom. Arrow keys move through cells, Enter selects.</p>
  </div>;
}

function MapCanvas({ values, start, columns, selected, label, limit, onPick }: {
  values: (number | undefined)[]; start: number; columns?: number; selected: number | null; label: string; limit: number;
  onPick: (a: number, b: number) => void;
}) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const bins = useMemo(() => binStatuses(values, limit), [values, limit]);
  const cols = Math.max(1, bins.length === values.length && columns ? columns : Math.ceil(Math.sqrt(bins.length)));
  const rows = Math.max(1, Math.ceil(bins.length / cols));
  const [focus, setFocus] = useState(0);
  const cell = 12;
  useEffect(() => {
    const paint = () => {
      const ctx = canvas.current?.getContext("2d");
      if (!ctx || !canvas.current) return;
      const css = getComputedStyle(canvas.current);
      const colors = Object.fromEntries(Object.entries(TOKENS).map(([k, v]) => [k, css.getPropertyValue(v).trim()]));
      ctx.clearRect(0, 0, cols * cell, rows * cell);
      bins.forEach((bin, i) => {
        const x = (i % cols) * cell, y = Math.floor(i / cols) * cell;
        ctx.fillStyle = colors[statusClass(bin.status)]!;
        ctx.fillRect(x + 1, y + 1, cell - 2, cell - 2);
        if (selected !== null && selected >= start + bin.start && selected < start + bin.end) {
          ctx.strokeStyle = css.getPropertyValue("--text"); ctx.lineWidth = 2;
          ctx.strokeRect(x + 2, y + 2, cell - 4, cell - 4);
        }
      });
    };
    paint();
    const observer = new MutationObserver(paint);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => observer.disconnect();
  }, [bins, cols, rows, selected, start]);
  const pick = (i: number) => { const b = bins[i]; if (b) onPick(start + b.start, start + b.end); };
  const current = bins[Math.min(focus, bins.length - 1)];
  return <figure className="neuron-channel">
    <figcaption>{label}</figcaption>
    <canvas ref={canvas} width={cols * cell} height={rows * cell} style={{ maxWidth: cols * 24 }} tabIndex={0} role="button"
      aria-label={`${label}. ${bins.length < values.length ? "Grouped cells. " : ""}${current ? `${statusLabel(current.status)}, index ${start + current.start}.` : ""} Use arrow keys and Enter.`}
      onClick={(e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        const col = Math.min(cols - 1, Math.floor((e.clientX - rect.left) / rect.width * cols));
        const row = Math.min(rows - 1, Math.floor((e.clientY - rect.top) / rect.height * rows));
        pick(row * cols + col);
      }}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); pick(focus); }
        const delta = ({ ArrowLeft: -1, ArrowRight: 1, ArrowUp: -cols, ArrowDown: cols } as Record<string, number>)[e.key];
        if (delta !== undefined) { e.preventDefault(); setFocus((f) => Math.max(0, Math.min(bins.length - 1, f + delta))); }
      }} />
    {bins.length < values.length && <small>{values.length} neurons in {bins.length} groups</small>}
    <span className="note">{current && `${start + current.start}${current.end - current.start > 1 ? `–${start + current.end - 1}` : ""}: ${statusLabel(current.status)}`}</span>
  </figure>;
}
