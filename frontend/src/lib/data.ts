import { UserPreferences } from './types';

export const initialUser: UserPreferences = {
  userId: '',
  allergies: [],
  dislikes: [],
  dietaryRestrictions: [],
  cookingSkillLevel: 'beginner',
  preferredCuisines: [],
};

// Common cuisine options supported by Spoonacular complexSearch
export const CUISINES: string[] = [
  'african','american','british','cajun','caribbean','chinese','eastern european',
  'european','french','german','greek','indian','irish','italian','japanese',
  'jewish','korean','latin american','mediterranean','mexican','middle eastern',
  'nordic','southern','spanish','thai','vietnamese'
];

// Dish types per Spoonacular “type” parameter
export const DISH_TYPES: string[] = [
  'main course','side dish','dessert','appetizer','salad','bread','breakfast',
  'soup','beverage','sauce','marinade','fingerfood','snack','drink'
];

// Recommendation limits to show in the UI
export const RECOMMEND_LIMITS: number[] = [3, 5, 10];
