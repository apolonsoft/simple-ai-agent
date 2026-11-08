import { Pipe, PipeTransform, inject, SecurityContext } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

@Pipe({
  name: 'markdown',
  standalone: true,
})
export class MarkdownPipe implements PipeTransform {
  private readonly sanitizer = inject(DomSanitizer);

  transform(value: string | null | undefined): SafeHtml {
    if (!value) return '';

    const html = this.parseMarkdown(value);
    return this.sanitizer.bypassSecurityTrustHtml(html);
  }

  private escapeHtml(str: string): string {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  private parseMarkdown(text: string): string {
    // 1. Separate code blocks to avoid altering markdown-like tokens inside code
    const codeBlocks: string[] = [];
    let processed = text.replace(/```([a-zA-Z0-9_-]*)\n?([\s\S]*?)```/g, (_match, lang, code) => {
      const language = lang ? this.escapeHtml(lang.trim()) : 'code';
      const escapedCode = this.escapeHtml(code.trimEnd());
      const blockHtml = `
        <div class="code-container">
          <div class="code-header">
            <span class="code-lang">${language}</span>
            <button type="button" class="copy-code-btn" title="Copy code">
              <svg class="copy-icon" xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
              <span class="copy-text">Copy</span>
            </button>
          </div>
          <pre><code>${escapedCode}</code></pre>
        </div>
      `;
      codeBlocks.push(blockHtml);
      return `__CODE_BLOCK_${codeBlocks.length - 1}__`;
    });

    // 2. Escape HTML for the non-code portions
    processed = this.escapeHtml(processed);

    // 3. Inline code: `code`
    processed = processed.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');

    // 4. Headers: #, ##, ###
    processed = processed.replace(/^### (.*$)/gim, '<h4 class="md-h4">$1</h4>');
    processed = processed.replace(/^## (.*$)/gim, '<h3 class="md-h3">$1</h3>');
    processed = processed.replace(/^# (.*$)/gim, '<h2 class="md-h2">$1</h2>');

    // 5. Bold & Italic
    processed = processed.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    processed = processed.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // 6. Blockquotes
    processed = processed.replace(/^>\s?(.*)$/gim, '<blockquote class="md-quote">$1</blockquote>');

    // 7. Unordered lists
    processed = processed.replace(/(?:^[-*]\s+(.+)(?:\r?\n|$))+/gm, (match) => {
      const items = match
        .trim()
        .split('\n')
        .map((line) => line.replace(/^[-*]\s+/, '').trim())
        .map((item) => `<li>${item}</li>`)
        .join('');
      return `<ul class="md-list">${items}</ul>`;
    });

    // 8. Markdown links [text](url)
    processed = processed.replace(
      /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener noreferrer" class="md-link">$1</a>'
    );

    // 9. Line breaks outside of code blocks
    processed = processed.replace(/\n/g, '<br/>');

    // Clean up redundant line breaks immediately adjacent to code blocks
    processed = processed.replace(/(?:<br\/>)+(?=__CODE_BLOCK_)/g, '');
    processed = processed.replace(/(__CODE_BLOCK_\d+__)(?:<br\/>)+/g, '$1');

    // 10. Re-insert code blocks
    processed = processed.replace(/__CODE_BLOCK_(\d+)__/g, (_match, index) => {
      return codeBlocks[Number(index)] || '';
    });

    return processed;
  }
}
