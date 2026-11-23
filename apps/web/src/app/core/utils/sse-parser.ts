const SSE_BLOCK_DELIMITER = /(?:\r\n\r\n|\r\r|\n\n)/;

export interface SseBufferSplit {
  blocks: string[];
  remainder: string;
}

export interface ParsedSseBlock {
  eventType: string;
  dataStr: string;
}

/**
 * Splits a buffered SSE stream string on double-newline block boundaries,
 * returning complete blocks and the trailing incomplete remainder.
 */
export function splitSseBuffer(buffer: string): SseBufferSplit {
  const blocks = buffer.split(SSE_BLOCK_DELIMITER);
  const remainder = blocks.pop() || '';
  return { blocks, remainder };
}

/**
 * Extracts the SSE `event:` type (defaulting to `'chunk'`) and `data:` payload
 * from a single SSE block, or returns `null` when no `data:` payload is present.
 */
export function parseSseBlock(block: string): ParsedSseBlock | null {
  let eventType = 'chunk';
  let dataStr = '';

  const lines = block.split(/\r?\n/);
  for (const rawLine of lines) {
    const line = rawLine.trimEnd();
    if (line.startsWith('event:')) {
      eventType = line.slice(6).trim();
    } else if (line.startsWith('data:')) {
      const rawData = line.slice(5);
      dataStr = rawData.startsWith(' ') ? rawData.slice(1) : rawData;
    }
  }

  if (!dataStr) return null;
  return { eventType, dataStr };
}
