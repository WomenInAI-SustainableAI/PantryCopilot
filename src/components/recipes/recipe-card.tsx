"use client";

import Image from "next/image";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Recipe } from "@/lib/types";
import { PlaceHolderImages } from "@/lib/placeholder-images";
import { Flame, Percent } from "lucide-react";

interface RecipeCardProps {
  recipe: Recipe;
  onSelectRecipe: (recipe: Recipe) => void;
}

export default function RecipeCard({ recipe, onSelectRecipe }: RecipeCardProps) {
  const image = PlaceHolderImages.find((img) => img.id === recipe.imageId);

  return (
    <Card
      className="overflow-hidden flex flex-col cursor-pointer hover:shadow-lg transition-shadow duration-300"
      onClick={() => onSelectRecipe(recipe)}
    >
      <CardHeader className="p-0 relative">
        {image && (
          <Image
            alt={recipe.title}
            className="aspect-video w-full object-cover"
            data-ai-hint={image.imageHint}
            height={337}
            src={image.imageUrl}
            width={600}
          />
        )}
        <div className="absolute top-2 right-2 flex flex-col gap-2">
            <Badge className="bg-primary/90 text-primary-foreground border-primary-foreground/20 backdrop-blur-sm">
                <Percent className="w-3 h-3 mr-1" />
                {recipe.matchPercentage}% Match
            </Badge>
            {recipe.expiringIngredientsCount && recipe.expiringIngredientsCount > 0 ? (
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
        <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
          {recipe.description}
        </p>
      </CardContent>
      <CardFooter className="p-4 pt-0">
        <Button className="w-full" variant="default">View Recipe</Button>
      </CardFooter>
    </Card>
  );
}
