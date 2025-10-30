"use client";

import { useEffect, useState, useMemo } from "react";
import Image from "next/image";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetFooter,
} from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ThumbsUp, ThumbsDown, Sparkles, ChefHat, Clock, ShieldCheck, Leaf, CookingPot } from "lucide-react";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
import type { Recipe, NormalizedRecipe, UserPreferences, InventoryFormItem, Ingredient } from "@/lib/types";
import { PlaceHolderImages } from "@/lib/placeholder-images";
import { submitFeedback, getUserFeedbackForRecipe } from "@/app/actions";
import { normalizeRecipe } from "@/lib/normalize-recipe";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { cookRecipe } from "@/app/actions";
// Lightweight client-side sanitizer for a limited set of tags/attrs.
// We avoid adding a runtime dependency here; this sanitizer keeps basic formatting and links.
function sanitizeHtml(dirty: string): string {
  if (!dirty) return "";
  const parser = new DOMParser();
  const doc = parser.parseFromString(dirty, "text/html");
  const allowedTags = new Set(["b", "strong", "i", "em", "a", "ul", "ol", "li", "p", "br"]);
  const allowedAttrs = new Set(["href", "title"]);

  function sanitizeElement(el: Element): Element | null {
    const tag = el.tagName.toLowerCase();
    if (!allowedTags.has(tag)) {
      // If tag not allowed, we will return a fragment of its children
      const frag = document.createDocumentFragment();
      el.childNodes.forEach((child) => {
        const sanitized = sanitizeNode(child);
        if (sanitized) frag.appendChild(sanitized);
      });
      const wrapper = document.createElement('div');
      wrapper.appendChild(frag);
      return wrapper;
    }

    const newEl = document.createElement(tag);
    // copy allowed attributes
    Array.from(el.attributes || []).forEach((attr) => {
      const name = attr.name.toLowerCase();
      if (allowedAttrs.has(name)) {
        if (name === 'href') {
          // Only allow http/https/mailto/hash URLs
          const v = attr.value || '';
          if (/^(https?:\/\/|mailto:|#)/i.test(v)) {
            newEl.setAttribute('href', v);
            newEl.setAttribute('target', '_blank');
            newEl.setAttribute('rel', 'noopener noreferrer');
          }
        } else {
          newEl.setAttribute(name, attr.value);
        }
      }
    });

    el.childNodes.forEach((child) => {
      const sanitized = sanitizeNode(child);
      if (sanitized) newEl.appendChild(sanitized);
    });
    return newEl;
  }

  function sanitizeNode(node: ChildNode): Node | null {
    if (node.nodeType === Node.TEXT_NODE) {
      return document.createTextNode(node.textContent || '');
    }
    if (node.nodeType === Node.ELEMENT_NODE) {
      return sanitizeElement(node as Element);
    }
    return null;
  }

  const container = document.createElement('div');
  doc.body.childNodes.forEach((child) => {
    const sanitized = sanitizeNode(child);
    if (sanitized) container.appendChild(sanitized);
  });
  return container.innerHTML;
}
import { differenceInDays } from "date-fns";

interface RecipeDetailsProps {
  recipe: Recipe;
  userPreferences: UserPreferences;
  inventory: InventoryFormItem[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCookRecipe: (recipe: NormalizedRecipe, servingsCooked?: number) => void;
}

interface ExplanationInfo {
  expiring: string[];
  safe: boolean;
  missing: Ingredient[];
  partial: { name: string; remaining: number; unit: string }[];
  moneySaved: number;
  co2Saved: number;
  foodSavedLbs: number;
}

// (kept HTML in description; we'll sanitize when rendering)

export default function RecipeDetails({
  recipe,
  userPreferences,
  inventory,
  open,
  onOpenChange,
  onCookRecipe,
}: RecipeDetailsProps) {
  const { toast } = useToast();
  const [feedbackSubmitted, setFeedbackSubmitted] = useState<"upvote" | "downvote" | null>(null);
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);
  const [isCooking, setIsCooking] = useState(false);
  const [showCookedDialog, setShowCookedDialog] = useState(false);
  const [originalServings, setOriginalServings] = useState<number>(1);
  const [selectedServings, setSelectedServings] = useState<number>(1);
  const [servingsInput, setServingsInput] = useState<string>("1");
  type CookedItem =
    | { type: 'quantity'; name: string; oldQty: number; newQty: number; unit: string }
    | { type: 'status'; name: string; status: string };
  const [cookedSummary, setCookedSummary] = useState<{
    items: CookedItem[];
    note?: string;
  } | null>(null);

  const normalized = useMemo(() => normalizeRecipe(recipe), [recipe]);

  const sanitizedDescription = useMemo(() => sanitizeHtml(normalized.description || ''), [normalized.description]);

  // Safely convert unknown values (objects/arrays/errors) into strings for rendering
  const toText = (val: any): string => {
    if (val == null) return '';
    if (typeof val === 'string') return val;
    if (Array.isArray(val)) return val.map(toText).filter(Boolean).join('; ');
    if (typeof val === 'object') {
      try {
        // Prefer common error shapes
        if ('msg' in val && typeof (val as any).msg === 'string') return (val as any).msg;
        if ('detail' in val) return toText((val as any).detail);
        return JSON.stringify(val);
      } catch {
        return String(val);
      }
    }
    return String(val);
  };

  // Initialize servings based on recipe information
  useEffect(() => {
    const base = Number((normalized as any)?.servings) || Number((recipe as any)?.servings) || 1;
    setOriginalServings(base);
    setSelectedServings(base);
    setServingsInput(String(base));
  }, [normalized?.id]);

  // Load any previously submitted feedback for this user+recipe to prevent duplicate submissions
  useEffect(() => {
    let cancelled = false;
    async function loadExisting() {
      if (!open) return; // only when sheet is open
      const uid = userPreferences?.userId;
      const rid = normalized?.id;
      if (!uid || !rid) return;
      const existing = await getUserFeedbackForRecipe(uid, rid);
      if (!cancelled) {
        if (existing === "upvote" || existing === "downvote") {
          setFeedbackSubmitted(existing);
        } else {
          setFeedbackSubmitted(null);
        }
      }
    }
    loadExisting();
    return () => {
      cancelled = true;
    };
  }, [open, userPreferences?.userId, normalized?.id]);

  // Derive image URL similar to RecipeCard: prefer normalized.image (spoonacular URL),
  // otherwise try a constructed spoonacular URL by id, then fallback to placeholder set.
  const placeholderImage = PlaceHolderImages.find((img) => img.id === normalized.imageId);
  const spoonacularImage = normalized.image || (normalized.id ? `https://spoonacular.com/recipeImages/${normalized.id}-636x393.jpg` : undefined);
  const imageUrl = spoonacularImage || placeholderImage?.imageUrl;

  const expiringIngredients = useMemo(() => {
    const recipeIngredients = new Set(normalized.ingredients.map((i: Ingredient) => i.name.toLowerCase()));
    return (inventory || []).filter(item => {
      const expiry = item?.expiryDate ? new Date(item.expiryDate) : null;
      if (!expiry || isNaN(expiry.getTime())) return false;
      const daysUntilExpiry = differenceInDays(expiry, new Date());
      return daysUntilExpiry <= 7 && recipeIngredients.has((item?.name || '').toLowerCase());
    }).map(item => item.name);
  }, [inventory, normalized.ingredients]);

  const missingIngredients = useMemo(() => {
    const inventoryMap = new Map<string, number>(
      (inventory || []).map(item => [((item?.name || '')).toLowerCase(), item?.quantity ?? 0])
    );
    return normalized.ingredients.filter(
      (ing: Ingredient) => (inventoryMap.get(ing.name.toLowerCase()) || 0) < (ing.quantity || 0)
    );
  }, [inventory, normalized.ingredients]);

  // Scaled ingredients based on selected servings
  const scaledIngredients = useMemo(() => {
    const base = originalServings || 1;
    const factor = (selectedServings || 1) / base;
    return (normalized.ingredients || []).map((ing: Ingredient) => ({
      ...ing,
      quantity: Math.round(((ing.quantity || 0) * factor + Number.EPSILON) * 100) / 100,
    }));
  }, [normalized.ingredients, originalServings, selectedServings]);

  // Client-side explanation info (inspired by v2)
  const explanationInfo = useMemo<ExplanationInfo>(() => {
    const inventoryMap = new Map<string, InventoryFormItem>((inventory || []).map(item => [
      (item?.name || '').toLowerCase(),
      item
    ]));
    // Backend is authoritative for category expansion. Frontend performs a basic exact check only.
    const allergySet = new Set((userPreferences?.allergies || []).map(a => (a || '').toLowerCase()));
    const hasAllergens = (normalized.ingredients || []).some((ing) => allergySet.has(String(ing?.name || '').toLowerCase()));

    const missing: Ingredient[] = [];
    const partial: { name: string; remaining: number; unit: string }[] = [];
    let moneySaved = 0;
    let foodSavedLbs = 0;

    (normalized.ingredients || []).forEach((ing) => {
      const name = (ing?.name || '').toLowerCase();
      const invItem = inventoryMap.get(name);
      const qtyInv = invItem?.quantity ?? 0;
      const qtyNeeded = ing?.quantity ?? 0;

      if (qtyInv < qtyNeeded) {
        // deficit is needed minus available
        missing.push({ ...ing, quantity: Math.max(qtyNeeded - qtyInv, 0) });
      } else {
        // Simple placeholder economics/environmental estimates
        const pricePerUnit = 2.5; // $ per unit (placeholder)
        const weightPerUnit = 0.5; // lbs per unit (placeholder)
        moneySaved += qtyNeeded * pricePerUnit;
        foodSavedLbs += qtyNeeded * weightPerUnit;

        if (qtyInv > qtyNeeded) {
          partial.push({
            name: ing.name,
            remaining: qtyInv - qtyNeeded,
            unit: ing.unit || '',
          });
        }
      }
    });

    const co2Saved = foodSavedLbs * 2.5; // kg CO2e per lb food waste avoided (placeholder)

    return {
      expiring: expiringIngredients,
      safe: !hasAllergens,
      missing,
      partial,
      moneySaved: parseFloat(moneySaved.toFixed(2)),
      co2Saved: parseFloat(co2Saved.toFixed(2)),
      foodSavedLbs: parseFloat(foodSavedLbs.toFixed(2)),
    };
  }, [inventory, normalized.ingredients, expiringIngredients, userPreferences?.allergies]);

  const handleFeedback = async (feedbackType: "upvote" | "downvote") => {
    if (isSubmittingFeedback) return;
    setIsSubmittingFeedback(true);

    // If pressing the same button again, treat it as a reset (neutral) using "skip"
    const sendingType = feedbackSubmitted === feedbackType ? ("skip" as any) : (feedbackType as any);
    // Optimistically update UI
    setFeedbackSubmitted(sendingType === "skip" ? null : feedbackType);

    const result = await submitFeedback({
      recipeId: normalized.id,
      feedbackType: sendingType,
      userId: userPreferences.userId,
      recipeTitle: normalized.title,
      recipeCategories: [
        ...((recipe as any)?.dishTypes || []),
        ...((recipe as any)?.cuisines || []),
      ].filter(Boolean),
    });

    toast({
      title: result.success ? (sendingType === "skip" ? "Feedback Cleared" : "Feedback Submitted") : "Error",
      description: toText(result.message),
      variant: result.success ? "default" : "destructive",
    });
    if (!result.success) {
      // Revert optimistic update
      setFeedbackSubmitted(feedbackSubmitted);
    }
    setIsSubmittingFeedback(false);
  };

  const handleCookClick = async () => {
    if (isCooking) return;
    setIsCooking(true);

    // Call backend cooked endpoint first to ensure server-side inventory updates
    const userId = userPreferences?.userId;
    if (!userId) {
      toast({ title: "Error", description: "Missing user ID.", variant: "destructive" });
      setIsCooking(false);
      return;
    }

  // Use the selected servings specified by the user
  // SNAPSHOT-COOK SUPPORT (temporary):
  // Prepare a snapshot so backend can bypass Spoonacular (402 quota or mock data)
  // To REMOVE later: delete this snapshot object and pass only (userId, id, servings) to cookRecipe
  const cookBaseServings = originalServings || Number((recipe as any)?.servings) || 1;
  const snapshot = {
    title: normalized.title,
    servings: cookBaseServings,
    dishTypes: ((recipe as any)?.dishTypes || []) as string[],
    cuisines: ((recipe as any)?.cuisines || []) as string[],
    ingredients: (normalized.ingredients || []).map((ing: Ingredient) => ({
      name: ing.name,
      quantity: ing.quantity || 0,
      unit: ing.unit || ''
    })),
  };
  const result = await cookRecipe(
    userId,
    normalized.id,
    Math.max(1, Number(selectedServings) || 1),
    snapshot
  );
    if (!result.success || !result.data) {
      toast({
        title: "Couldn’t mark as cooked",
        description: toText(result.message) || "Please try again.",
        variant: "destructive",
      });
      setIsCooking(false);
      return;
    }

    // Build detailed cooked summary items with deltas
  const norm = (s: string) => (s || '').toLowerCase().replace(/["']/g, '').trim();
    const findInv = (name: string): InventoryFormItem | undefined => {
      const exact = (inventory || []).find(i => norm(i.name) === norm(name));
      if (exact) return exact;
      // Only allow multi-word subset matches (e.g., 'milk chocolate' ⊆ 'dark milk chocolate bar')
      const tokens = (s: string) => s.split(/\s+/).filter(Boolean);
      const ingTokens = tokens(norm(name));
      if ( ingTokens.length >= 2 ) {
        const ingSet = new Set(ingTokens);
        for (const i of (inventory || [])) {
          const invSet = new Set(tokens(norm(i.name)));
          let subset = true;
          for (const t of ingSet) { if (!invSet.has(t)) { subset = false; break; } }
          if (subset) return i;
        }
      }
      return undefined;
    };
    const parseBackendNew = (msg: string): number | null => {
      const m = /new quantity:\s*([-+]?[0-9]*\.?[0-9]+)/i.exec(msg || '');
      return m ? parseFloat(m[1]) : null;
    };
    const items: CookedItem[] = [];
    const baseServings = originalServings || 1;
    const usedFactor = (selectedServings || 1) / baseServings;
    const updates = (result.data?.inventory_updates || {}) as Record<string, string>;
    normalized.ingredients.forEach(ing => {
      const inv = findInv(ing.name);
      const unit = inv?.unit || ing.unit || '';
      const backendMsgRaw = updates[ing.name];
      const backendMsg = toText(backendMsgRaw);
      if (inv) {
        let oldQty = inv.quantity;
        let newQty: number | null = null;
        if (backendMsg) {
          if (/deleted/i.test(backendMsg)) {
            newQty = 0;
          } else {
            const parsed = parseBackendNew(backendMsg);
            if (parsed !== null && !Number.isNaN(parsed)) newQty = parsed;
          }
        }
        if (newQty === null) {
          const used = (ing.quantity || 0) * usedFactor;
          newQty = Math.max(0, oldQty - used);
        }
        items.push({ type: 'quantity', name: ing.name, oldQty, newQty, unit });
      } else {
        const statusRaw = backendMsg || 'not found in inventory';
        items.push({ type: 'status', name: ing.name, status: statusRaw });
      }
    });

    setCookedSummary({ items, note: result.data.message });

    // Show dialog with summary; defer parent updates until user acknowledges
    setShowCookedDialog(true);
    setIsCooking(false);
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-2xl w-full p-0">
        <ScrollArea className="h-full">
          <div className="pb-32">
            <SheetHeader className="relative">
              {imageUrl ? (
                <Image
                  alt={normalized.title}
                  className="aspect-video w-full object-cover"
                  height={337}
                  src={imageUrl}
                  width={600}
                />
              ) : (
                // simple visual placeholder when no image URL available
                <div className="aspect-video w-full bg-muted/50 flex items-center justify-center text-muted-foreground">No image</div>
              )}
              <div className="p-6 text-left space-y-2">
                <SheetTitle className="font-headline text-3xl">{normalized.title}</SheetTitle>
                {/* Render sanitized HTML directly in a div to avoid invalid nesting (SheetDescription
                    may render a <p>, and putting block elements inside a <p> causes hydration errors). */}
                <div className="text-sm text-muted-foreground leading-relaxed" dangerouslySetInnerHTML={{ __html: sanitizedDescription }} />
              </div>
            </SheetHeader>
            <div className="p-6 space-y-6">
              <div>
                <h3 className="font-headline text-lg font-semibold mb-3 flex items-center">
                    <Sparkles className="w-5 h-5 mr-2 text-primary" /> Why This Recipe?
                </h3>
                <div className="bg-muted/50 p-4 rounded-lg border space-y-4">
                  {explanationInfo.expiring.length > 0 && (
                    <div className="flex items-start gap-3">
                      <Clock className="w-5 h-5 mt-0.5 text-destructive flex-shrink-0" />
                      <div>
                        <h4 className="font-semibold text-foreground">Urgency</h4>
                        <p className="text-sm text-muted-foreground">Helps you use up <span className="font-medium text-foreground">{explanationInfo.expiring.join(', ')}</span> before it expires.</p>
                      </div>
                    </div>
                  )}
                  <div className="flex items-start gap-3">
                    <ShieldCheck className={`w-5 h-5 mt-0.5 ${explanationInfo.safe ? 'text-green-600' : 'text-destructive'} flex-shrink-0`} />
                    <div>
                      <h4 className="font-semibold text-foreground">Safety</h4>
                      {explanationInfo.safe ? (
                        <p className="text-sm text-muted-foreground">This recipe appears to be safe and doesn't contain your listed allergens.</p>
                      ) : (
                        <p className="text-sm font-medium text-destructive">Warning! This recipe may contain ingredients you are allergic to. Please review carefully.</p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <Leaf className="w-5 h-5 mt-0.5 text-green-600 flex-shrink-0" />
                    <div>
                      <h4 className="font-semibold text-foreground">Estimated Impact</h4>
                      <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
                        <span><strong className="text-foreground">${explanationInfo.moneySaved}</strong> saved</span>
                        <span><strong className="text-foreground">{explanationInfo.co2Saved} kg</strong> CO2 avoided</span>
                        <span><strong className="text-foreground">{explanationInfo.foodSavedLbs} lbs</strong> food saved</span>
                      </div>
                    </div>
                  </div>
                  {(explanationInfo.missing.length > 0 || explanationInfo.partial.length > 0) && (
                    <div className="flex items-start gap-3">
                      <CookingPot className="w-5 h-5 mt-0.5 text-accent flex-shrink-0" />
                      <div>
                        <h4 className="font-semibold text-foreground">Ingredient Usage</h4>
                        {explanationInfo.missing.length > 0 && (
                          <p className="text-sm text-muted-foreground">You might need to buy: <span className="font-medium text-foreground">{explanationInfo.missing.map(i => `${i.name} (${i.quantity} ${i.unit})`).join(', ')}.</span></p>
                        )}
                        {explanationInfo.partial.length > 0 && (
                          <p className="text-sm text-muted-foreground">You'll have some leftovers of: <span className="font-medium text-foreground">{explanationInfo.partial.map(i => `${i.name} (~${i.remaining} ${i.unit})`).join(', ')}.</span></p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
              <Separator />
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-headline text-lg font-semibold">Ingredients</h3>
                  <div className="flex flex-col items-end gap-1 text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground">Servings</span>
                      <Input
                        type="number"
                        inputMode="decimal"
                        min={1}
                        step={0.1}
                        className="w-24 h-8"
                        aria-label="Servings"
                        value={servingsInput}
                        onChange={(e) => {
                          const val = e.target.value;
                          setServingsInput(val);
                          const num = parseFloat(val);
                          if (!Number.isNaN(num) && num > 0) {
                            setSelectedServings(num);
                          }
                        }}
                      />
                    </div>
                    {selectedServings !== originalServings && (
                      <div className="text-xs">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-auto p-0 text-xs text-muted-foreground hover:text-foreground"
                          onClick={() => {
                            setSelectedServings(originalServings);
                            setServingsInput(String(originalServings));
                          }}
                          aria-label="Reset servings to original"
                          title="Reset servings to original"
                        >
                          Reset to original
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
                <ul className="space-y-2 text-sm">
                  {scaledIngredients.map((ing: Ingredient, index: number) => (
                    <li key={index} className="flex justify-between">
                      <span>{ing.name}</span>
                      <span className="text-muted-foreground">{ing.quantity} {ing.unit}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <Separator />
              <div>
                <h3 className="font-headline text-lg font-semibold mb-3">Instructions</h3>
                <ol className="space-y-4 text-sm list-decimal list-inside">
                  {normalized.instructions.map((step: string, index: number) => (
                    <li key={index}>{step}</li>
                  ))}
                </ol>
              </div>
      </div>
      </div>
    <SheetFooter className="absolute bottom-0 left-0 right-0 bg-background/80 backdrop-blur-sm p-4 border-t flex-col sm:flex-col items-start gap-4">
  <Button className="w-full sm:w-auto" size="lg" onClick={handleCookClick} disabled={isCooking}>
        <ChefHat className="mr-2 h-5 w-5" />
   {isCooking ? 'Updating…' : 'Cooked this Recipe'}
       </Button>
      {!showCookedDialog && (
      <div className="flex w-full justify-between items-center">
        <span className="text-sm font-medium text-muted-foreground">Was this recommendation helpful?</span>
        <div className="flex gap-2">
        <Button
          variant={feedbackSubmitted === "upvote" ? "default" : "outline"}
          size="icon"
          onClick={() => handleFeedback("upvote")}
          disabled={isSubmittingFeedback}
          title={feedbackSubmitted === "upvote" ? "Click again to clear" : "Upvote"}
          aria-label="Upvote recommendation"
        >
          <ThumbsUp className="h-4 w-4" />
        </Button>
        <Button
          variant={feedbackSubmitted === "downvote" ? "destructive" : "outline"}
          size="icon"
          onClick={() => handleFeedback("downvote")}
          disabled={isSubmittingFeedback}
          title={feedbackSubmitted === "downvote" ? "Click again to clear" : "Downvote"}
          aria-label="Downvote recommendation"
        >
          <ThumbsDown className="h-4 w-4" />
        </Button>
        </div>
      </div>
      )}
      </SheetFooter>
        </ScrollArea>
      </SheetContent>
      <AlertDialog open={showCookedDialog} onOpenChange={setShowCookedDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Good job! You cooked {normalized.title} 🎉</AlertDialogTitle>
            <div className="text-sm text-muted-foreground">
              {cookedSummary?.note && (
                <p className="mb-2 text-foreground">{toText(cookedSummary.note)}</p>
              )}
              <p className="mb-2">Servings cooked: <span className="font-medium text-foreground">{Math.max(1, Number(selectedServings) || 1)}</span></p>
              <ul className="list-disc pl-5 space-y-1 text-foreground">
                {cookedSummary?.items.map((it, idx) => {
                  if (it.type === 'quantity') {
                    const delta = it.oldQty - it.newQty;
                    const v = (n: number) => {
                      const r = Math.round((n + Number.EPSILON) * 100) / 100;
                      return Number.isInteger(r) ? r.toString() : r.toString();
                    };
                    return (
                      <li key={idx}>
                        {it.name}: {v(it.oldQty)} {it.unit} <span className="mx-1">→</span> {v(it.newQty)} {it.unit} <span className="text-destructive font-medium">({delta > 0 ? '-' : ''}{v(Math.abs(delta))} {it.unit})</span>
                      </li>
                    );
                  }
                  return (
                    <li key={idx}>{it.name}: {it.status}</li>
                  );
                })}
              </ul>
              <div className="mt-4 flex items-center justify-between">
                <span className="text-sm font-medium text-muted-foreground">Was this recommendation helpful?</span>
                <div className="flex gap-2">
                  <Button
                    variant={feedbackSubmitted === "upvote" ? "default" : "outline"}
                    size="icon"
                    onClick={() => handleFeedback("upvote")}
                    disabled={isSubmittingFeedback}
                    title={feedbackSubmitted === "upvote" ? "Click again to clear" : "Upvote"}
                    aria-label="Upvote recommendation"
                  >
                    <ThumbsUp className="h-4 w-4" />
                  </Button>
                  <Button
                    variant={feedbackSubmitted === "downvote" ? "destructive" : "outline"}
                    size="icon"
                    onClick={() => handleFeedback("downvote")}
                    disabled={isSubmittingFeedback}
                    title={feedbackSubmitted === "downvote" ? "Click again to clear" : "Downvote"}
                    aria-label="Downvote recommendation"
                  >
                    <ThumbsDown className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogAction onClick={() => {
              onCookRecipe(
                normalized,
                Math.max(1, Number(selectedServings) || 1)
              );
              setShowCookedDialog(false);
            }}>Nice!</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Sheet>
  );
}
