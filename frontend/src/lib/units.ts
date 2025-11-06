export type UnitFamily = 'mass' | 'volume' | 'count' | 'unknown';

// Normalize textual unit to a canonical key
const normalizeStr = (s: string) => (s || '').toLowerCase().trim();

export const unitKey = (u?: string): string => {
  let k = normalizeStr(u || '');
  // remove trailing dots (e.g., "tbsp.")
  k = k.replace(/\.$/, '');
  // canonical long forms
  k = k
    .replace(/fluid\s*ounce|fluid\s*ounces/g, 'fl oz')
    .replace(/floz/g, 'fl oz')
    .replace(/millilitre|millilitres|milliliter|milliliters/g, 'ml')
    .replace(/litre|litres|liter|liters/g, 'l')
    .replace(/ounce|ounces/g, 'oz')
    .replace(/pound|pounds/g, 'lb')
    .replace(/gram|grams/g, 'g')
    .replace(/kilogram|kilograms/g, 'kg')
    .replace(/tablespoons?/g, 'tbsp')
    .replace(/teaspoons?/g, 'tsp')
    .replace(/pieces?/g, 'piece')
    .replace(/items?/g, 'item')
    .replace(/units?/g, 'unit')
    .replace(/eggs?/g, 'egg')
    .replace(/cloves?/g, 'clove')
    .replace(/cans?/g, 'can');
  if (k === 'pc') k = 'pcs';
  return k;
};

// Converters
export const MASS_TO_GRAMS: Readonly<Record<string, number>> = Object.freeze({
  g: 1,
  kg: 1000,
  mg: 0.001,
  lb: 453.59237,
  oz: 28.349523125,
});

export const VOLUME_TO_ML: Readonly<Record<string, number>> = Object.freeze({
  ml: 1,
  l: 1000,
  cup: 240,
  tbsp: 15,
  tsp: 5,
  'fl oz': 29.5735,
});

export const COUNT_UNITS: Readonly<Set<string>> = new Set([
  '', 'unit', 'piece', 'pcs', 'item', 'clove', 'egg', 'can'
]);

export const classifyUnit = (u?: string): UnitFamily => {
  const k = unitKey(u);
  if (k in MASS_TO_GRAMS) return 'mass';
  if (k in VOLUME_TO_ML) return 'volume';
  if (COUNT_UNITS.has(k)) return 'count';
  return 'unknown';
};

export const toBase = (
  qty: number,
  unit?: string
): { family: UnitFamily; value: number; key: string } => {
  const k = unitKey(unit);
  const fam = classifyUnit(k);
  if (!Number.isFinite(qty) || qty < 0) return { family: fam, value: 0, key: k };
  if (fam === 'mass') return { family: fam, value: qty * (MASS_TO_GRAMS[k] || 1), key: k }; // grams
  if (fam === 'volume') return { family: fam, value: qty * (VOLUME_TO_ML[k] || 1), key: k }; // milliliters
  if (fam === 'count') return { family: fam, value: qty, key: k }; // items
  return { family: fam, value: qty, key: k };
};

export const fromBase = (baseValue: number, targetUnit?: string): number => {
  const k = unitKey(targetUnit);
  const fam = classifyUnit(k);
  if (fam === 'mass') return baseValue / (MASS_TO_GRAMS[k] || 1);
  if (fam === 'volume') return baseValue / (VOLUME_TO_ML[k] || 1);
  // count or unknown: return as-is
  return baseValue;
};
