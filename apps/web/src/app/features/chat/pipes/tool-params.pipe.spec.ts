import { describe, it, expect } from 'vitest';
import { ToolParamsPipe } from './tool-params.pipe';

describe('ToolParamsPipe', () => {
  const pipe = new ToolParamsPipe();

  it('returns empty array for undefined args', () => {
    expect(pipe.transform(undefined)).toEqual([]);
  });

  it('converts primitive and object entries into key/value pairs', () => {
    expect(pipe.transform({ operator: 'add', count: 2, nested: { a: 1 } })).toEqual([
      { key: 'operator', value: 'add' },
      { key: 'count', value: '2' },
      { key: 'nested', value: '{"a":1}' },
    ]);
  });
});
