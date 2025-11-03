"use client";

import Image from "next/image";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Recipe, NormalizedRecipe } from "@/lib/types";
// Lightweight sanitizer for recipe card descriptions (same rules as details view)
function sanitizeHtmlForCard(dirty: string): string {
  if (!dirty) return '';
  try {
    const parser = new DOMParser();
    const doc = parser.parseFromString(dirty, 'text/html');
    const allowed = new Set(['b','strong','i','em','a','p']);
    const container = document.createElement('div');
    function walk(node: ChildNode, target: Node) {
      if (node.nodeType === Node.TEXT_NODE) {
        target.appendChild(document.createTextNode(node.textContent || ''));
        return;
      }
      if (node.nodeType === Node.ELEMENT_NODE) {
        const el = node as Element;
        const tag = el.tagName.toLowerCase();
        if (!allowed.has(tag)) {
          el.childNodes.forEach(c => walk(c, target));
          return;
        }
        const newEl = document.createElement(tag);
        if (tag === 'a') {
          const href = el.getAttribute('href') || '';
          if (/^(https?:\/\/|mailto:|#)/i.test(href)) {
            newEl.setAttribute('href', href);
            newEl.setAttribute('target', '_blank');
            newEl.setAttribute('rel', 'noopener noreferrer');
          }
        }
        el.childNodes.forEach(c => walk(c, newEl));
        target.appendChild(newEl);
      }
    }
    doc.body.childNodes.forEach(n => walk(n, container));
    return container.innerHTML;
  } catch (e) {
    return '';
  }
}
import { PlaceHolderImages } from "@/lib/placeholder-images";
import { Flame, Percent } from "lucide-react";

interface RecipeCardProps {
  recipe: Recipe | NormalizedRecipe;
  onSelectRecipe: (recipe: Recipe | NormalizedRecipe) => void;
}

export default function RecipeCard({ recipe, onSelectRecipe }: RecipeCardProps) {
  // Use Spoonacular image if available, fallback to placeholder
  const spoonacularImage = recipe.image || `https://spoonacular.com/recipeImages/${recipe.id}-312x231.jpg`;
  const placeholderImage = PlaceHolderImages.find((img) => img.id === recipe.imageId);
  const imageUrl = spoonacularImage || placeholderImage?.imageUrl;

  // Normalize match percentage: backend sometimes returns a number or a string
  // (e.g. "80" or "80%"), so coerce to a numeric value and strip non-numeric
  // characters before rounding to avoid rendering duplicate percent signs.
  const rawMatch = recipe.matchPercentage ?? 0;
  const numericMatch = (() => {
    if (typeof rawMatch === 'number') return rawMatch;
    try {
      const cleaned = String(rawMatch).replace(/[^0-9.-]+/g, '');
      const n = Number(cleaned);
      return isNaN(n) ? 0 : n;
    } catch {
      return 0;
    }
  })();

  return (
    <Card
      className="overflow-hidden flex flex-col cursor-pointer hover:shadow-lg transition-shadow duration-300"
      onClick={() => onSelectRecipe(recipe)}
    >
      <CardHeader className="p-0 relative">
        {imageUrl && (
          <Image
            alt={recipe.title}
            className="aspect-video w-full object-cover"
            height={337}
            src={imageUrl}
            width={600}
          />
        )}
        <div className="absolute top-2 right-2 flex flex-col gap-2">
          <Badge className="bg-primary/90 text-primary-foreground border-primary-foreground/20 backdrop-blur-sm flex items-center justify-center text-center">
            <span className="text-xs font-semibold">{Math.round(numericMatch)}% match</span>
          </Badge>
      {/* Show expiring badge only when the count is explicitly > 0. */}
      {(recipe.expiringIngredientsCount ?? 0) > 0 ? (
        <Badge variant="destructive">
          <Flame className="w-3 h-3 mr-1" />
          {recipe.expiringIngredientsCount} Expiring
        </Badge>
      ) : null}
        </div>
      </CardHeader>
      <CardContent className="p-4 flex-grow">
        <h3 className="font-headline text-lg font-semibold leading-tight">
          {recipe.title}
        </h3>
        {/* Category badges (CMAB) */}
        {Array.isArray((recipe as any)?.categories) && (recipe as any).categories.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {((recipe as any).categories as string[]).slice(0, 3).map((c) => (
              <Badge key={c} variant="outline" className="text-xs capitalize">
                {c.replace(/_/g, ' ')}
              </Badge>
            ))}
          </div>
        )}
        <div className="text-sm text-muted-foreground mt-1 line-clamp-2" dangerouslySetInnerHTML={{ __html: sanitizeHtmlForCard(recipe.description || '') }} />
      </CardContent>
      <CardFooter className="p-4 pt-0">
        <Button className="w-full" variant="default">View Recipe</Button>
      </CardFooter>
    </Card>
  );
}
