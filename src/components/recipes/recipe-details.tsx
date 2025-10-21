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
import { ThumbsUp, ThumbsDown, Sparkles } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import type { Recipe, UserPreferences, InventoryItem } from "@/lib/types";
import { PlaceHolderImages } from "@/lib/placeholder-images";
import { getRecipeExplanation, submitFeedback } from "@/app/actions";
import { Skeleton } from "../ui/skeleton";
import { differenceInDays } from "date-fns";

interface RecipeDetailsProps {
  recipe: Recipe;
  userPreferences: UserPreferences;
  inventory: InventoryItem[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function RecipeDetails({
  recipe,
  userPreferences,
  inventory,
  open,
  onOpenChange,
}: RecipeDetailsProps) {
  const { toast } = useToast();
  const [explanation, setExplanation] = useState<string>("");
  const [isLoadingExplanation, setIsLoadingExplanation] = useState<boolean>(true);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState<"upvote" | "downvote" | null>(null);

  const image = PlaceHolderImages.find((img) => img.id === recipe.imageId);

  const expiringIngredients = useMemo(() => {
    const recipeIngredients = new Set(recipe.ingredients.map(i => i.name.toLowerCase()));
    return inventory.filter(item => {
        const daysUntilExpiry = differenceInDays(new Date(item.expiryDate), new Date());
        return daysUntilExpiry <= 7 && recipeIngredients.has(item.name.toLowerCase());
    }).map(item => item.name);
  }, [inventory, recipe.ingredients]);

  useEffect(() => {
    if (recipe) {
      setIsLoadingExplanation(true);
      setFeedbackSubmitted(null);
      
      const fetchExplanation = async () => {
        const result = await getRecipeExplanation({
          recipeName: recipe.title,
          expiringIngredients: expiringIngredients,
          allergies: userPreferences.allergies,
          inventoryMatchPercentage: recipe.matchPercentage || 0,
        });
        setExplanation(result.explanation);
        setIsLoadingExplanation(false);
      };

      fetchExplanation();
    }
  }, [recipe, expiringIngredients, userPreferences]);

  const handleFeedback = async (feedbackType: "upvote" | "downvote") => {
    if (feedbackSubmitted) return;
    setFeedbackSubmitted(feedbackType);

    const result = await submitFeedback({
      recipeId: recipe.id,
      feedbackType,
      userId: userPreferences.userId,
    });
    
    toast({
      title: result.success ? "Feedback Submitted" : "Error",
      description: result.message,
      variant: result.success ? "default" : "destructive",
    });
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-2xl w-full p-0">
        <ScrollArea className="h-full">
          <div className="pb-16">
            <SheetHeader className="relative">
              {image && (
                <Image
                  alt={recipe.title}
                  className="aspect-video w-full object-cover"
                  height={337}
                  src={image.imageUrl}
                  width={600}
                  data-ai-hint={image.imageHint}
                />
              )}
              <div className="p-6 text-left space-y-2">
                <SheetTitle className="font-headline text-3xl">{recipe.title}</SheetTitle>
                <SheetDescription>{recipe.description}</SheetDescription>
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
                  {recipe.ingredients.map((ing, index) => (
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
                  {recipe.instructions.map((step, index) => (
                    <li key={index}>{step}</li>
                  ))}
                </ol>
              </div>
            </div>
          </div>
          <SheetFooter className="absolute bottom-0 left-0 right-0 bg-background/80 backdrop-blur-sm p-4 border-t">
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
