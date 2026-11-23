import { SecurityContext } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { DomSanitizer } from '@angular/platform-browser';
import hljs from 'highlight.js/lib/core';
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

  it('should format code blocks with language headers and syntax highlighted tokens', () => {
    const markdown = '```python\ndef hello():\n    return "world"\n```';
    const result = pipe.transform(markdown)?.toString();
    expect(result).toContain('code-container');
    expect(result).toContain('python');
    expect(result).toContain('hljs');
    expect(result).toContain('hljs-keyword');
    expect(result).toContain('def');
    expect(result).toContain('hello');
  });

  it('should highlight Python code correctly', () => {
    const markdown = '```python\ndef calculate(x: int) -> int:\n    return x * 2\n```';
    const result = pipe.transform(markdown)?.toString();
    expect(result).toContain('language-python');
    expect(result).toContain('hljs-keyword');
    expect(result).toContain('calculate');
  });

  it('should highlight C# code correctly with c# and cs aliases', () => {
    const markdownCs = '```c#\npublic class Program {\n    public static void Main() {}\n}\n```';
    const resultCs = pipe.transform(markdownCs)?.toString();
    expect(resultCs).toContain('language-csharp');
    expect(resultCs).toContain('hljs-keyword');
    expect(resultCs).toContain('class');
    expect(resultCs).toContain('Program');

    const markdownCsAlias = '```cs\nnamespace App;\n```';
    const resultCsAlias = pipe.transform(markdownCsAlias)?.toString();
    expect(resultCsAlias).toContain('language-csharp');
    expect(resultCsAlias).toContain('hljs-keyword');
  });

  it('should highlight TypeScript code correctly', () => {
    const markdown = '```typescript\nexport interface User {\n    id: string;\n    name: string;\n}\n```';
    const result = pipe.transform(markdown)?.toString();
    expect(result).toContain('language-typescript');
    expect(result).toContain('hljs-keyword');
    expect(result).toContain('interface');
    expect(result).toContain('User');
  });

  it('should highlight Java code correctly', () => {
    const markdown = '```java\npublic class Solution {\n    public int count() { return 0; }\n}\n```';
    const result = pipe.transform(markdown)?.toString();
    expect(result).toContain('language-java');
    expect(result).toContain('hljs-keyword');
    expect(result).toContain('Solution');
  });

  it('should highlight PHP code correctly', () => {
    const markdown = '```php\nfunction greet($name) {\n    return "Hello " . $name;\n}\n```';
    const result = pipe.transform(markdown)?.toString();
    expect(result).toContain('language-php');
    expect(result).toContain('hljs-keyword');
    expect(result).toContain('greet');
  });

  it('should highlight Ruby code correctly', () => {
    const markdown = '```ruby\ndef greet(name)\n  puts "Hello #{name}"\nend\n```';
    const result = pipe.transform(markdown)?.toString();
    expect(result).toContain('language-ruby');
    expect(result).toContain('hljs-keyword');
    expect(result).toContain('def');
  });

  it('should highlight CSS code correctly', () => {
    const markdown = '```css\n.container {\n    display: flex;\n    background-color: #faf8f5;\n}\n```';
    const result = pipe.transform(markdown)?.toString();
    expect(result).toContain('language-css');
    expect(result).toContain('container');
    expect(result).toContain('display');
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

  it('should return a plain string rather than a SafeHtml bypass object', () => {
    const result = pipe.transform('**bold**');
    expect(typeof result).toBe('string');
    expect(result).toBe('<strong>bold</strong>');
  });

  it('should produce output safely sanitized by DomSanitizer for adversarial inputs', () => {
    const imgXss = pipe.transform('<img src=x onerror=alert(1)>');
    const sanitizedImg = sanitizer.sanitize(SecurityContext.HTML, imgXss) ?? '';
    expect(sanitizedImg).not.toContain('<img');
    expect(sanitizedImg).toContain('&lt;img');

    const jsLink = pipe.transform('[x](javascript:alert(1))');
    const sanitizedJsLink = sanitizer.sanitize(SecurityContext.HTML, jsLink) ?? '';
    expect(sanitizedJsLink).not.toContain('<a');
    expect(sanitizedJsLink).not.toContain('href=');

    const nestedUrl = pipe.transform('[click](https://example.com/**foo**)');
    const sanitizedNested = sanitizer.sanitize(SecurityContext.HTML, nestedUrl) ?? '';
    expect(sanitizedNested).toContain('href="https://example.com/**foo**"');
    expect(sanitizedNested).not.toContain('<strong>');
  });

  it('should render unlabeled code blocks as escaped HTML without calling hljs.highlight', () => {
    const highlightSpy = vi.spyOn(hljs, 'highlight');
    const markdown = '```\nconst x = 1 < 2;\n```';
    const result = pipe.transform(markdown);

    expect(highlightSpy).not.toHaveBeenCalled();
    expect(result).toContain('<pre><code class="hljs ">const x = 1 &lt; 2;</code></pre>');
    expect(result).toContain('<span class="copy-code-btn"><span class="copy-text">Copy</span></span>');
    highlightSpy.mockRestore();
  });
});
