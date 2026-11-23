import { Pipe, PipeTransform } from '@angular/core';
import hljs from 'highlight.js/lib/core';
import python from 'highlight.js/lib/languages/python';
import typescript from 'highlight.js/lib/languages/typescript';
import javascript from 'highlight.js/lib/languages/javascript';
import csharp from 'highlight.js/lib/languages/csharp';
import java from 'highlight.js/lib/languages/java';
import php from 'highlight.js/lib/languages/php';
import ruby from 'highlight.js/lib/languages/ruby';
import css from 'highlight.js/lib/languages/css';
import json from 'highlight.js/lib/languages/json';
import bash from 'highlight.js/lib/languages/bash';
import sql from 'highlight.js/lib/languages/sql';
import yaml from 'highlight.js/lib/languages/yaml';
import xml from 'highlight.js/lib/languages/xml';
import markdown from 'highlight.js/lib/languages/markdown';
import go from 'highlight.js/lib/languages/go';
import rust from 'highlight.js/lib/languages/rust';

hljs.registerLanguage('python', python);
hljs.registerLanguage('typescript', typescript);
hljs.registerLanguage('javascript', javascript);
hljs.registerLanguage('csharp', csharp);
hljs.registerLanguage('java', java);
hljs.registerLanguage('php', php);
hljs.registerLanguage('ruby', ruby);
hljs.registerLanguage('css', css);
hljs.registerLanguage('json', json);
hljs.registerLanguage('bash', bash);
hljs.registerLanguage('sql', sql);
hljs.registerLanguage('yaml', yaml);
hljs.registerLanguage('xml', xml);
hljs.registerLanguage('markdown', markdown);
hljs.registerLanguage('go', go);
hljs.registerLanguage('rust', rust);

@Pipe({
  name: 'markdown',
  standalone: true,
})
export class MarkdownPipe implements PipeTransform {
  transform(value: string | null | undefined): string {
    if (!value) return '';

    return this.parseMarkdown(value);
  }

  private escapeHtml(str: string): string {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  private normalizeLanguage(lang: string): string {
    const clean = lang.trim().toLowerCase();
    switch (clean) {
      case 'c#':
      case 'cs':
      case 'csharp':
        return 'csharp';
      case 'python':
      case 'py':
        return 'python';
      case 'typescript':
      case 'ts':
        return 'typescript';
      case 'javascript':
      case 'js':
        return 'javascript';
      case 'java':
        return 'java';
      case 'php':
        return 'php';
      case 'ruby':
      case 'rb':
        return 'ruby';
      case 'css':
      case 'scss':
      case 'sass':
      case 'less':
        return 'css';
      default:
        return clean;
    }
  }

  private highlightCode(code: string, language: string): string {
    const rawCode = code.trimEnd();
    if (!rawCode) return '';

    const resolved = this.normalizeLanguage(language);
    if (resolved && hljs.getLanguage(resolved)) {
      try {
        return hljs.highlight(rawCode, { language: resolved, ignoreIllegals: true }).value;
      } catch {
        return this.escapeHtml(rawCode);
      }
    }

    return this.escapeHtml(rawCode);
  }

  private parseMarkdown(text: string): string {
    // 1. Separate code blocks to avoid altering markdown-like tokens inside code
    const codeBlocks: string[] = [];
    let processed = text.replace(/```([a-zA-Z0-9_#+.-]*)\n?([\s\S]*?)```/g, (_match, rawLang, code) => {
      const displayLang = rawLang ? this.escapeHtml(rawLang.trim()) : 'code';
      const normalizedLang = this.normalizeLanguage(rawLang || '');
      const highlightedCode = this.highlightCode(code, normalizedLang);

      const blockHtml = `
        <div class="code-container">
          <div class="code-header">
            <span class="code-lang">${displayLang}</span>
            <span class="copy-code-btn"><span class="copy-text">Copy</span></span>
          </div>
          <pre><code class="hljs ${normalizedLang ? 'language-' + normalizedLang : ''}">${highlightedCode}</code></pre>
        </div>
      `;
      codeBlocks.push(blockHtml);
      return `__CODE_BLOCK_${codeBlocks.length - 1}__`;
    });

    // 2. Escape HTML for the non-code portions
    processed = this.escapeHtml(processed);

    // 3. Inline code: `code`
    processed = processed.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');

    // 4. Markdown links [text](url) extracted before bold/italic so URLs are not mangled
    const linkUrls: string[] = [];
    processed = processed.replace(
      /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
      (_match, linkText, url) => {
        linkUrls.push(url);
        return `<a href="__LINK_URL_${linkUrls.length - 1}__" target="_blank" rel="noopener noreferrer" class="md-link">${linkText}</a>`;
      }
    );

    // 5. Headers: #, ##, ###
    processed = processed.replace(/^### (.*$)/gim, '<h4 class="md-h4">$1</h4>');
    processed = processed.replace(/^## (.*$)/gim, '<h3 class="md-h3">$1</h3>');
    processed = processed.replace(/^# (.*$)/gim, '<h2 class="md-h2">$1</h2>');

    // 6. Bold & Italic
    processed = processed.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    processed = processed.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // 7. Blockquotes
    processed = processed.replace(/^>\s?(.*)$/gim, '<blockquote class="md-quote">$1</blockquote>');

    // 8. Unordered lists
    processed = processed.replace(/(?:^[-*]\s+(.+)(?:\r?\n|$))+/gm, (match) => {
      const items = match
        .trim()
        .split('\n')
        .map((line) => line.replace(/^[-*]\s+/, '').trim())
        .map((item) => `<li>${item}</li>`)
        .join('');
      return `<ul class="md-list">${items}</ul>`;
    });

    // 9. Restore link URLs
    processed = processed.replace(/__LINK_URL_(\d+)__/g, (_match, index) => {
      return linkUrls[Number(index)] || '';
    });

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
