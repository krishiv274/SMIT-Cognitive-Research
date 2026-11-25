import { useEffect, useRef } from "react";

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

export default function Plot({ data, layout, height = 320 }: { data: unknown[]; layout: Record<string, unknown>; height?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    let alive = true;
    const el = ref.current;
    const dark = document.documentElement.classList.contains("dark");
    loadPlotly().then((P) => {
      if (!alive || !el) return;
      P.react(el, data, {
        height,
        margin: { l: 60, r: 20, t: 40, b: 50 },
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        font: { color: dark ? "#e2e8f0" : "#0f172a", size: 12 },
        ...layout,
      }, { displaylogo: false, responsive: true, modeBarButtonsToRemove: ["lasso2d", "select2d"] });
    });
    return () => {
      alive = false;
      if (el) loadPlotly().then((P) => P.purge(el));
    };
  }, [data, layout, height]);
  return <div ref={ref} className="w-full" />;
}
