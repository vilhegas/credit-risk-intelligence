/** JSON.parse alone silently accepts duplicate keys. Scan the grammar first. */
export function parseStrictJson(bytes: Uint8Array): unknown {
  const input = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(bytes);
  let i = 0;
  const fail = (): never => { throw new Error(`JSON inválido na posição ${i}`); };
  const whitespace = () => { while (/[\x20\t\r\n]/.test(input[i] ?? "x")) i++; };
  const string = (): string => {
    const start = i++;
    while (i < input.length) {
      const char = input[i++];
      if (char === '"') return JSON.parse(input.slice(start, i)) as string;
      if (char === "\\") i++;
    }
    return fail();
  };
  const value = (depth: number): void => {
    if (depth > 100) fail();
    whitespace();
    if (input[i] === "{") {
      i++; whitespace();
      const keys = new Set<string>();
      if (input[i] === "}") { i++; return; }
      while (i < input.length) {
        if (input[i] !== '"') fail();
        const key = string();
        if (keys.has(key)) throw new Error(`Chave JSON duplicada: ${key}`);
        keys.add(key); whitespace();
        if (input[i++] !== ":") fail();
        value(depth + 1); whitespace();
        if (input[i] === "}") { i++; return; }
        if (input[i++] !== ",") fail();
        whitespace();
      }
      fail();
    } else if (input[i] === "[") {
      i++; whitespace();
      if (input[i] === "]") { i++; return; }
      while (i < input.length) {
        value(depth + 1); whitespace();
        if (input[i] === "]") { i++; return; }
        if (input[i++] !== ",") fail();
      }
      fail();
    } else if (input[i] === '"') string();
    else {
      const token = /^(?:true|false|null|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)/.exec(input.slice(i));
      if (!token) fail();
      i += token![0].length;
      if (!/^(true|false|null)$/.test(token![0]) && !Number.isFinite(Number(token![0]))) fail();
    }
  };
  value(0); whitespace();
  if (i !== input.length) fail();
  return JSON.parse(input) as unknown;
}
