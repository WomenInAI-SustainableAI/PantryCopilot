import { UserPreferences } from './types';

export const initialUser: UserPreferences = {
  userId: '',
  allergies: [],
  dislikes: [],
  dietaryRestrictions: [],
  cookingSkillLevel: 'beginner',
  preferredCuisines: [],
};

// Recommendation limits to show in the UI
export const RECOMMEND_LIMITS: number[] = [3, 5, 10];
