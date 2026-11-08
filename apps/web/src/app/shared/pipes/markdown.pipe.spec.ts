import { TestBed } from '@angular/core/testing';
import { DomSanitizer } from '@angular/platform-browser';
import { MarkdownPipe } from './markdown.pipe';

describe('MarkdownPipe', () => {
  let pipe: MarkdownPipe;
  let sanitizer: DomSanitizer;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [MarkdownPipe],
    });
    pipe = TestBed.inject(MarkdownPipe);
    sanitizer = TestBed.inject(DomSanitizer);
  });

  it('should return empty string for null or undefined input', () => {
    expect(pipe.transform(null)).toBe('');
    expect(pipe.transform(undefined)).toBe('');
    expect(pipe.transform('')).toBe('');
  });

  it('should escape raw HTML tags to prevent XSS attacks', () => {
    const raw = '<script>alert("xss")</script>';
    const result = pipe.transform(raw)?.toString();
    expect(result).not.toContain('<script>');
    expect(result).toContain('&lt;script&gt;');
  });

  it('should format code blocks with language headers and preformatted code', () => {
    const markdown = '```python\ndef hello():\n    return "world"\n```';
    const result = pipe.transform(markdown)?.toString();
    expect(result).toContain('code-container');
    expect(result).toContain('python');
    expect(result).toContain('def hello():');
  });

  it('should format inline code, bold text, and italic text', () => {
    const markdown = 'This is `inline code` and **bold keyword** with *italic note*.';
    const result = pipe.transform(markdown)?.toString();
    expect(result).toContain('<code class="inline-code">inline code</code>');
    expect(result).toContain('<strong>bold keyword</strong>');
    expect(result).toContain('<em>italic note</em>');
  });

  it('should format markdown headers and lists', () => {
    const markdown = '# Header 1\n## Header 2\n- Item One\n- Item Two';
    const result = pipe.transform(markdown)?.toString();
    expect(result).toContain('<h2 class="md-h2">Header 1</h2>');
    expect(result).toContain('<h3 class="md-h3">Header 2</h3>');
    expect(result).toContain('<li>Item One</li>');
    expect(result).toContain('<li>Item Two</li>');
  });
});
