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
import type { InventoryItem, Recipe, UserPreferences } from "@/lib/types";
import { initialInventory, initialRecipes, initialUser } from "@/lib/data";
import RecipeDetails from "@/components/recipes/recipe-details";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import RecipeCard from "@/components/recipes/recipe-card";
import { differenceInDays, formatDistanceToNow } from "date-fns";

export default function DashboardPage() {
  const [inventory, setInventory] = useState<InventoryItem[]>(initialInventory);
  const [recipes, setRecipes] = useState<Recipe[]>(initialRecipes);
  const [userPreferences, setUserPreferences] =
    useState<UserPreferences>(initialUser);
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);

  const handleUpdateInventory = (newInventory: InventoryItem[]) => {
    setInventory(newInventory);
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
    const updatedRecipes = recipes.map((recipe) => {
      let matches = 0;
      let expiringMatches = 0;
      const recipeIngredients = new Set(
        recipe.ingredients.map((i) => i.name.toLowerCase())
      );
      const inventoryNames = new Set(
        inventory.map((i) => i.name.toLowerCase())
      );
      const expiringSoonNames = new Set(
        expiringSoonItems.map((i) => i.name.toLowerCase())
      );

      for (const ingredient of recipeIngredients) {
        if (inventoryNames.has(ingredient)) {
          matches++;
          if (expiringSoonNames.has(ingredient)) {
            expiringMatches++;
          }
        }
      }

      const matchPercentage =
        recipe.ingredients.length > 0
          ? Math.round((matches / recipe.ingredients.length) * 100)
          : 0;

      const expiringIngredientBonus =
        expiringSoonItems.length > 0
          ? (expiringMatches / expiringSoonItems.length) * 30
          : 0;
      
      const score = matchPercentage * 0.7 + expiringIngredientBonus * 0.3;

      return {
        ...recipe,
        matchPercentage,
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
          />
        )}
      </SidebarInset>
    </SidebarProvider>
  );
}
