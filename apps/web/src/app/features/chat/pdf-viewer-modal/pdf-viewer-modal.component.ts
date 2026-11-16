import {
  Component,
  ElementRef,
  ViewChild,
  input,
  output,
  signal,
  effect,
  AfterViewInit,
  OnDestroy,
  HostListener,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import * as pdfjsLib from 'pdfjs-dist';

// Configure worker URL using CDN matching the installed version
if (typeof window !== 'undefined' && !pdfjsLib.GlobalWorkerOptions.workerSrc) {
  pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.mjs`;
}

export interface Point {
  x: number; // Stored in unscaled page coordinates
  y: number; // Stored in unscaled page coordinates
}

export interface Stroke {
  tool: 'pen' | 'highlighter';
  color: string;
  width: number;
  points: Point[];
}

@Component({
  selector: 'app-pdf-viewer-modal',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './pdf-viewer-modal.component.html',
  styleUrl: './pdf-viewer-modal.component.scss',
})
export class PdfViewerModalComponent implements AfterViewInit, OnDestroy {
  // Inputs & Outputs
  readonly pdfBlob = input<Blob | null>(null);
  readonly filename = input<string>('document.pdf');
  readonly closeModal = output<void>();
  readonly download = output<string>();

  @ViewChild('basePdfCanvas') private basePdfCanvas?: ElementRef<HTMLCanvasElement>;
  @ViewChild('overlayDrawCanvas') private overlayDrawCanvas?: ElementRef<HTMLCanvasElement>;
  @ViewChild('canvasContainer') private canvasContainer?: ElementRef<HTMLDivElement>;

  // Component reactive state
  readonly currentPage = signal<number>(1);
  readonly totalPages = signal<number>(1);
  readonly zoomScale = signal<number>(1.0);
  readonly activeTool = signal<'pan' | 'pen' | 'highlighter'>('pan');
  readonly activeColor = signal<string>('#ef4444');
  readonly strokeWidth = signal<number>(3);
  readonly isLoading = signal<boolean>(true);
  readonly renderError = signal<string | null>(null);
  readonly Math = Math;

  // Available palette colors
  readonly paletteColors = [
    { label: 'Charcoal', hex: '#27251e' },
    { label: 'Red', hex: '#ef4444' },
    { label: 'Blue', hex: '#2563eb' },
    { label: 'Green', hex: '#16a34a' },
    { label: 'Yellow', hex: '#eab308' },
  ];

  private pdfDoc: any = null;
  private renderTask: any = null;
  private unscaledWidth: number = 595;
  private unscaledHeight: number = 842;

  // Stored annotations per page (page number -> list of strokes in unscaled coords)
  private pageAnnotations = new Map<number, Stroke[]>();
  private isDrawing = false;
  private currentStroke: Stroke | null = null;

  constructor() {
    effect(() => {
      const blob = this.pdfBlob();
      if (blob) {
        this.loadPdfFromBlob(blob);
      }
    });
  }

  ngAfterViewInit(): void {
    if (this.pdfDoc) {
      this.renderCurrentPage();
    }
  }

  ngOnDestroy(): void {
    if (this.renderTask) {
      try {
        this.renderTask.cancel();
      } catch {
        // ignore cancellation errors
      }
    }
    if (this.pdfDoc) {
      try {
        this.pdfDoc.destroy();
      } catch {
        // ignore destroy errors
      }
    }
  }

  @HostListener('window:keydown', ['$event'])
  handleKeyboardEvent(event: KeyboardEvent): void {
    if (event.key === 'Escape') {
      this.close();
    } else if (event.key === 'ArrowLeft' || event.key === 'PageUp') {
      this.prevPage();
    } else if (event.key === 'ArrowRight' || event.key === 'PageDown') {
      this.nextPage();
    }
  }

  private async loadPdfFromBlob(blob: Blob): Promise<void> {
    this.isLoading.set(true);
    this.renderError.set(null);
    try {
      const arrayBuffer = await blob.arrayBuffer();
      const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer });
      this.pdfDoc = await loadingTask.promise;
      this.totalPages.set(this.pdfDoc.numPages);
      this.currentPage.set(1);
      this.pageAnnotations.clear();
      await this.renderCurrentPage();
    } catch (err: any) {
      console.error('Failed to parse PDF document', err);
      this.renderError.set(err?.message || 'Failed to load PDF document.');
    } finally {
      this.isLoading.set(false);
    }
  }

  async renderCurrentPage(): Promise<void> {
    if (!this.pdfDoc || !this.basePdfCanvas?.nativeElement || !this.overlayDrawCanvas?.nativeElement) {
      return;
    }

    if (this.renderTask) {
      try {
        this.renderTask.cancel();
      } catch {
        // ignore cancellation
      }
      this.renderTask = null;
    }

    try {
      const pageNumber = this.currentPage();
      const page = await this.pdfDoc.getPage(pageNumber);

      const baseViewport = page.getViewport({ scale: 1.0 });
      this.unscaledWidth = baseViewport.width;
      this.unscaledHeight = baseViewport.height;

      const scale = this.zoomScale();
      const viewport = page.getViewport({ scale });

      const dpr = typeof window !== 'undefined' ? window.devicePixelRatio || 1 : 1;

      const baseCanvas = this.basePdfCanvas.nativeElement;
      const overlayCanvas = this.overlayDrawCanvas.nativeElement;

      // Base canvas setup
      baseCanvas.width = Math.floor(viewport.width * dpr);
      baseCanvas.height = Math.floor(viewport.height * dpr);
      baseCanvas.style.width = `${Math.floor(viewport.width)}px`;
      baseCanvas.style.height = `${Math.floor(viewport.height)}px`;

      // Overlay canvas setup
      overlayCanvas.width = Math.floor(viewport.width * dpr);
      overlayCanvas.height = Math.floor(viewport.height * dpr);
      overlayCanvas.style.width = `${Math.floor(viewport.width)}px`;
      overlayCanvas.style.height = `${Math.floor(viewport.height)}px`;

      const ctx = baseCanvas.getContext('2d');
      if (!ctx) return;
      ctx.save();
      ctx.scale(dpr, dpr);

      const renderContext = {
        canvasContext: ctx,
        viewport,
      };

      this.renderTask = page.render(renderContext);
      await this.renderTask.promise;
      ctx.restore();

      this.redrawAnnotations();
    } catch (err: any) {
      if (err?.name === 'RenderingCancelledException') {
        return;
      }
      console.error('Error rendering PDF page', err);
    }
  }

  // --- Zoom Controls ---

  zoomIn(): void {
    const next = Math.min(3.0, Number((this.zoomScale() + 0.25).toFixed(2)));
    if (next !== this.zoomScale()) {
      this.zoomScale.set(next);
      this.renderCurrentPage();
    }
  }

  zoomOut(): void {
    const next = Math.max(0.5, Number((this.zoomScale() - 0.25).toFixed(2)));
    if (next !== this.zoomScale()) {
      this.zoomScale.set(next);
      this.renderCurrentPage();
    }
  }

  resetZoom(): void {
    if (this.zoomScale() !== 1.0) {
      this.zoomScale.set(1.0);
      this.renderCurrentPage();
    }
  }

  fitWidth(): void {
    if (!this.canvasContainer?.nativeElement || this.unscaledWidth <= 0) return;
    const available = this.canvasContainer.nativeElement.clientWidth - 48;
    const fitScale = Math.max(0.5, Math.min(2.5, Number((available / this.unscaledWidth).toFixed(2))));
    this.zoomScale.set(fitScale);
    this.renderCurrentPage();
  }

  // --- Page Navigation ---

  prevPage(): void {
    if (this.currentPage() > 1) {
      this.currentPage.update((p) => p - 1);
      this.renderCurrentPage();
    }
  }

  nextPage(): void {
    if (this.currentPage() < this.totalPages()) {
      this.currentPage.update((p) => p + 1);
      this.renderCurrentPage();
    }
  }

  // --- Drawing & Annotations ---

  setTool(tool: 'pan' | 'pen' | 'highlighter'): void {
    this.activeTool.set(tool);
  }

  setColor(color: string): void {
    this.activeColor.set(color);
  }

  clearAnnotations(): void {
    this.pageAnnotations.set(this.currentPage(), []);
    this.redrawAnnotations();
  }

  onPointerDown(event: PointerEvent): void {
    if (this.activeTool() === 'pan' || !this.overlayDrawCanvas?.nativeElement) return;
    event.preventDefault();
    this.isDrawing = true;

    const coords = this.getUnscaledCoords(event);
    this.currentStroke = {
      tool: this.activeTool() as 'pen' | 'highlighter',
      color: this.activeColor(),
      width: this.strokeWidth(),
      points: [coords],
    };

    this.overlayDrawCanvas.nativeElement.setPointerCapture(event.pointerId);
  }

  onPointerMove(event: PointerEvent): void {
    if (!this.isDrawing || !this.currentStroke || !this.overlayDrawCanvas?.nativeElement) return;
    event.preventDefault();

    const coords = this.getUnscaledCoords(event);
    this.currentStroke.points.push(coords);

    // Incrementally render line segment
    this.drawSegment(this.currentStroke);
  }

  onPointerUp(event: PointerEvent): void {
    if (!this.isDrawing) return;
    this.isDrawing = false;
    if (this.currentStroke && this.currentStroke.points.length > 0) {
      const pageStrokes = this.pageAnnotations.get(this.currentPage()) || [];
      pageStrokes.push(this.currentStroke);
      this.pageAnnotations.set(this.currentPage(), pageStrokes);
    }
    this.currentStroke = null;
    this.redrawAnnotations();

    if (this.overlayDrawCanvas?.nativeElement?.hasPointerCapture(event.pointerId)) {
      this.overlayDrawCanvas.nativeElement.releasePointerCapture(event.pointerId);
    }
  }

  private getUnscaledCoords(event: PointerEvent): Point {
    const canvas = this.overlayDrawCanvas!.nativeElement;
    const rect = canvas.getBoundingClientRect();
    const clientX = event.clientX - rect.left;
    const clientY = event.clientY - rect.top;
    const scale = this.zoomScale();
    return {
      x: clientX / scale,
      y: clientY / scale,
    };
  }

  private drawSegment(stroke: Stroke): void {
    const canvas = this.overlayDrawCanvas?.nativeElement;
    if (!canvas || stroke.points.length < 2) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = typeof window !== 'undefined' ? window.devicePixelRatio || 1 : 1;
    const scale = this.zoomScale() * dpr;

    const p1 = stroke.points[stroke.points.length - 2];
    const p2 = stroke.points[stroke.points.length - 1];

    ctx.save();
    this.applyStrokeStyle(ctx, stroke, dpr);
    ctx.beginPath();
    ctx.moveTo(p1.x * scale, p1.y * scale);
    ctx.lineTo(p2.x * scale, p2.y * scale);
    ctx.stroke();
    ctx.restore();
  }

  private redrawAnnotations(): void {
    const canvas = this.overlayDrawCanvas?.nativeElement;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const dpr = typeof window !== 'undefined' ? window.devicePixelRatio || 1 : 1;
    const scale = this.zoomScale() * dpr;

    const strokes = this.pageAnnotations.get(this.currentPage()) || [];
    for (const stroke of strokes) {
      if (stroke.points.length === 0) continue;
      ctx.save();
      this.applyStrokeStyle(ctx, stroke, dpr);
      ctx.beginPath();
      ctx.moveTo(stroke.points[0].x * scale, stroke.points[0].y * scale);
      for (let i = 1; i < stroke.points.length; i++) {
        ctx.lineTo(stroke.points[i].x * scale, stroke.points[i].y * scale);
      }
      ctx.stroke();
      ctx.restore();
    }
  }

  private applyStrokeStyle(ctx: CanvasRenderingContext2D, stroke: Stroke, dpr: number): void {
    ctx.strokeStyle = stroke.color;
    ctx.lineCap = stroke.tool === 'highlighter' ? 'square' : 'round';
    ctx.lineJoin = stroke.tool === 'highlighter' ? 'bevel' : 'round';

    if (stroke.tool === 'highlighter') {
      ctx.lineWidth = stroke.width * 5 * dpr;
      ctx.globalAlpha = 0.35;
      ctx.globalCompositeOperation = 'multiply';
    } else {
      ctx.lineWidth = stroke.width * dpr;
      ctx.globalAlpha = 1.0;
      ctx.globalCompositeOperation = 'source-over';
    }
  }

  // --- Modal Actions ---

  triggerDownload(): void {
    this.download.emit(this.filename());
  }

  close(): void {
    this.closeModal.emit();
  }
}
