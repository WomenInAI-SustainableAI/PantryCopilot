import type { InventoryFormItem } from "@/lib/types";

// Basic text normalization and tokenization with plural handling and stopword removal
const lower = (s: string) => (s || "").toLowerCase();
const stripPunct = (s: string) => s.replace(/["'`,.~!@#$%^&*()_+={}\[\]\\|:;<>\/?]/g, " ");
const collapseWs = (s: string) => s.replace(/\s+/g, " ").trim();

const STOPWORDS = new Set<string>([
  "of", "and", "a", "the", "fresh", "pcs", "piece", "pieces", "unit", "units",
  "can", "cans", "bottle", "bottles", "pack", "package", "pkg"
]);

const singular = (w: string): string => {
  // Very small plural rules sufficient for food names
  if (/^(tomatoes|potatoes)$/.test(w)) return w.replace(/oes$/, "o");
  if (/ies$/.test(w)) return w.replace(/ies$/, "y");
  if (/(ches|shes|xes|zes|ses)$/.test(w)) return w.replace(/es$/, "");
  if (/s$/.test(w) && !/(ss|\d+s)$/.test(w)) return w.replace(/s$/, "");
  return w;
};

export const tokenize = (name: string): string[] => {
  const n = collapseWs(stripPunct(lower(name)));
  const raw = n.split(" ").filter(Boolean);
  const out: string[] = [];
  for (const tok of raw) {
    if (STOPWORDS.has(tok)) continue;
    out.push(singular(tok));
  }
  return out;
};

const jaccard = (a: Set<string>, b: Set<string>): number => {
  if (a.size === 0 || b.size === 0) return 0;
  let inter = 0;
  for (const t of a) if (b.has(t)) inter++;
  return inter / (a.size + b.size - inter);
};

export function matchInventory(
  ingredientName: string,
  inventory: InventoryFormItem[]
): InventoryFormItem | undefined {
  const ingTokens = new Set(tokenize(ingredientName));
  if (ingTokens.size === 0) return undefined;

  // 1) exact normalized match first
  const ingNorm = Array.from(ingTokens).join(" ");
  for (const it of inventory) {
    const invNorm = tokenize(it.name).join(" ");
    if (invNorm === ingNorm) return it;
  }

  // 2) token-based best match using Jaccard, with a minimum overlap
  let best: { it: InventoryFormItem; score: number } | null = null;
  for (const it of inventory) {
    const invTokens = new Set(tokenize(it.name));
    let overlap = 0;
    for (const t of ingTokens) if (invTokens.has(t)) overlap++;
    if (overlap === 0) continue;
    const score = jaccard(ingTokens, invTokens);
    if (!best || score > best.score) best = { it, score };
  }
  // require a modest threshold to avoid spurious matches
  if (best && best.score >= 0.34) return best.it;
  return undefined;
}

export function matchAllInventory(
  ingredientName: string,
  inventory: InventoryFormItem[]
): InventoryFormItem[] {
  const ingTokens = new Set(tokenize(ingredientName));
  if (ingTokens.size === 0) return [];
  const scored: Array<{ it: InventoryFormItem; score: number }> = [];
  for (const it of inventory) {
    const invTokens = new Set(tokenize(it.name));
    let overlap = 0;
    for (const t of ingTokens) if (invTokens.has(t)) overlap++;
    if (overlap === 0) continue;
    const score = jaccard(ingTokens, invTokens);
    scored.push({ it, score });
  }
  scored.sort((a, b) => b.score - a.score);
  return scored.filter(s => s.score >= 0.34).map(s => s.it);
}
