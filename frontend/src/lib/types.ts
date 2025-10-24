export interface InventoryItem {
  id: string;
  item_name: string;
  quantity: number;
  unit: string;
  expiry_date: string;
  user_id: string;
  added_at: string;
  updated_at: string;
}

// Frontend-only interface for the form
export interface InventoryFormItem {
  id: string;
  name: string;
  quantity: number;
  unit: string;
  purchaseDate: string;
  expiryDate: string;
  shelfLife: number;
}

// API request interfaces
export interface AddInventoryRequest {
  item_name: string;
  quantity: number;
  unit?: string;
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
  image?: string; // Spoonacular image URL
  matchPercentage?: number;
  expiringIngredientsCount?: number;
  score?: number;
}

// Normalized recipe shape used by the frontend after converting Spoonacular payloads
export interface NormalizedIngredient {
  name: string;
  quantity: number;
  unit: string;
  original?: unknown;
}

export type NormalizedRecipe = Omit<Recipe, "ingredients" | "instructions"> & {
  ingredients: NormalizedIngredient[];
  instructions: string[];
  matchPercentage: number;
};

export interface User {
  id: string;
  email: string;
  name: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  name: string;
  password: string;
}

export interface UserSettings {
  userId: string;
  name?: string;
  email?: string;
}

export interface UserPreferences {
  userId: string;
  allergies: string[];
  dislikes: string[];
  dietaryRestrictions?: string[];
  cookingSkillLevel?: 'beginner' | 'intermediate' | 'advanced';
  preferredCuisines?: string[];
}
