import { Pipe, PipeTransform } from '@angular/core';

export interface ToolParamEntry {
  key: string;
  value: string;
}

@Pipe({
  name: 'toolParams',
  standalone: true,
  pure: true,
})
export class ToolParamsPipe implements PipeTransform {
  transform(args: Record<string, unknown> | undefined): ToolParamEntry[] {
    if (!args) return [];
    return Object.entries(args).map(([key, val]) => ({
      key,
      value: typeof val === 'object' ? JSON.stringify(val) : String(val),
    }));
  }
}
