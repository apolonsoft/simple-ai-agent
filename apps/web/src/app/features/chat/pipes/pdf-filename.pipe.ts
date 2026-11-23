import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'pdfFilename',
  standalone: true,
  pure: true,
})
export class PdfFilenamePipe implements PipeTransform {
  transform(result: unknown): string | null {
    if (!result) return null;
    let data: unknown = result;

    if (typeof result === 'string') {
      try {
        data = JSON.parse(result);
      } catch {
        const match = result.match(/[\w\-.]+\.pdf/i);
        return match ? match[0] : null;
      }
    }

    if (typeof data === 'object' && data !== null) {
      const record = data as Record<string, unknown>;
      if (typeof record['filename'] === 'string' && record['filename'].toLowerCase().endsWith('.pdf')) {
        return record['filename'];
      }
      if (typeof record['file_path'] === 'string' && record['file_path'].toLowerCase().endsWith('.pdf')) {
        const parts = record['file_path'].split(/[/\\]/);
        return parts[parts.length - 1];
      }
      if (
        typeof record['merged_file_path'] === 'string' &&
        record['merged_file_path'].toLowerCase().endsWith('.pdf')
      ) {
        const parts = record['merged_file_path'].split(/[/\\]/);
        return parts[parts.length - 1];
      }
    }

    return null;
  }
}
