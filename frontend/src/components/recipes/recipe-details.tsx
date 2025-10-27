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
import { useToast } from "@/hooks/use-toast";
import type { Recipe, NormalizedRecipe, UserPreferences, InventoryFormItem, Ingredient } from "@/lib/types";
import { PlaceHolderImages } from "@/lib/placeholder-images";
import { submitFeedback } from "@/app/actions";
import { normalizeRecipe } from "@/lib/normalize-recipe";
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
  onCookRecipe: (recipe: NormalizedRecipe) => void;
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

  const normalized = useMemo(() => normalizeRecipe(recipe), [recipe]);

  const sanitizedDescription = useMemo(() => sanitizeHtml(normalized.description || ''), [normalized.description]);

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

  // Client-side explanation info (inspired by v2)
  const explanationInfo = useMemo<ExplanationInfo>(() => {
    const inventoryMap = new Map<string, InventoryFormItem>((inventory || []).map(item => [
      (item?.name || '').toLowerCase(),
      item
    ]));

    const allergySet = new Set((userPreferences?.allergies || []).map(a => (a || '').toLowerCase()));
    const hasAllergens = (normalized.ingredients || []).some((ing) => allergySet.has((ing?.name || '').toLowerCase()));

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
    // If the same button is clicked again, do nothing (no-op)
    if (feedbackSubmitted === feedbackType) return;
    if (isSubmittingFeedback) return;
    setIsSubmittingFeedback(true);
    // Optimistically set selection so UI reflects intent immediately
    setFeedbackSubmitted(feedbackType);

    const result = await submitFeedback({
      recipeId: normalized.id,
      // submitFeedback expects a FeedbackType; cast here to satisfy the API surface
      feedbackType: feedbackType as any,
      userId: userPreferences.userId,
      recipeTitle: normalized.title,
      // Try to include categories when available from raw recipe payload
      recipeCategories: [
        ...((recipe as any)?.dishTypes || []),
        ...((recipe as any)?.cuisines || []),
      ].filter(Boolean),
    });
    
    toast({
      title: result.success ? "Feedback Submitted" : "Error",
      description: result.message,
      variant: result.success ? "default" : "destructive",
    });
    if (!result.success) {
      // allow retry if there was an error
      setFeedbackSubmitted(null);
    }
    setIsSubmittingFeedback(false);
  };

  const handleCookClick = () => {
  // Pass a normalized recipe shape to the parent so inventory updates work
  // (parent expects recipe.ingredients to be objects with .name and .quantity)
  onCookRecipe(normalized);
    toast({
      title: "Bon Appétit!",
      description: `Your inventory has been updated after cooking ${normalized.title}.`,
    });
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
                <h3 className="font-headline text-lg font-semibold mb-3">Ingredients</h3>
                <ul className="space-y-2 text-sm">
                  {normalized.ingredients.map((ing: Ingredient, index: number) => (
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
       <Button className="w-full sm:w-auto" size="lg" onClick={handleCookClick}>
        <ChefHat className="mr-2 h-5 w-5" />
        Cooked this Recipe
       </Button>
      <div className="flex w-full justify-between items-center">
        <span className="text-sm font-medium text-muted-foreground">Was this recommendation helpful?</span>
        <div className="flex gap-2">
        <Button
          variant={feedbackSubmitted === "upvote" ? "default" : "outline"}
          size="icon"
          onClick={() => handleFeedback("upvote")}
          disabled={isSubmittingFeedback}
        >
          <ThumbsUp className="h-4 w-4" />
        </Button>
        <Button
          variant={feedbackSubmitted === "downvote" ? "destructive" : "outline"}
          size="icon"
          onClick={() => handleFeedback("downvote")}
          disabled={isSubmittingFeedback}
        >
          <ThumbsDown className="h-4 w-4" />
        </Button>
        </div>
      </div>
      </SheetFooter>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
