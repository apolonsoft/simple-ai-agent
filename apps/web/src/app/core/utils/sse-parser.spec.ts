import { describe, it, expect } from 'vitest';
import { splitSseBuffer, parseSseBlock } from './sse-parser';

describe('sse-parser', () => {
  describe('splitSseBuffer', () => {
    it('splits complete LF-delimited blocks and returns empty remainder', () => {
      const result = splitSseBuffer('event: chunk\ndata: {"a":1}\n\ndata: {"b":2}\n\n');
      expect(result.blocks).toEqual(['event: chunk\ndata: {"a":1}', 'data: {"b":2}']);
      expect(result.remainder).toBe('');
    });

    it('preserves incomplete trailing block in remainder across chunk boundaries', () => {
      const first = splitSseBuffer('data: {"a":1}\n\ndata: {"b":');
      expect(first.blocks).toEqual(['data: {"a":1}']);
      expect(first.remainder).toBe('data: {"b":');

      const second = splitSseBuffer(first.remainder + '2}\n\n');
      expect(second.blocks).toEqual(['data: {"b":2}']);
      expect(second.remainder).toBe('');
    });

    it('handles CRLF and CR double-newline delimiters', () => {
      const crlf = splitSseBuffer('data: 1\r\n\r\ndata: 2\r\n\r\n');
      expect(crlf.blocks).toEqual(['data: 1', 'data: 2']);
      expect(crlf.remainder).toBe('');

      const cr = splitSseBuffer('data: 1\r\rdata: 2\r\r');
      expect(cr.blocks).toEqual(['data: 1', 'data: 2']);
      expect(cr.remainder).toBe('');
    });

    it('handles empty buffer', () => {
      expect(splitSseBuffer('')).toEqual({ blocks: [], remainder: '' });
    });
  });

  describe('parseSseBlock', () => {
    it('defaults eventType to chunk when event line is omitted', () => {
      expect(parseSseBlock('data: {"token":"hello"}')).toEqual({
        eventType: 'chunk',
        dataStr: '{"token":"hello"}',
      });
    });

    it('extracts explicit eventType and strips single leading space from data', () => {
      expect(parseSseBlock('event: tool_call\r\ndata: {"id":"1"}')).toEqual({
        eventType: 'tool_call',
        dataStr: '{"id":"1"}',
      });
    });

    it('handles data line without leading space', () => {
      expect(parseSseBlock('event: done\ndata:{"status":"completed"}')).toEqual({
        eventType: 'done',
        dataStr: '{"status":"completed"}',
      });
    });

    it('returns null for empty or comment-only blocks without data', () => {
      expect(parseSseBlock('')).toBeNull();
      expect(parseSseBlock('   \n  ')).toBeNull();
      expect(parseSseBlock('event: ping\n: keepalive')).toBeNull();
    });
  });
});
