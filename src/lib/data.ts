import { InventoryItem, Recipe, UserPreferences } from './types';
import { addDays } from 'date-fns';

const today = new Date();

export const initialInventory: InventoryItem[] = [
  {
    id: 'inv1',
    name: 'Spaghetti',
    quantity: 500,
    unit: 'g',
    purchaseDate: today.toISOString(),
    expiryDate: addDays(today, 365).toISOString(),
    shelfLife: 365,
  },
  {
    id: 'inv2',
    name: 'Garlic',
    quantity: 5,
    unit: 'cloves',
    purchaseDate: today.toISOString(),
    expiryDate: addDays(today, 3).toISOString(),
    shelfLife: 21,
  },
  {
    id: 'inv3',
    name: 'Olive Oil',
    quantity: 500,
    unit: 'ml',
    purchaseDate: today.toISOString(),
    expiryDate: addDays(today, 730).toISOString(),
    shelfLife: 730,
  },
  {
    id: 'inv4',
    name: 'Chicken Breast',
    quantity: 2,
    unit: 'pcs',
    purchaseDate: today.toISOString(),
    expiryDate: addDays(today, 2).toISOString(),
    shelfLife: 4,
  },
  {
    id: 'inv5',
    name: 'Lettuce',
    quantity: 1,
    unit: 'head',
    purchaseDate: today.toISOString(),
    expiryDate: addDays(today, 6).toISOString(),
    shelfLife: 7,
  },
  {
    id: 'inv6',
    name: 'Tomato',
    quantity: 4,
    unit: 'pcs',
    purchaseDate: today.toISOString(),
    expiryDate: addDays(today, 8).toISOString(),
    shelfLife: 14,
  },
  {
    id: 'inv7',
    name: 'Onion',
    quantity: 3,
    unit: 'pcs',
    purchaseDate: today.toISOString(),
    expiryDate: addDays(today, 30).toISOString(),
    shelfLife: 40,
  },
  {
    id: 'inv8',
    name: 'Eggs',
    quantity: 12,
    unit: 'pcs',
    purchaseDate: today.toISOString(),
    expiryDate: addDays(today, 21).toISOString(),
    shelfLife: 28,
  },
];

export const initialRecipes: Recipe[] = [
  {
    id: 'rec1',
    title: 'Spaghetti Aglio e Olio',
    description: 'A classic Italian dish that is simple, delicious, and quick to make.',
    ingredients: [
      { name: 'Spaghetti', quantity: 200, unit: 'g' },
      { name: 'Garlic', quantity: 3, unit: 'cloves' },
      { name: 'Olive Oil', quantity: 4, unit: 'tbsp' },
      { name: 'Red Pepper Flakes', quantity: 0.5, unit: 'tsp' },
      { name: 'Parsley', quantity: 2, unit: 'tbsp' },
    ],
    instructions: [
      'Cook spaghetti according to package directions.',
      'Meanwhile, heat olive oil in a large skillet over medium heat. Add garlic and red pepper flakes, cook until garlic is golden.',
      'Drain spaghetti, reserving 1/2 cup of pasta water.',
      'Add spaghetti and parsley to the skillet. Toss to combine, adding pasta water as needed to create a sauce.',
      'Serve immediately.',
    ],
    imageId: 'recipe1',
  },
  {
    id: 'rec2',
    title: 'Grilled Chicken Salad',
    description: 'A healthy and refreshing salad with tender grilled chicken.',
    ingredients: [
      { name: 'Chicken Breast', quantity: 1, unit: 'pc' },
      { name: 'Lettuce', quantity: 0.5, unit: 'head' },
      { name: 'Tomato', quantity: 1, unit: 'pc' },
      { name: 'Cucumber', quantity: 0.5, unit: 'pc' },
      { name: 'Olive Oil', quantity: 2, unit: 'tbsp' },
      { name: 'Lemon Juice', quantity: 1, unit: 'tbsp' },
    ],
    instructions: [
      'Season and grill chicken breast until cooked through. Let it rest, then slice.',
      'Chop lettuce, tomato, and cucumber. Place in a large bowl.',
      'Add sliced chicken to the bowl.',
      'Drizzle with olive oil and lemon juice. Toss to combine.',
      'Serve fresh.',
    ],
    imageId: 'recipe2',
  },
  {
    id: 'rec3',
    title: 'Classic Tomato Soup',
    description: 'Creamy and comforting tomato soup, perfect with a grilled cheese sandwich.',
    ingredients: [
      { name: 'Tomato', quantity: 4, unit: 'pcs' },
      { name: 'Onion', quantity: 1, unit: 'pc' },
      { name: 'Garlic', quantity: 2, unit: 'cloves' },
      { name: 'Vegetable Broth', quantity: 2, unit: 'cups' },
      { name: 'Heavy Cream', quantity: 0.5, unit: 'cup' },
    ],
    instructions: [
      'Sauté onion and garlic in a pot.',
      'Add chopped tomatoes and vegetable broth. Simmer for 20 minutes.',
      'Blend the soup until smooth.',
      'Stir in heavy cream and season with salt and pepper.',
      'Serve hot.',
    ],
    imageId: 'recipe3',
  },
  {
    id: 'rec4',
    title: 'Simple Scrambled Eggs',
    description: 'Quick and fluffy scrambled eggs for a perfect breakfast.',
    ingredients: [
      { name: 'Eggs', quantity: 3, unit: 'pcs' },
      { name: 'Milk', quantity: 2, unit: 'tbsp' },
      { name: 'Butter', quantity: 1, unit: 'tbsp' },
    ],
    instructions: [
      'Whisk eggs and milk in a bowl.',
      'Melt butter in a non-stick skillet over medium heat.',
      'Pour in the egg mixture. Cook, stirring gently, until eggs are set.',
      'Season with salt and pepper.',
      'Serve immediately.',
    ],
    imageId: 'recipe4',
  },
  {
    id: 'rec5',
    title: 'Vegetable Stir-fry',
    description: 'A colorful and healthy stir-fry with a variety of vegetables.',
    ingredients: [
      { name: 'Broccoli', quantity: 1, unit: 'cup' },
      { name: 'Carrot', quantity: 1, unit: 'pc' },
      { name: 'Bell Pepper', quantity: 1, unit: 'pc' },
      { name: 'Onion', quantity: 0.5, unit: 'pc' },
      { name: 'Soy Sauce', quantity: 3, unit: 'tbsp' },
    ],
    instructions: [
        'Chop all vegetables.',
        'Heat oil in a wok or large skillet over high heat.',
        'Add vegetables and stir-fry for 5-7 minutes until tender-crisp.',
        'Add soy sauce and stir to coat.',
        'Serve over rice or noodles.',
    ],
    imageId: 'recipe5'
  },
  {
    id: 'rec6',
    title: 'Caprese Salad',
    description: 'An elegant Italian salad, showcasing fresh tomatoes, mozzarella, and basil.',
    ingredients: [
        { name: 'Tomato', quantity: 2, unit: 'pcs' },
        { name: 'Fresh Mozzarella', quantity: 1, unit: 'ball' },
        { name: 'Fresh Basil', quantity: 1, unit: 'bunch' },
        { name: 'Olive Oil', quantity: 2, unit: 'tbsp' },
    ],
    instructions: [
        'Slice tomatoes and mozzarella.',
        'Arrange alternating slices of tomato and mozzarella on a plate.',
        'Tuck fresh basil leaves in between.',
        'Drizzle with high-quality olive oil.',
        'Season with salt and pepper before serving.',
    ],
    imageId: 'recipe6'
  }
];

export const initialUser: UserPreferences = {
  userId: 'user123',
  allergies: ['peanuts', 'shellfish'],
  dislikes: ['cilantro', 'olives'],
};
