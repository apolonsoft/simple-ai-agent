import { TestBed, ComponentFixture } from '@angular/core/testing';
import * as pdfjsLib from 'pdfjs-dist';
import { PdfViewerModalComponent } from './pdf-viewer-modal.component';

describe('PdfViewerModalComponent', () => {
  let component: PdfViewerModalComponent;
  let fixture: ComponentFixture<PdfViewerModalComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PdfViewerModalComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(PdfViewerModalComponent);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('filename', 'test_sample.pdf');
    fixture.detectChanges();
  });

  it('should create and display filename in toolbar', () => {
    expect(component).toBeTruthy();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('test_sample.pdf');
  });

  it('should handle page navigation signals', () => {
    // Mock multiple pages
    component.totalPages.set(5);
    component.currentPage.set(2);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.page-indicator')?.textContent).toContain('2 / 5');

    // Next page
    component.nextPage();
    expect(component.currentPage()).toBe(3);

    // Prev page
    component.prevPage();
    expect(component.currentPage()).toBe(2);
  });

  it('should adjust zoom scale on zoomIn, zoomOut, and resetZoom', () => {
    expect(component.zoomScale()).toBe(1.0);

    component.zoomIn();
    expect(component.zoomScale()).toBe(1.25);

    component.zoomIn();
    expect(component.zoomScale()).toBe(1.5);

    component.zoomOut();
    expect(component.zoomScale()).toBe(1.25);

    component.resetZoom();
    expect(component.zoomScale()).toBe(1.0);
  });

  it('should update active tool and color selection', () => {
    expect(component.activeTool()).toBe('pan');

    component.setTool('pen');
    expect(component.activeTool()).toBe('pen');

    component.setTool('highlighter');
    expect(component.activeTool()).toBe('highlighter');

    component.setColor('#2563eb');
    expect(component.activeColor()).toBe('#2563eb');
  });

  it('should emit closeModal event on close button click', () => {
    let closed = false;
    component.closeModal.subscribe(() => {
      closed = true;
    });

    const closeBtn = fixture.nativeElement.querySelector('.btn-close') as HTMLButtonElement;
    closeBtn.click();
    expect(closed).toBe(true);
  });

  it('should emit download event with filename on download button click', () => {
    let downloadedName = '';
    component.download.subscribe((name) => {
      downloadedName = name;
    });

    const downloadBtn = fixture.nativeElement.querySelector('.btn-download') as HTMLButtonElement;
    downloadBtn.click();
    expect(downloadedName).toBe('test_sample.pdf');
  });

  it('should configure self-hosted workerSrc and dialog ARIA attributes', () => {
    expect(pdfjsLib.GlobalWorkerOptions.workerSrc).toBe('/assets/pdf.worker.min.mjs');

    const dialog = (fixture.nativeElement as HTMLElement).querySelector('[role="dialog"]');
    expect(dialog).toBeTruthy();
    expect(dialog?.getAttribute('aria-modal')).toBe('true');
  });

  it('should destroy previous pdfDoc when a new pdfBlob is provided', async () => {
    const destroySpy = vi.fn().mockResolvedValue(undefined);
    (component as any).pdfDoc = { destroy: destroySpy };

    fixture.componentRef.setInput('pdfBlob', new Blob(['pdf-2'], { type: 'application/pdf' }));
    fixture.detectChanges();
    await Promise.resolve();

    expect(destroySpy).toHaveBeenCalled();
  });
});
