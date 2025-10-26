"use client";

import { useEffect, useState, useMemo } from "react";
import Image from "next/image";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ThumbsUp, ThumbsDown, Sparkles, ChefHat } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import type { Recipe, NormalizedRecipe, UserPreferences, InventoryFormItem, Ingredient } from "@/lib/types";
import { PlaceHolderImages } from "@/lib/placeholder-images";
import { getRecipeExplanation, submitFeedback } from "@/app/actions";
import { Skeleton } from "../ui/skeleton";
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

// Helpers to normalize incoming recipe shapes from the backend/spoonacular
function stripHtmlToSteps(html?: string): string[] {
  if (!html) return [];
  // Replace <li> with separator then strip tags
  const withSep = html.replace(/<li[^>]*>/gi, "||").replace(/<\/li>/gi, "");
  const text = withSep.replace(/<[^>]+>/g, "");
  return text.split("||").map((s) => s.trim()).filter(Boolean);
}

// (kept HTML in description; we'll sanitize when rendering using DOMPurify)

function normalizeRecipe(raw: any): NormalizedRecipe {
  if (!raw) return { id: '', title: '', description: '', ingredients: [], instructions: [], imageId: '', matchPercentage: 0 } as NormalizedRecipe;

  // Instructions: prefer analyzedInstructions -> steps, otherwise parse `instructions` HTML or coerce string -> array
  let instructions: string[] = [];
  if (Array.isArray(raw?.analyzedInstructions) && raw.analyzedInstructions.length) {
    const steps = raw.analyzedInstructions[0]?.steps || [];
    instructions = steps.map((s: any) => s?.step).filter(Boolean);
  } else if (Array.isArray(raw?.instructions)) {
    instructions = raw.instructions.filter(Boolean);
  } else if (typeof raw?.instructions === "string") {
    const parsed = stripHtmlToSteps(raw.instructions);
    instructions = parsed.length ? parsed : raw.instructions.split("\n").map((s: string) => s.trim()).filter(Boolean);
  }

  // Ingredients: prefer extendedIngredients -> map to {name, quantity, unit}
  let ingredients: Array<{ name: string; quantity: number; unit: string }> = [];
  if (Array.isArray(raw?.extendedIngredients) && raw.extendedIngredients.length) {
    ingredients = raw.extendedIngredients.map((ing: any) => ({
      name: ing?.name || ing?.original || "",
      quantity: typeof ing?.amount === "number" ? ing.amount : 0,
      unit: ing?.unit || (ing?.measures?.metric?.unitShort) || "",
    }));
  } else if (Array.isArray(raw?.ingredients) && raw.ingredients.length) {
    ingredients = raw.ingredients.map((i: any) =>
      typeof i === "string" ? { name: i, quantity: 0, unit: "" } : { name: i?.name || "", quantity: i?.quantity ?? 0, unit: i?.unit || "" }
    );
  }

  const matchPercentage = raw?.scoring?.match_percentage ?? raw?.matchPercentage ?? raw?.scoring?.matchPercentage ?? 0;

  // Build a Recipe-shaped object
  const recipeObj: NormalizedRecipe = {
    id: raw?.id ? String(raw.id) : (raw?.recipeId ? String(raw.recipeId) : ''),
  title: raw?.title || '',
  description: raw?.summary || raw?.description || '',
    ingredients: ingredients as any,
    instructions,
    imageId: raw?.imageId || '',
    image: raw?.image || raw?.imageUrl,
    matchPercentage: matchPercentage,
  };

  return recipeObj;
}

export default function RecipeDetails({
  recipe,
  userPreferences,
  inventory,
  open,
  onOpenChange,
  onCookRecipe,
}: RecipeDetailsProps) {
  const { toast } = useToast();
  const [explanation, setExplanation] = useState<string>("");
  const [isLoadingExplanation, setIsLoadingExplanation] = useState<boolean>(true);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState<"upvote" | "downvote" | null>(null);

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

  useEffect(() => {
    if (recipe) {
      setIsLoadingExplanation(true);
      setFeedbackSubmitted(null);
      const fetchExplanation = async () => {
        const result = await getRecipeExplanation({
          recipeName: normalized.title,
          expiringIngredients,
          allergies: userPreferences.allergies,
          inventoryMatchPercentage: normalized.matchPercentage ?? 0,
          missingIngredients: missingIngredients.map((i: Ingredient) => i.name),
        });
        setExplanation(result.explanation);
        setIsLoadingExplanation(false);
      };

      fetchExplanation();
    }
  }, [recipe, expiringIngredients, userPreferences, missingIngredients]);

  const handleFeedback = async (feedbackType: "upvote" | "downvote") => {
    if (feedbackSubmitted) return;
    setFeedbackSubmitted(feedbackType);

    const result = await submitFeedback({
      recipeId: normalized.id,
      // submitFeedback expects a FeedbackType; cast here to satisfy the API surface
      feedbackType: feedbackType as any,
      userId: userPreferences.userId,
    });
    
    toast({
      title: result.success ? "Feedback Submitted" : "Error",
      description: result.message,
      variant: result.success ? "default" : "destructive",
    });
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
                {isLoadingExplanation ? (
                    <div className="space-y-2">
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-4 w-3/4" />
                    </div>
                ) : (
                    <p className="text-sm text-muted-foreground bg-muted p-4 rounded-lg">{explanation}</p>
                )}
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
          disabled={!!feedbackSubmitted}
        >
          <ThumbsUp className="h-4 w-4" />
        </Button>
        <Button
          variant={feedbackSubmitted === "downvote" ? "destructive" : "outline"}
          size="icon"
          onClick={() => handleFeedback("downvote")}
          disabled={!!feedbackSubmitted}
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
