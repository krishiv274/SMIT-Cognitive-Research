import { useEffect, useRef, useState } from "react";

/* Minimal Plotly wrapper; plotly is loaded lazily so the participant app stays small. */
type PlotlyLike = {
  react: (el: HTMLElement, data: unknown[], layout: Record<string, unknown>, config: Record<string, unknown>) => Promise<unknown>;
  purge: (el: HTMLElement) => void;
};

let plotlyPromise: Promise<PlotlyLike> | null = null;
function loadPlotly(): Promise<PlotlyLike> {
  plotlyPromise ??= import("plotly.js-dist-min").then((m) => (m.default ?? m) as PlotlyLike);
  return plotlyPromise;
}

/** Tracks the dashboard's dark-mode class so charts redraw with readable text colours after a theme switch. */
function useDarkClass(): boolean {
  const [dark, setDark] = useState(() => document.documentElement.classList.contains("dark"));
  useEffect(() => {
    const el = document.documentElement;
    const obs = new MutationObserver(() => setDark(el.classList.contains("dark")));
    obs.observe(el, { attributes: true, attributeFilter: ["class"] });
    return () => obs.disconnect();
  }, []);
  return dark;
}

export default function Plot({ data, layout, height = 320 }: { data: unknown[]; layout: Record<string, unknown>; height?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const dark = useDarkClass();
  // data/layout are usually new objects on every render; compare by content so the chart only redraws when it changes.
  const key = JSON.stringify([data, layout, height, dark]);
  useEffect(() => {
    let alive = true;
    const el = ref.current;
    const fg = dark ? "#e2e8f0" : "#0f172a";
    const grid = dark ? "#333333" : "#e2e8f0";
    const axis = (a: unknown) => ({ gridcolor: grid, zerolinecolor: grid, ...(a as Record<string, unknown> | undefined) });
    loadPlotly().then((P) => {
      if (!alive || !el) return;
      P.react(el, data, {
        height,
        margin: { l: 60, r: 20, t: 40, b: 50 },
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        font: { color: fg, size: 12 },
        ...layout,
        xaxis: axis(layout.xaxis),
        yaxis: axis(layout.yaxis),
      }, { displaylogo: false, responsive: true, modeBarButtonsToRemove: ["lasso2d", "select2d"] });
    }).catch(() => undefined);
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  useEffect(() => {
    const el = ref.current;
    return () => { if (el) loadPlotly().then((P) => P.purge(el)).catch(() => undefined); };
  }, []);
  return <div ref={ref} className="w-full" />;
}
