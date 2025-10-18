export interface InventoryItem {
  id: string;
  name: string;
  quantity: number;
  unit: string;
  purchaseDate: string;
  expiryDate: string;
  shelfLife: number; // in days
}

export interface Ingredient {
  name: string;
  quantity: number;
  unit: string;
}

export interface Recipe {
  id: string;
  title: string;
  description: string;
  ingredients: Ingredient[];
  instructions: string[];
  imageId: string;
  matchPercentage?: number;
  expiringIngredientsCount?: number;
  score?: number;
}

export interface UserPreferences {
  userId: string;
  allergies: string[];
  dislikes: string[];
}
