"use client";

import * as React from "react";
import { useMemo, useState } from "react";
import {
  SidebarProvider,
  Sidebar,
  SidebarInset,
} from "@/components/ui/sidebar";
import SidebarContent from "@/components/layout/sidebar-content";
import Header from "@/components/layout/header";
import type { InventoryItem, Recipe, UserPreferences, Ingredient } from "@/lib/types";
import { initialInventory, initialRecipes, initialUser } from "@/lib/data";
import RecipeDetails from "@/components/recipes/recipe-details";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import RecipeCard from "@/components/recipes/recipe-card";
import { differenceInDays, formatDistanceToNow } from "date-fns";

export default function Dashboard() {
  const [inventory, setInventory] = useState<InventoryItem[]>(initialInventory);
  const [recipes, setRecipes] = useState<Recipe[]>(initialRecipes);
  const [userPreferences, setUserPreferences] =
    useState<UserPreferences>(initialUser);
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);

  const handleUpdateInventory = (newInventory: InventoryItem[]) => {
    setInventory(newInventory);
  };

  const handleCookRecipe = (recipe: Recipe) => {
    const updatedInventory = inventory.map(invItem => {
      const recipeIngredient = recipe.ingredients.find(
        ing => ing.name.toLowerCase() === invItem.name.toLowerCase()
      );
      if (recipeIngredient) {
        return {
          ...invItem,
          quantity: Math.max(0, invItem.quantity - recipeIngredient.quantity),
        };
      }
      return invItem;
    }).filter(item => item.quantity > 0);
  
    setInventory(updatedInventory);
    setSelectedRecipe(null);
  };

  const handleUpdatePreferences = (newPreferences: UserPreferences) => {
    setUserPreferences(newPreferences);
  };

  const expiringSoonItems = useMemo(() => {
    return inventory
      .filter((item) => {
        const daysUntilExpiry = differenceInDays(new Date(item.expiryDate), new Date());
        return daysUntilExpiry >= 0 && daysUntilExpiry <= 7;
      })
      .sort(
        (a, b) =>
          new Date(a.expiryDate).getTime() - new Date(b.expiryDate).getTime()
      );
  }, [inventory]);

  const recommendedRecipes = useMemo(() => {
    const inventoryMap = new Map(
      inventory.map(item => [item.name.toLowerCase(), item])
    );
    const expiringSoonNames = new Set(
      expiringSoonItems.map(i => i.name.toLowerCase())
    );

    const updatedRecipes = recipes.map(recipe => {
      let weightedMatchSum = 0;
      let expiringMatches = 0;
      let totalPossibleWeight = 0;

      recipe.ingredients.forEach(ingredient => {
        const inventoryItem = inventoryMap.get(ingredient.name.toLowerCase());
        const weight = 1;
        totalPossibleWeight += weight;

        if (inventoryItem) {
          const quantityRatio = Math.min(inventoryItem.quantity / ingredient.quantity, 1.0);
          weightedMatchSum += quantityRatio * weight;

          if (expiringSoonNames.has(ingredient.name.toLowerCase())) {
            expiringMatches++;
          }
        }
      });
      
      const matchPercentage = totalPossibleWeight > 0 ? (weightedMatchSum / totalPossibleWeight) * 100 : 0;
      const expiringIngredientBonus = expiringMatches * 10;
      const score = matchPercentage + expiringIngredientBonus;

      return {
        ...recipe,
        matchPercentage: Math.round(matchPercentage),
        expiringIngredientsCount: expiringMatches,
        score,
      };
    });

    const filteredRecipes = updatedRecipes.filter((recipe) => {
        const hasAllergens = recipe.ingredients.some(ingredient => userPreferences.allergies.includes(ingredient.name.toLowerCase()));
        const hasDislikes = recipe.ingredients.some(ingredient => userPreferences.dislikes.includes(ingredient.name.toLowerCase()));
        return !hasAllergens && !hasDislikes;
    });

    return filteredRecipes.sort((a, b) => b.score - a.score);
  }, [recipes, inventory, userPreferences, expiringSoonItems]);

  return (
    <SidebarProvider defaultOpen>
      <Sidebar>
        <SidebarContent
          inventory={inventory}
          onUpdateInventory={handleUpdateInventory}
          preferences={userPreferences}
          onUpdatePreferences={handleUpdatePreferences}
        />
      </Sidebar>
      <SidebarInset>
        <Header />
        <main className="p-4 sm:p-6 lg:p-8 space-y-8">
          <div>
            <h1 className="font-headline text-3xl font-bold text-foreground">
              Welcome Back!
            </h1>
            <p className="text-muted-foreground">
              Here&apos;s what&apos;s cooking in your pantry.
            </p>
          </div>

          <div className="grid gap-8 lg:grid-cols-3">
            <div className="lg:col-span-2 space-y-6">
              <h2 className="font-headline text-2xl font-semibold">
                Recommended For You
              </h2>
              <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
                {recommendedRecipes.map((recipe) => (
                  <RecipeCard
                    key={recipe.id}
                    recipe={recipe}
                    onSelectRecipe={setSelectedRecipe}
                  />
                ))}
              </div>
            </div>
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="font-headline">Expiring Soon</CardTitle>
                </CardHeader>
                <CardContent>
                  {expiringSoonItems.length > 0 ? (
                    <ul className="space-y-4">
                      {expiringSoonItems.map((item) => (
                        <li key={item.id} className="flex justify-between items-center">
                          <div>
                            <p className="font-medium">{item.name}</p>
                            <p className="text-sm text-muted-foreground">
                              {item.quantity} {item.unit}
                            </p>
                          </div>
                          <Badge variant="destructive">
                            Expires in {formatDistanceToNow(new Date(item.expiryDate))}
                          </Badge>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-muted-foreground text-sm">
                      Nothing is expiring soon. Cook freely!
                    </p>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </main>
        {selectedRecipe && (
          <RecipeDetails
            recipe={selectedRecipe}
            userPreferences={userPreferences}
            inventory={inventory}
            open={!!selectedRecipe}
            onOpenChange={(isOpen) => !isOpen && setSelectedRecipe(null)}
            onCookRecipe={handleCookRecipe}
          />
        )}
      </SidebarInset>
    </SidebarProvider>
  );
}