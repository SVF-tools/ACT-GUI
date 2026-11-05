// Skippable onboarding tour: spotlights `[data-tour=...]` regions of the layout one step at a time.
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { placeCard, TOUR_STEPS, type Rect, type Size } from "./tourSteps";

const PAD = 6;

function findTarget(target: string | null): HTMLElement | null {
  if (target === null) return null;
  const el = document.querySelector<HTMLElement>(`[data-tour="${target}"]`);
  if (!el) return null;
  const r = el.getBoundingClientRect();
  return r.width > 0 && r.height > 0 ? el : null;
}

function visibleRect(el: HTMLElement): Rect {
  const r = el.getBoundingClientRect();
  const top = Math.max(r.top, 0) - PAD;
  const left = Math.max(r.left, 0) - PAD;
  const bottom = Math.min(r.bottom, window.innerHeight) + PAD;
  const right = Math.min(r.right, window.innerWidth) + PAD;
  return { top, left, width: right - left, height: bottom - top };
}

export function Tour({ onClose }: { onClose: () => void }) {
  const [index, setIndex] = useState(0);
  const [rect, setRect] = useState<Rect | null>(null);
  const [card, setCard] = useState<Size>({ width: 360, height: 200 });
  const cardRef = useRef<HTMLDivElement>(null);
  const nextRef = useRef<HTMLButtonElement>(null);
  const step = TOUR_STEPS[index]!;
  const last = index === TOUR_STEPS.length - 1;

  const next = useCallback(() => (last ? onClose() : setIndex((i) => i + 1)), [last, onClose]);
  const back = useCallback(() => setIndex((i) => Math.max(0, i - 1)), []);

  useLayoutEffect(() => {
    const el = findTarget(step.target);
    if (!el) {
      setRect(null);
      return;
    }
    el.scrollIntoView({ block: "nearest", inline: "nearest" });
    const measure = () => setRect(visibleRect(el));
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(el);
    window.addEventListener("resize", measure);
    window.addEventListener("scroll", measure, true);
    return () => {
      observer.disconnect();
      window.removeEventListener("resize", measure);
      window.removeEventListener("scroll", measure, true);
    };
  }, [step.target]);

  useLayoutEffect(() => {
    const el = cardRef.current;
    if (el && (el.offsetWidth !== card.width || el.offsetHeight !== card.height)) {
      setCard({ width: el.offsetWidth, height: el.offsetHeight });
    }
  });

  useEffect(() => nextRef.current?.focus(), [index]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      else if (e.key === "ArrowRight") next();
      else if (e.key === "ArrowLeft") back();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [next, back, onClose]);

  const pos = placeCard(rect, card, { width: window.innerWidth, height: window.innerHeight });
  const missing = step.target !== null && rect === null ? step.missing : undefined;

  return createPortal(
    <div className="tour">
      <div className={rect ? "tourblock" : "tourblock dim"} onClick={(e) => e.stopPropagation()} />
      {rect && <div className="tourspot" style={{ top: rect.top, left: rect.left, width: rect.width, height: rect.height }} />}
      <div ref={cardRef} className="tourcard" role="dialog" aria-modal="true" aria-labelledby="tour-title"
        style={{ top: pos.top, left: pos.left }}>
        <div className="tourstep">{index + 1} / {TOUR_STEPS.length}</div>
        <h3 id="tour-title">{step.title}</h3>
        <p>{step.body}</p>
        {missing && <p className="note">{missing}</p>}
        <div className="touractions">
          {!last && <button type="button" className="tourskip" onClick={onClose}>Skip tour</button>}
          <span className="tourgrow" />
          {index > 0 && <button type="button" className="secondary small" onClick={back}>Back</button>}
          <button type="button" ref={nextRef} className="primary small" onClick={next}>{last ? "Finish" : "Next"}</button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
