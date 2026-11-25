import type { ExperimentConfig } from "../types";

/** What the trial engine can put on screen. Implemented with <canvas> in the browser and recorded in tests. */
export interface Renderer {
  clear(): void;
  fixation(): void;
  dot(): void;
  grid(pattern: number[], color: string, caption?: string, question?: string): void;
  equation(text: string, question: string, caption: string): void;
  feedback(lines: { text: string; color: string }[]): void;
}

export class RecordingRenderer implements Renderer {
  public log: string[] = [];
  clear() { this.log.push("clear"); }
  fixation() { this.log.push("fixation"); }
  dot() { this.log.push("dot"); }
  grid(pattern: number[], color: string) { this.log.push(`grid:${pattern.join("-")}:${color}`); }
  equation(text: string) { this.log.push(`equation:${text}`); }
  feedback(lines: { text: string }[]) { this.log.push(`feedback:${lines.map((l) => l.text).join("|")}`); }
}

/**
 * Canvas renderer. All stimuli are drawn at a fixed position (canvas centre), with fixed
 * geometry and colours from the locked configuration, so presentation is identical on every trial.
 */
export class CanvasRenderer implements Renderer {
  private ctx: CanvasRenderingContext2D;
  private w = 0;
  private h = 0;

  constructor(private canvas: HTMLCanvasElement, private cfg: ExperimentConfig) {
    const ctx = canvas.getContext("2d", { alpha: false });
    if (!ctx) throw new Error("Canvas 2D context not available");
    this.ctx = ctx;
    this.resize();
  }

  resize() {
    const dpr = window.devicePixelRatio || 1;
    const rect = this.canvas.getBoundingClientRect();
    this.w = rect.width;
    this.h = rect.height;
    this.canvas.width = Math.round(rect.width * dpr);
    this.canvas.height = Math.round(rect.height * dpr);
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  clear() {
    this.ctx.fillStyle = this.cfg.grid.background_color;
    this.ctx.fillRect(0, 0, this.w, this.h);
  }

  fixation() {
    this.clear();
    const { ctx } = this;
    const cx = this.w / 2, cy = this.h / 2, s = 14;
    ctx.strokeStyle = "#000000";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(cx - s, cy); ctx.lineTo(cx + s, cy);
    ctx.moveTo(cx, cy - s); ctx.lineTo(cx, cy + s);
    ctx.stroke();
  }

  dot() {
    this.clear();
    this.ctx.fillStyle = "#000000";
    this.ctx.beginPath();
    this.ctx.arc(this.w / 2, this.h / 2, 3, 0, Math.PI * 2);
    this.ctx.fill();
  }

  private text(t: string, y: number, size = 22, color = "#000000", weight = "500") {
    const { ctx } = this;
    ctx.fillStyle = color;
    ctx.font = `${weight} ${size}px system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(t, this.w / 2, y);
  }

  grid(pattern: number[], color: string, caption?: string, question?: string) {
    this.clear();
    const { size, cell_size_px: cell, cell_gap_px: gap, cell_color, grid_border_color } = this.cfg.grid;
    const total = size * cell + (size - 1) * gap;
    const x0 = Math.round(this.w / 2 - total / 2);
    const y0 = Math.round(this.h / 2 - total / 2);
    const filled = new Set(pattern);
    const { ctx } = this;
    ctx.fillStyle = grid_border_color;
    ctx.fillRect(x0 - gap, y0 - gap, total + 2 * gap, total + 2 * gap);
    for (let i = 0; i < size * size; i++) {
      const r = Math.floor(i / size), c = i % size;
      ctx.fillStyle = filled.has(i) ? color : cell_color;
      ctx.fillRect(x0 + c * (cell + gap), y0 + r * (cell + gap), cell, cell);
    }
    if (question) this.text(question, y0 - gap - 34, 22, "#000000", "600");
    if (caption) this.text(caption, y0 + total + gap + 34, 20, "#111111");
  }

  equation(text: string, question: string, caption: string) {
    this.clear();
    this.text(question, this.h / 2 - 80, 22, "#000000", "600");
    this.text(text, this.h / 2, 56, "#000000", "600");
    this.text(caption, this.h / 2 + 80, 20, "#111111");
  }

  feedback(lines: { text: string; color: string }[]) {
    this.clear();
    lines.forEach((l, i) => this.text(l.text, this.h / 2 + (i - (lines.length - 1) / 2) * 44, i === 0 ? 32 : 22, l.color, "600"));
  }
}
