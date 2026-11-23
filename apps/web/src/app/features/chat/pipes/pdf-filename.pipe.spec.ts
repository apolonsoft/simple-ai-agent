import { describe, it, expect } from 'vitest';
import { PdfFilenamePipe } from './pdf-filename.pipe';

describe('PdfFilenamePipe', () => {
  const pipe = new PdfFilenamePipe();

  it('returns null for falsy or non-pdf inputs', () => {
    expect(pipe.transform(null)).toBeNull();
    expect(pipe.transform(undefined)).toBeNull();
    expect(pipe.transform('no pdf here')).toBeNull();
  });

  it('extracts filename from JSON string or object fields', () => {
    expect(pipe.transform(JSON.stringify({ filename: 'report.pdf' }))).toBe('report.pdf');
    expect(pipe.transform({ file_path: '/tmp/out/summary.pdf' })).toBe('summary.pdf');
    expect(pipe.transform({ merged_file_path: 'C:\\docs\\merged.pdf' })).toBe('merged.pdf');
  });

  it('extracts .pdf filename from plain text fallback', () => {
    expect(pipe.transform('Saved output to /var/tmp/invoice_2026.pdf successfully')).toBe('invoice_2026.pdf');
  });
});
