"""
Mock Recommendations Dataset and helpers.

Provides a small Spoonacular-like set of recipes for demo/fallback when the
external API is unavailable or disabled. Keep this light-weight and safe to ship.
"""
from __future__ import annotations
from typing import List, Dict, Optional, Set, Tuple
from src.services.cmab_service import RecipeCategory


def get_mock_recommendations_raw() -> List[Dict]:
    """Return a small set of Spoonacular-like recipe objects.

    Shape mirrors the important fields used by the frontend normalizer:
    - id, title, image, readyInMinutes, servings, cuisines, dishTypes, summary
    - extendedIngredients: [{ name, amount?, unit?, measures: { metric: { amount, unitShort } } }]
    - analyzedInstructions: [{ steps: [{ number, step }] }]
    - scoring: { overall_score, match_percentage }
    """
    return [
        {
            "id": 700001,
            "image": "https://img.spoonacular.com/recipes/700001-556x370.jpg",
            "title": "Italian Tomato Basil Pasta",
            "readyInMinutes": 25,
            "servings": 2,
            "cuisines": ["italian"],
            "dishTypes": ["main course", "dinner"],
            "summary": "A quick pasta with tomatoes and basil.",
            "extendedIngredients": [
                {"name": "spaghetti", "amount": 200, "unit": "g", "measures": {"metric": {"amount": 200, "unitShort": "g"}, "us": {"amount": 7.05, "unitShort": "oz"}}},
                {"name": "tomatoes", "amount": 2, "unit": "", "measures": {"metric": {"amount": 2, "unitShort": ""}, "us": {"amount": 2, "unitShort": ""}}},
                {"name": "basil", "amount": 10, "unit": "g", "measures": {"metric": {"amount": 10, "unitShort": "g"}, "us": {"amount": 0.35, "unitShort": "oz"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Cook pasta."}, {"number": 2, "step": "Sauté tomatoes and basil."}, {"number": 3, "step": "Combine and serve."}
            ]}],
            "scoring": {"overall_score": 20.1, "match_percentage": 40.0},
    },
        {
            "id": 700002,
            "image": "https://img.spoonacular.com/recipes/700002-556x370.jpg",
            "title": "Mexican Chicken Tacos",
            "readyInMinutes": 30,
            "servings": 3,
            "cuisines": ["mexican"],
            "dishTypes": ["main course", "lunch", "dinner"],
            "summary": "Simple tacos with spiced chicken.",
            "extendedIngredients": [
                {"name": "tortillas", "amount": 6, "unit": "", "measures": {"metric": {"amount": 6, "unitShort": ""}, "us": {"amount": 6, "unitShort": ""}}},
                {"name": "chicken breast", "amount": 300, "unit": "g", "measures": {"metric": {"amount": 300, "unitShort": "g"}, "us": {"amount": 10.58, "unitShort": "oz"}}},
                {"name": "lettuce", "amount": 50, "unit": "g", "measures": {"metric": {"amount": 50, "unitShort": "g"}, "us": {"amount": 1.76, "unitShort": "oz"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Cook spiced chicken."}, {"number": 2, "step": "Warm tortillas."}, {"number": 3, "step": "Assemble tacos."}
            ]}],
            "scoring": {"overall_score": 22.0, "match_percentage": 35.0},
    },
        {
            "id": 700003,
            "image": "https://img.spoonacular.com/recipes/700003-556x370.jpg",
            "title": "French Onion Soup",
            "readyInMinutes": 45,
            "servings": 4,
            "cuisines": ["french"],
            "dishTypes": ["soup", "starter", "appetizer"],
            "summary": "Classic onion soup with toasted bread.",
            "extendedIngredients": [
                {"name": "onions", "amount": 4, "unit": "", "measures": {"metric": {"amount": 4, "unitShort": ""}, "us": {"amount": 4, "unitShort": ""}}},
                {"name": "beef broth", "amount": 750, "unit": "ml", "measures": {"metric": {"amount": 750, "unitShort": "ml"}, "us": {"amount": 25.36, "unitShort": "fl oz"}}},
                {"name": "baguette", "amount": 6, "unit": "slices", "measures": {"metric": {"amount": 6, "unitShort": "slices"}, "us": {"amount": 6, "unitShort": "slices"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Caramelize onions."}, {"number": 2, "step": "Add broth and simmer."}, {"number": 3, "step": "Serve with toasted bread."}
            ]}],
            "scoring": {"overall_score": 18.0, "match_percentage": 30.0},
    },
        {
            "id": 700030,
            "image": "https://img.spoonacular.com/recipes/700030-556x370.jpg",
            "title": "Mexican Churro Sundae",
            "readyInMinutes": 25,
            "servings": 2,
            "cuisines": ["mexican", "latin american"],
            "dishTypes": ["dessert"],
            "summary": "Warm churros with ice cream.",
            "extendedIngredients": [
                {"name": "churros", "amount": 6, "unit": "", "measures": {"metric": {"amount": 6, "unitShort": ""}, "us": {"amount": 6, "unitShort": ""}}},
                {"name": "vanilla ice cream", "amount": 2, "unit": "scoops", "measures": {"metric": {"amount": 2, "unitShort": "scoops"}, "us": {"amount": 2, "unitShort": "scoops"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Assemble and serve immediately."}
            ]}],
            "scoring": {"overall_score": 14.2, "match_percentage": 12.0},
    },

        # Additional coverage examples
        {
            "id": 700031,
            "image": "https://img.spoonacular.com/recipes/700031-556x370.jpg",
            "title": "Easy 15 Minute Garlic Shrimp",
            "readyInMinutes": 15,
            "servings": 2,
            "cuisines": ["american"],
            "dishTypes": ["main course", "dinner", "quick"],
            "summary": "Quick and easy garlic shrimp.",
            "extendedIngredients": [
                {"name": "shrimp", "amount": 300, "unit": "g", "measures": {"metric": {"amount": 300, "unitShort": "g"}, "us": {"amount": 10.58, "unitShort": "oz"}}},
                {"name": "garlic", "amount": 3, "unit": "cloves", "measures": {"metric": {"amount": 3, "unitShort": "cloves"}, "us": {"amount": 3, "unitShort": "cloves"}}},
                {"name": "butter", "amount": 30, "unit": "g", "measures": {"metric": {"amount": 30, "unitShort": "g"}, "us": {"amount": 1.06, "unitShort": "oz"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Sauté garlic and shrimp for 2-3 minutes."},
                {"number": 2, "step": "Finish with butter and serve."},
            ]}],
            "scoring": {"overall_score": 18.0, "match_percentage": 22.0},
    },
        {
            "id": 700032,
            "image": "https://img.spoonacular.com/recipes/700032-556x370.jpg",
            "title": "Banana Bread Loaf",
            "readyInMinutes": 60,
            "servings": 8,
            "cuisines": ["american"],
            "dishTypes": ["bread", "snack", "baking"],
            "summary": "Classic moist banana bread.",
            "extendedIngredients": [
                {"name": "bananas", "amount": 3, "unit": "", "measures": {"metric": {"amount": 3, "unitShort": ""}, "us": {"amount": 3, "unitShort": ""}}},
                {"name": "flour", "amount": 250, "unit": "g", "measures": {"metric": {"amount": 250, "unitShort": "g"}, "us": {"amount": 8.82, "unitShort": "oz"}}},
                {"name": "sugar", "amount": 120, "unit": "g", "measures": {"metric": {"amount": 120, "unitShort": "g"}, "us": {"amount": 4.23, "unitShort": "oz"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Mix and bake until done."}
            ]}],
            "scoring": {"overall_score": 15.0, "match_percentage": 18.0},
    },
        {
            "id": 700033,
            "image": "https://img.spoonacular.com/recipes/700033-556x370.jpg",
            "title": "Chocolate Lava Cake Dessert",
            "readyInMinutes": 25,
            "servings": 2,
            "cuisines": ["french"],
            "dishTypes": ["dessert"],
            "summary": "Rich chocolate lava cakes.",
            "extendedIngredients": [
                {"name": "chocolate", "amount": 150, "unit": "g", "measures": {"metric": {"amount": 150, "unitShort": "g"}, "us": {"amount": 5.29, "unitShort": "oz"}}},
                {"name": "butter", "amount": 80, "unit": "g", "measures": {"metric": {"amount": 80, "unitShort": "g"}, "us": {"amount": 2.82, "unitShort": "oz"}}},
                {"name": "eggs", "amount": 2, "unit": "", "measures": {"metric": {"amount": 2, "unitShort": ""}, "us": {"amount": 2, "unitShort": ""}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Bake until edges set and center molten."}
            ]}],
            "scoring": {"overall_score": 16.5, "match_percentage": 20.0},
    },
        {
            "id": 700034,
            "image": "https://img.spoonacular.com/recipes/700034-556x370.jpg",
            "title": "Vegetarian Lentil Bolognese",
            "readyInMinutes": 40,
            "servings": 4,
            "cuisines": ["italian", "vegetarian"],
            "dishTypes": ["main course", "dinner"],
            "summary": "Hearty veggie bolognese with lentils.",
            "extendedIngredients": [
                {"name": "lentils", "amount": 250, "unit": "g", "measures": {"metric": {"amount": 250, "unitShort": "g"}, "us": {"amount": 8.82, "unitShort": "oz"}}},
                {"name": "tomato puree", "amount": 300, "unit": "g", "measures": {"metric": {"amount": 300, "unitShort": "g"}, "us": {"amount": 10.58, "unitShort": "oz"}}},
                {"name": "spaghetti", "amount": 300, "unit": "g", "measures": {"metric": {"amount": 300, "unitShort": "g"}, "us": {"amount": 10.58, "unitShort": "oz"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Simmer sauce and cook pasta."}
            ]}],
            "scoring": {"overall_score": 19.0, "match_percentage": 28.0},
    },
        {
            "id": 700035,
            "image": "https://img.spoonacular.com/recipes/700035-556x370.jpg",
            "title": "Vegan Buddha Bowl",
            "readyInMinutes": 20,
            "servings": 2,
            "cuisines": ["asian", "vegan"],
            "dishTypes": ["salad", "lunch"],
            "summary": "Colorful bowl with grains and veg.",
            "extendedIngredients": [
                {"name": "quinoa", "amount": 150, "unit": "g", "measures": {"metric": {"amount": 150, "unitShort": "g"}, "us": {"amount": 5.29, "unitShort": "oz"}}},
                {"name": "broccoli", "amount": 120, "unit": "g", "measures": {"metric": {"amount": 120, "unitShort": "g"}, "us": {"amount": 4.23, "unitShort": "oz"}}},
                {"name": "avocado", "amount": 1, "unit": "", "measures": {"metric": {"amount": 1, "unitShort": ""}, "us": {"amount": 1, "unitShort": ""}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Assemble cooked grains and toppings."}
            ]}],
            "scoring": {"overall_score": 17.2, "match_percentage": 23.0},
    },
        {
            "id": 700036,
            "image": "https://img.spoonacular.com/recipes/700036-556x370.jpg",
            "title": "Healthy Quinoa Salad",
            "readyInMinutes": 15,
            "servings": 2,
            "cuisines": ["mediterranean"],
            "dishTypes": ["salad", "lunch"],
            "summary": "Light and healthy quinoa salad.",
            "extendedIngredients": [
                {"name": "quinoa", "amount": 150, "unit": "g", "measures": {"metric": {"amount": 150, "unitShort": "g"}, "us": {"amount": 5.29, "unitShort": "oz"}}},
                {"name": "tomatoes", "amount": 2, "unit": "", "measures": {"metric": {"amount": 2, "unitShort": ""}, "us": {"amount": 2, "unitShort": ""}}},
                {"name": "cucumber", "amount": 1, "unit": "", "measures": {"metric": {"amount": 1, "unitShort": ""}, "us": {"amount": 1, "unitShort": ""}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Combine all ingredients and toss."}
            ]}],
            "scoring": {"overall_score": 16.8, "match_percentage": 22.0},
    },
        {
            "id": 700037,
            "image": "https://img.spoonacular.com/recipes/700037-556x370.jpg",
            "title": "30 Minute Waffle Breakfast",
            "readyInMinutes": 30,
            "servings": 2,
            "cuisines": ["american"],
            "dishTypes": ["breakfast", "brunch"],
            "summary": "Crisp waffles in 30 minutes.",
            "extendedIngredients": [
                {"name": "flour", "amount": 200, "unit": "g", "measures": {"metric": {"amount": 200, "unitShort": "g"}, "us": {"amount": 7.05, "unitShort": "oz"}}},
                {"name": "milk", "amount": 250, "unit": "ml", "measures": {"metric": {"amount": 250, "unitShort": "ml"}, "us": {"amount": 8.45, "unitShort": "fl oz"}}},
                {"name": "egg", "amount": 1, "unit": "", "measures": {"metric": {"amount": 1, "unitShort": ""}, "us": {"amount": 1, "unitShort": ""}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Mix batter and cook in waffle iron."}
            ]}],
            "scoring": {"overall_score": 15.9, "match_percentage": 19.0},
    },
        {
            "id": 700038,
            "image": "https://img.spoonacular.com/recipes/700038-556x370.jpg",
            "title": "Muffin Pastry Sampler",
            "readyInMinutes": 35,
            "servings": 6,
            "cuisines": ["american"],
            "dishTypes": ["breakfast", "snack", "bread"],
            "summary": "Assorted muffins and pastries.",
            "extendedIngredients": [
                {"name": "flour", "amount": 300, "unit": "g", "measures": {"metric": {"amount": 300, "unitShort": "g"}, "us": {"amount": 10.58, "unitShort": "oz"}}},
                {"name": "sugar", "amount": 120, "unit": "g", "measures": {"metric": {"amount": 120, "unitShort": "g"}, "us": {"amount": 4.23, "unitShort": "oz"}}},
                {"name": "butter", "amount": 100, "unit": "g", "measures": {"metric": {"amount": 100, "unitShort": "g"}, "us": {"amount": 3.53, "unitShort": "oz"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Prepare batter and bake in tins."}
            ]}],
            "scoring": {"overall_score": 14.8, "match_percentage": 17.0},
        },
        # New: Indian curry (covers 'indian')
        {
            "id": 700039,
            "image": "https://img.spoonacular.com/recipes/700039-556x370.jpg",
            "title": "Indian Chickpea Curry",
            "readyInMinutes": 35,
            "servings": 4,
            "cuisines": ["indian"],
            "dishTypes": ["main course", "dinner"],
            "summary": "A hearty chickpea curry simmered with tomatoes and spices.",
            "extendedIngredients": [
                {"name": "chickpeas", "amount": 400, "unit": "g", "measures": {"metric": {"amount": 400, "unitShort": "g"}}},
                {"name": "tomato puree", "amount": 200, "unit": "g", "measures": {"metric": {"amount": 200, "unitShort": "g"}}},
                {"name": "curry powder", "amount": 2, "unit": "tbsp", "measures": {"metric": {"amount": 2, "unitShort": "tbsp"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Sauté spices, add tomatoes and chickpeas."},
                {"number": 2, "step": "Simmer until thickened and serve with rice."}
            ]}],
            "scoring": {"overall_score": 19.5, "match_percentage": 26.0},
        },
        # New: Asian stir fry (covers 'asian' and 'quick_meals')
        {
            "id": 700040,
            "image": "https://img.spoonacular.com/recipes/700040-556x370.jpg",
            "title": "Quick Veggie Stir Fry",
            "readyInMinutes": 15,
            "servings": 2,
            "cuisines": ["asian"],
            "dishTypes": ["main course", "quick"],
            "summary": "Colorful vegetables stir-fried with a simple sauce.",
            "extendedIngredients": [
                {"name": "broccoli", "amount": 150, "unit": "g", "measures": {"metric": {"amount": 150, "unitShort": "g"}}},
                {"name": "bell pepper", "amount": 1, "unit": "", "measures": {"metric": {"amount": 1, "unitShort": ""}}},
                {"name": "soy sauce", "amount": 2, "unit": "tbsp", "measures": {"metric": {"amount": 2, "unitShort": "tbsp"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Stir-fry vegetables and add sauce."}
            ]}],
            "scoring": {"overall_score": 17.8, "match_percentage": 24.0},
        },
        # New: Greek Salad (covers 'mediterranean' and 'salad')
        {
            "id": 700041,
            "image": "https://img.spoonacular.com/recipes/700041-556x370.jpg",
            "title": "Greek Salad Bowl",
            "readyInMinutes": 10,
            "servings": 2,
            "cuisines": ["greek", "mediterranean"],
            "dishTypes": ["salad", "lunch", "healthy"],
            "summary": "A fresh salad with tomatoes, cucumber, olives, and feta.",
            "extendedIngredients": [
                {"name": "tomatoes", "amount": 2, "unit": "", "measures": {"metric": {"amount": 2, "unitShort": ""}}},
                {"name": "cucumber", "amount": 1, "unit": "", "measures": {"metric": {"amount": 1, "unitShort": ""}}},
                {"name": "feta cheese", "amount": 100, "unit": "g", "measures": {"metric": {"amount": 100, "unitShort": "g"}}},
                {"name": "olives", "amount": 50, "unit": "g", "measures": {"metric": {"amount": 50, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Chop and toss all ingredients with olive oil."}
            ]}],
            "scoring": {"overall_score": 16.0, "match_percentage": 20.0},
        },
        # New: Classic Burger (covers 'american')
        {
            "id": 700042,
            "image": "https://img.spoonacular.com/recipes/700042-556x370.jpg",
            "title": "Classic Beef Burger",
            "readyInMinutes": 20,
            "servings": 2,
            "cuisines": ["american"],
            "dishTypes": ["main course", "dinner"],
            "summary": "Juicy burger with lettuce and tomato.",
            "extendedIngredients": [
                {"name": "ground beef", "amount": 300, "unit": "g", "measures": {"metric": {"amount": 300, "unitShort": "g"}}},
                {"name": "burger buns", "amount": 2, "unit": "", "measures": {"metric": {"amount": 2, "unitShort": ""}}},
                {"name": "lettuce", "amount": 30, "unit": "g", "measures": {"metric": {"amount": 30, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Form patties and grill."},
                {"number": 2, "step": "Assemble with toppings."}
            ]}],
            "scoring": {"overall_score": 18.5, "match_percentage": 25.0},
        },
        # New: Healthy Smoothie (covers 'healthy' and 'breakfast')
        {
            "id": 700043,
            "image": "https://img.spoonacular.com/recipes/700043-556x370.jpg",
            "title": "Healthy Berry Smoothie",
            "readyInMinutes": 5,
            "servings": 1,
            "cuisines": ["american"],
            "dishTypes": ["breakfast", "healthy"],
            "summary": "A light and healthy berry smoothie.",
            "extendedIngredients": [
                {"name": "mixed berries", "amount": 150, "unit": "g", "measures": {"metric": {"amount": 150, "unitShort": "g"}}},
                {"name": "yogurt", "amount": 120, "unit": "g", "measures": {"metric": {"amount": 120, "unitShort": "g"}}},
                {"name": "milk", "amount": 150, "unit": "ml", "measures": {"metric": {"amount": 150, "unitShort": "ml"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Blend until smooth."}
            ]}],
            "scoring": {"overall_score": 12.0, "match_percentage": 15.0},
        },
        # New: Vegan Chili (covers 'vegan' and 'soup')
        {
            "id": 700044,
            "image": "https://img.spoonacular.com/recipes/700044-556x370.jpg",
            "title": "Vegan Bean Chili",
            "readyInMinutes": 40,
            "servings": 4,
            "cuisines": ["american", "vegan"],
            "dishTypes": ["soup", "main course"],
            "summary": "Hearty vegan chili with beans and tomatoes.",
            "extendedIngredients": [
                {"name": "kidney beans", "amount": 400, "unit": "g", "measures": {"metric": {"amount": 400, "unitShort": "g"}}},
                {"name": "tomatoes", "amount": 3, "unit": "", "measures": {"metric": {"amount": 3, "unitShort": ""}}},
                {"name": "onions", "amount": 1, "unit": "", "measures": {"metric": {"amount": 1, "unitShort": ""}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Simmer all ingredients until flavors meld."}
            ]}],
            "scoring": {"overall_score": 17.0, "match_percentage": 22.0},
        },
        # New: Quick Pancakes (covers 'breakfast' and 'baking')
        {
            "id": 700045,
            "image": "https://img.spoonacular.com/recipes/700045-556x370.jpg",
            "title": "Quick Fluffy Pancakes",
            "readyInMinutes": 15,
            "servings": 2,
            "cuisines": ["american"],
            "dishTypes": ["breakfast", "baking", "quick"],
            "summary": "Easy pancakes ready in minutes.",
            "extendedIngredients": [
                {"name": "flour", "amount": 150, "unit": "g", "measures": {"metric": {"amount": 150, "unitShort": "g"}}},
                {"name": "milk", "amount": 200, "unit": "ml", "measures": {"metric": {"amount": 200, "unitShort": "ml"}}},
                {"name": "egg", "amount": 1, "unit": "", "measures": {"metric": {"amount": 1, "unitShort": ""}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Mix batter and cook on skillet."}
            ]}],
            "scoring": {"overall_score": 13.5, "match_percentage": 16.0},
        },
        # Additional mock recipes to expand coverage
        {
            "id": 700046,
            "image": "https://img.spoonacular.com/recipes/700046-556x370.jpg",
            "title": "Caprese Salad with Balsamic",
            "readyInMinutes": 10,
            "servings": 2,
            "cuisines": ["italian", "mediterranean"],
            "dishTypes": ["salad", "appetizer"],
            "summary": "Fresh mozzarella, tomatoes, and basil with balsamic glaze.",
            "extendedIngredients": [
                {"name": "mozzarella", "amount": 125, "unit": "g", "measures": {"metric": {"amount": 125, "unitShort": "g"}}},
                {"name": "tomatoes", "amount": 2, "unit": "", "measures": {"metric": {"amount": 2, "unitShort": ""}}},
                {"name": "basil", "amount": 10, "unit": "g", "measures": {"metric": {"amount": 10, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Slice tomatoes and mozzarella, layer with basil, drizzle glaze."}
            ]}],
            "scoring": {"overall_score": 15.2, "match_percentage": 21.0},
        },
        {
            "id": 700047,
            "image": "https://img.spoonacular.com/recipes/700047-556x370.jpg",
            "title": "Spicy Tofu Stir-Fry",
            "readyInMinutes": 18,
            "servings": 2,
            "cuisines": ["asian", "vegan"],
            "dishTypes": ["main course", "quick"],
            "summary": "Crispy tofu tossed with vegetables and a spicy sauce.",
            "extendedIngredients": [
                {"name": "tofu", "amount": 250, "unit": "g", "measures": {"metric": {"amount": 250, "unitShort": "g"}}},
                {"name": "soy sauce", "amount": 2, "unit": "tbsp", "measures": {"metric": {"amount": 2, "unitShort": "tbsp"}}},
                {"name": "chili sauce", "amount": 1, "unit": "tbsp", "measures": {"metric": {"amount": 1, "unitShort": "tbsp"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Pan-fry tofu, add vegetables and sauces, stir to coat."}
            ]}],
            "scoring": {"overall_score": 17.1, "match_percentage": 23.0},
        },
        {
            "id": 700048,
            "image": "https://img.spoonacular.com/recipes/700048-556x370.jpg",
            "title": "Chicken Caesar Wraps",
            "readyInMinutes": 20,
            "servings": 2,
            "cuisines": ["american"],
            "dishTypes": ["lunch", "main course"],
            "summary": "Grilled chicken tossed with Caesar salad wrapped in tortillas.",
            "extendedIngredients": [
                {"name": "tortillas", "amount": 2, "unit": "", "measures": {"metric": {"amount": 2, "unitShort": ""}}},
                {"name": "chicken breast", "amount": 250, "unit": "g", "measures": {"metric": {"amount": 250, "unitShort": "g"}}},
                {"name": "romaine", "amount": 80, "unit": "g", "measures": {"metric": {"amount": 80, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Grill chicken, toss with lettuce and dressing, wrap."}
            ]}],
            "scoring": {"overall_score": 16.4, "match_percentage": 22.0},
        },
        {
            "id": 700049,
            "image": "https://img.spoonacular.com/recipes/700049-556x370.jpg",
            "title": "Garlic Butter Salmon",
            "readyInMinutes": 15,
            "servings": 2,
            "cuisines": ["american", "mediterranean"],
            "dishTypes": ["main course", "dinner"],
            "summary": "Pan-seared salmon finished with garlic butter and lemon.",
            "extendedIngredients": [
                {"name": "salmon fillet", "amount": 300, "unit": "g", "measures": {"metric": {"amount": 300, "unitShort": "g"}}},
                {"name": "butter", "amount": 30, "unit": "g", "measures": {"metric": {"amount": 30, "unitShort": "g"}}},
                {"name": "garlic", "amount": 2, "unit": "cloves", "measures": {"metric": {"amount": 2, "unitShort": "cloves"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Sear salmon, add garlic butter to finish."}
            ]}],
            "scoring": {"overall_score": 18.9, "match_percentage": 27.0},
        },
        {
            "id": 700050,
            "image": "https://img.spoonacular.com/recipes/700050-556x370.jpg",
            "title": "Mushroom Risotto",
            "readyInMinutes": 35,
            "servings": 3,
            "cuisines": ["italian"],
            "dishTypes": ["main course", "dinner"],
            "summary": "Creamy risotto with sautéed mushrooms and parmesan.",
            "extendedIngredients": [
                {"name": "arborio rice", "amount": 240, "unit": "g", "measures": {"metric": {"amount": 240, "unitShort": "g"}}},
                {"name": "mushrooms", "amount": 200, "unit": "g", "measures": {"metric": {"amount": 200, "unitShort": "g"}}},
                {"name": "parmesan", "amount": 40, "unit": "g", "measures": {"metric": {"amount": 40, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Toast rice, add broth gradually, fold in mushrooms and cheese."}
            ]}],
            "scoring": {"overall_score": 19.3, "match_percentage": 29.0},
        },
        {
            "id": 700051,
            "image": "https://img.spoonacular.com/recipes/700051-556x370.jpg",
            "title": "Thai Green Curry",
            "readyInMinutes": 30,
            "servings": 3,
            "cuisines": ["asian", "thai"],
            "dishTypes": ["main course", "dinner"],
            "summary": "Fragrant coconut curry with vegetables.",
            "extendedIngredients": [
                {"name": "coconut milk", "amount": 400, "unit": "ml", "measures": {"metric": {"amount": 400, "unitShort": "ml"}}},
                {"name": "green curry paste", "amount": 2, "unit": "tbsp", "measures": {"metric": {"amount": 2, "unitShort": "tbsp"}}},
                {"name": "mixed vegetables", "amount": 250, "unit": "g", "measures": {"metric": {"amount": 250, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Simmer coconut milk with curry paste, add vegetables until tender."}
            ]}],
            "scoring": {"overall_score": 18.2, "match_percentage": 24.0},
        },
        {
            "id": 700052,
            "image": "https://img.spoonacular.com/recipes/700052-556x370.jpg",
            "title": "Greek Lemon Chicken Soup",
            "readyInMinutes": 30,
            "servings": 4,
            "cuisines": ["greek", "mediterranean"],
            "dishTypes": ["soup", "starter"],
            "summary": "Light chicken soup with lemon and dill.",
            "extendedIngredients": [
                {"name": "chicken", "amount": 250, "unit": "g", "measures": {"metric": {"amount": 250, "unitShort": "g"}}},
                {"name": "lemon", "amount": 1, "unit": "", "measures": {"metric": {"amount": 1, "unitShort": ""}}},
                {"name": "dill", "amount": 5, "unit": "g", "measures": {"metric": {"amount": 5, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Simmer chicken, finish with lemon and dill."}
            ]}],
            "scoring": {"overall_score": 16.7, "match_percentage": 21.0},
        },
        {
            "id": 700053,
            "image": "https://img.spoonacular.com/recipes/700053-556x370.jpg",
            "title": "Avocado Toast with Egg",
            "readyInMinutes": 8,
            "servings": 1,
            "cuisines": ["american"],
            "dishTypes": ["breakfast", "brunch"],
            "summary": "Smashed avocado on toast topped with a fried egg.",
            "extendedIngredients": [
                {"name": "bread", "amount": 1, "unit": "slice", "measures": {"metric": {"amount": 1, "unitShort": "slice"}}},
                {"name": "avocado", "amount": 0.5, "unit": "", "measures": {"metric": {"amount": 0.5, "unitShort": ""}}},
                {"name": "egg", "amount": 1, "unit": "", "measures": {"metric": {"amount": 1, "unitShort": ""}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Toast bread, smash avocado, top with egg."}
            ]}],
            "scoring": {"overall_score": 12.7, "match_percentage": 14.0},
        },
        {
            "id": 700054,
            "image": "https://img.spoonacular.com/recipes/700054-556x370.jpg",
            "title": "Turkey Chili",
            "readyInMinutes": 35,
            "servings": 4,
            "cuisines": ["american"],
            "dishTypes": ["soup", "main course"],
            "summary": "Lean and hearty chili with ground turkey.",
            "extendedIngredients": [
                {"name": "ground turkey", "amount": 400, "unit": "g", "measures": {"metric": {"amount": 400, "unitShort": "g"}}},
                {"name": "beans", "amount": 400, "unit": "g", "measures": {"metric": {"amount": 400, "unitShort": "g"}}},
                {"name": "tomato sauce", "amount": 300, "unit": "g", "measures": {"metric": {"amount": 300, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Brown turkey, add rest and simmer."}
            ]}],
            "scoring": {"overall_score": 17.4, "match_percentage": 23.0},
        },
        {
            "id": 700055,
            "image": "https://img.spoonacular.com/recipes/700055-556x370.jpg",
            "title": "Pesto Chicken Pasta",
            "readyInMinutes": 22,
            "servings": 2,
            "cuisines": ["italian"],
            "dishTypes": ["main course", "dinner"],
            "summary": "Pasta tossed with pesto and grilled chicken.",
            "extendedIngredients": [
                {"name": "pasta", "amount": 200, "unit": "g", "measures": {"metric": {"amount": 200, "unitShort": "g"}}},
                {"name": "chicken breast", "amount": 200, "unit": "g", "measures": {"metric": {"amount": 200, "unitShort": "g"}}},
                {"name": "pesto", "amount": 3, "unit": "tbsp", "measures": {"metric": {"amount": 3, "unitShort": "tbsp"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Boil pasta, grill chicken, combine with pesto."}
            ]}],
            "scoring": {"overall_score": 18.0, "match_percentage": 25.0},
        },
        {
            "id": 700056,
            "image": "https://img.spoonacular.com/recipes/700056-556x370.jpg",
            "title": "Quiche Lorraine",
            "readyInMinutes": 50,
            "servings": 6,
            "cuisines": ["french"],
            "dishTypes": ["breakfast", "brunch", "baking"],
            "summary": "Classic bacon and cheese quiche.",
            "extendedIngredients": [
                {"name": "eggs", "amount": 4, "unit": "", "measures": {"metric": {"amount": 4, "unitShort": ""}}},
                {"name": "cream", "amount": 200, "unit": "ml", "measures": {"metric": {"amount": 200, "unitShort": "ml"}}},
                {"name": "bacon", "amount": 120, "unit": "g", "measures": {"metric": {"amount": 120, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Blind-bake crust, add filling, bake until set."}
            ]}],
            "scoring": {"overall_score": 16.9, "match_percentage": 21.0},
        },
        {
            "id": 700057,
            "image": "https://img.spoonacular.com/recipes/700057-556x370.jpg",
            "title": "Crispy Baked Falafel",
            "readyInMinutes": 35,
            "servings": 4,
            "cuisines": ["mediterranean", "vegan"],
            "dishTypes": ["main course", "lunch"],
            "summary": "Baked falafel served with tahini sauce.",
            "extendedIngredients": [
                {"name": "chickpeas", "amount": 300, "unit": "g", "measures": {"metric": {"amount": 300, "unitShort": "g"}}},
                {"name": "tahini", "amount": 2, "unit": "tbsp", "measures": {"metric": {"amount": 2, "unitShort": "tbsp"}}},
                {"name": "parsley", "amount": 15, "unit": "g", "measures": {"metric": {"amount": 15, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Blend, form balls, bake until crisp."}
            ]}],
            "scoring": {"overall_score": 17.3, "match_percentage": 24.0},
        },
        {
            "id": 700058,
            "image": "https://img.spoonacular.com/recipes/700058-556x370.jpg",
            "title": "Soba Noodle Salad",
            "readyInMinutes": 15,
            "servings": 2,
            "cuisines": ["asian", "japanese"],
            "dishTypes": ["salad", "lunch", "quick"],
            "summary": "Cold soba with sesame dressing and veggies.",
            "extendedIngredients": [
                {"name": "soba noodles", "amount": 180, "unit": "g", "measures": {"metric": {"amount": 180, "unitShort": "g"}}},
                {"name": "sesame oil", "amount": 1, "unit": "tbsp", "measures": {"metric": {"amount": 1, "unitShort": "tbsp"}}},
                {"name": "cucumber", "amount": 1, "unit": "", "measures": {"metric": {"amount": 1, "unitShort": ""}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Cook noodles, toss with dressing and veggies."}
            ]}],
            "scoring": {"overall_score": 15.6, "match_percentage": 20.0},
        },
        {
            "id": 700059,
            "image": "https://img.spoonacular.com/recipes/700059-556x370.jpg",
            "title": "Roasted Veggie Sheet Pan Dinner",
            "readyInMinutes": 30,
            "servings": 3,
            "cuisines": ["american", "vegetarian"],
            "dishTypes": ["main course", "dinner"],
            "summary": "Assorted vegetables roasted on a sheet pan.",
            "extendedIngredients": [
                {"name": "sweet potato", "amount": 1, "unit": "", "measures": {"metric": {"amount": 1, "unitShort": ""}}},
                {"name": "broccoli", "amount": 150, "unit": "g", "measures": {"metric": {"amount": 150, "unitShort": "g"}}},
                {"name": "olive oil", "amount": 2, "unit": "tbsp", "measures": {"metric": {"amount": 2, "unitShort": "tbsp"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Chop, season, roast until tender."}
            ]}],
            "scoring": {"overall_score": 16.2, "match_percentage": 21.0},
        },
        {
            "id": 700060,
            "image": "https://img.spoonacular.com/recipes/700060-556x370.jpg",
            "title": "Beef and Broccoli",
            "readyInMinutes": 20,
            "servings": 2,
            "cuisines": ["asian", "chinese"],
            "dishTypes": ["main course", "dinner", "quick"],
            "summary": "Classic takeout-style beef and broccoli.",
            "extendedIngredients": [
                {"name": "beef strips", "amount": 250, "unit": "g", "measures": {"metric": {"amount": 250, "unitShort": "g"}}},
                {"name": "broccoli", "amount": 180, "unit": "g", "measures": {"metric": {"amount": 180, "unitShort": "g"}}},
                {"name": "soy sauce", "amount": 2, "unit": "tbsp", "measures": {"metric": {"amount": 2, "unitShort": "tbsp"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Stir-fry beef, add broccoli and sauce; cook until crisp-tender."}
            ]}],
            "scoring": {"overall_score": 18.6, "match_percentage": 26.0},
        },
        {
            "id": 700061,
            "image": "https://img.spoonacular.com/recipes/700061-556x370.jpg",
            "title": "Lemon Herb Roasted Chicken",
            "readyInMinutes": 55,
            "servings": 4,
            "cuisines": ["american", "mediterranean"],
            "dishTypes": ["main course", "dinner"],
            "summary": "Whole chicken roasted with lemon and herbs.",
            "extendedIngredients": [
                {"name": "whole chicken", "amount": 1200, "unit": "g", "measures": {"metric": {"amount": 1200, "unitShort": "g"}}},
                {"name": "lemon", "amount": 1, "unit": "", "measures": {"metric": {"amount": 1, "unitShort": ""}}},
                {"name": "rosemary", "amount": 5, "unit": "g", "measures": {"metric": {"amount": 5, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Season, roast until juices run clear."}
            ]}],
            "scoring": {"overall_score": 19.1, "match_percentage": 27.0},
        },
        {
            "id": 700062,
            "image": "https://img.spoonacular.com/recipes/700062-556x370.jpg",
            "title": "Shrimp Scampi Linguine",
            "readyInMinutes": 20,
            "servings": 2,
            "cuisines": ["italian"],
            "dishTypes": ["main course", "dinner", "quick"],
            "summary": "Garlic butter shrimp over linguine.",
            "extendedIngredients": [
                {"name": "linguine", "amount": 200, "unit": "g", "measures": {"metric": {"amount": 200, "unitShort": "g"}}},
                {"name": "shrimp", "amount": 250, "unit": "g", "measures": {"metric": {"amount": 250, "unitShort": "g"}}},
                {"name": "garlic", "amount": 3, "unit": "cloves", "measures": {"metric": {"amount": 3, "unitShort": "cloves"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Cook pasta, sauté shrimp with garlic and butter, combine."}
            ]}],
            "scoring": {"overall_score": 18.3, "match_percentage": 25.0},
        },
        {
            "id": 700063,
            "image": "https://img.spoonacular.com/recipes/700063-556x370.jpg",
            "title": "Black Bean Quesadillas",
            "readyInMinutes": 12,
            "servings": 2,
            "cuisines": ["mexican"],
            "dishTypes": ["lunch", "main course", "quick"],
            "summary": "Crispy quesadillas filled with black beans and cheese.",
            "extendedIngredients": [
                {"name": "tortillas", "amount": 2, "unit": "", "measures": {"metric": {"amount": 2, "unitShort": ""}}},
                {"name": "black beans", "amount": 150, "unit": "g", "measures": {"metric": {"amount": 150, "unitShort": "g"}}},
                {"name": "cheddar", "amount": 80, "unit": "g", "measures": {"metric": {"amount": 80, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Fill tortillas and toast until cheese melts."}
            ]}],
            "scoring": {"overall_score": 14.9, "match_percentage": 18.0},
        },
        {
            "id": 700064,
            "image": "https://img.spoonacular.com/recipes/700064-556x370.jpg",
            "title": "Teriyaki Chicken Rice Bowl",
            "readyInMinutes": 25,
            "servings": 2,
            "cuisines": ["asian", "japanese"],
            "dishTypes": ["main course", "dinner"],
            "summary": "Glazed chicken over steamed rice with vegetables.",
            "extendedIngredients": [
                {"name": "chicken thigh", "amount": 300, "unit": "g", "measures": {"metric": {"amount": 300, "unitShort": "g"}}},
                {"name": "teriyaki sauce", "amount": 3, "unit": "tbsp", "measures": {"metric": {"amount": 3, "unitShort": "tbsp"}}},
                {"name": "rice", "amount": 250, "unit": "g", "measures": {"metric": {"amount": 250, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Cook rice, pan-glaze chicken, assemble bowl."}
            ]}],
            "scoring": {"overall_score": 17.7, "match_percentage": 23.0},
        },
        {
            "id": 700065,
            "image": "https://img.spoonacular.com/recipes/700065-556x370.jpg",
            "title": "Mediterranean Couscous Salad",
            "readyInMinutes": 15,
            "servings": 2,
            "cuisines": ["mediterranean"],
            "dishTypes": ["salad", "lunch", "healthy"],
            "summary": "Pearl couscous with tomatoes, cucumber, and feta.",
            "extendedIngredients": [
                {"name": "couscous", "amount": 180, "unit": "g", "measures": {"metric": {"amount": 180, "unitShort": "g"}}},
                {"name": "tomatoes", "amount": 2, "unit": "", "measures": {"metric": {"amount": 2, "unitShort": ""}}},
                {"name": "feta", "amount": 80, "unit": "g", "measures": {"metric": {"amount": 80, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Cook couscous, toss with veg and cheese."}
            ]}],
            "scoring": {"overall_score": 16.0, "match_percentage": 20.0},
        },
        {
            "id": 700066,
            "image": "https://img.spoonacular.com/recipes/700066-556x370.jpg",
            "title": "BBQ Pulled Pork Sandwiches",
            "readyInMinutes": 240,
            "servings": 6,
            "cuisines": ["american"],
            "dishTypes": ["main course", "dinner"],
            "summary": "Slow-cooked pulled pork with BBQ sauce.",
            "extendedIngredients": [
                {"name": "pork shoulder", "amount": 1200, "unit": "g", "measures": {"metric": {"amount": 1200, "unitShort": "g"}}},
                {"name": "bbq sauce", "amount": 200, "unit": "g", "measures": {"metric": {"amount": 200, "unitShort": "g"}}},
                {"name": "burger buns", "amount": 6, "unit": "", "measures": {"metric": {"amount": 6, "unitShort": ""}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Slow-cook pork, shred, toss with sauce, serve on buns."}
            ]}],
            "scoring": {"overall_score": 18.8, "match_percentage": 26.0},
        },
        {
            "id": 700067,
            "image": "https://img.spoonacular.com/recipes/700067-556x370.jpg",
            "title": "Baked Ziti",
            "readyInMinutes": 35,
            "servings": 4,
            "cuisines": ["italian"],
            "dishTypes": ["main course", "dinner", "baking"],
            "summary": "Pasta baked with tomato sauce and cheese.",
            "extendedIngredients": [
                {"name": "ziti pasta", "amount": 300, "unit": "g", "measures": {"metric": {"amount": 300, "unitShort": "g"}}},
                {"name": "tomato sauce", "amount": 350, "unit": "g", "measures": {"metric": {"amount": 350, "unitShort": "g"}}},
                {"name": "mozzarella", "amount": 150, "unit": "g", "measures": {"metric": {"amount": 150, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Boil pasta, mix with sauce and cheese, bake until bubbly."}
            ]}],
            "scoring": {"overall_score": 17.0, "match_percentage": 23.0},
        },
        {
            "id": 700068,
            "image": "https://img.spoonacular.com/recipes/700068-556x370.jpg",
            "title": "Spinach and Feta Omelette",
            "readyInMinutes": 12,
            "servings": 1,
            "cuisines": ["greek", "mediterranean"],
            "dishTypes": ["breakfast", "brunch", "quick"],
            "summary": "Fluffy omelette with spinach and feta.",
            "extendedIngredients": [
                {"name": "eggs", "amount": 2, "unit": "", "measures": {"metric": {"amount": 2, "unitShort": ""}}},
                {"name": "spinach", "amount": 50, "unit": "g", "measures": {"metric": {"amount": 50, "unitShort": "g"}}},
                {"name": "feta", "amount": 40, "unit": "g", "measures": {"metric": {"amount": 40, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Cook eggs, add fillings, fold and serve."}
            ]}],
            "scoring": {"overall_score": 13.9, "match_percentage": 16.0},
        },
        {
            "id": 700069,
            "image": "https://img.spoonacular.com/recipes/700069-556x370.jpg",
            "title": "Tom Yum Soup",
            "readyInMinutes": 25,
            "servings": 3,
            "cuisines": ["thai", "asian"],
            "dishTypes": ["soup", "starter"],
            "summary": "Hot and sour Thai soup with shrimp.",
            "extendedIngredients": [
                {"name": "shrimp", "amount": 200, "unit": "g", "measures": {"metric": {"amount": 200, "unitShort": "g"}}},
                {"name": "lemongrass", "amount": 1, "unit": "stalk", "measures": {"metric": {"amount": 1, "unitShort": "stalk"}}},
                {"name": "mushrooms", "amount": 120, "unit": "g", "measures": {"metric": {"amount": 120, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Simmer broth with aromatics, add shrimp and mushrooms."}
            ]}],
            "scoring": {"overall_score": 17.6, "match_percentage": 23.0},
        },
        {
            "id": 700070,
            "image": "https://img.spoonacular.com/recipes/700070-556x370.jpg",
            "title": "Cinnamon Apple Oatmeal",
            "readyInMinutes": 10,
            "servings": 1,
            "cuisines": ["american"],
            "dishTypes": ["breakfast", "healthy"],
            "summary": "Warm oats cooked with apples and cinnamon.",
            "extendedIngredients": [
                {"name": "rolled oats", "amount": 60, "unit": "g", "measures": {"metric": {"amount": 60, "unitShort": "g"}}},
                {"name": "apple", "amount": 0.5, "unit": "", "measures": {"metric": {"amount": 0.5, "unitShort": ""}}},
                {"name": "cinnamon", "amount": 0.5, "unit": "tsp", "measures": {"metric": {"amount": 0.5, "unitShort": "tsp"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Cook oats with milk/water, stir in apple and cinnamon."}
            ]}],
            "scoring": {"overall_score": 12.4, "match_percentage": 14.0},
        },
        {
            "id": 700071,
            "image": "https://img.spoonacular.com/recipes/700071-556x370.jpg",
            "title": "Margherita Pizza Flatbread",
            "readyInMinutes": 15,
            "servings": 2,
            "cuisines": ["italian"],
            "dishTypes": ["main course", "dinner", "quick"],
            "summary": "Flatbread topped with tomato, mozzarella, and basil.",
            "extendedIngredients": [
                {"name": "flatbread", "amount": 2, "unit": "", "measures": {"metric": {"amount": 2, "unitShort": ""}}},
                {"name": "mozzarella", "amount": 120, "unit": "g", "measures": {"metric": {"amount": 120, "unitShort": "g"}}},
                {"name": "tomato sauce", "amount": 120, "unit": "g", "measures": {"metric": {"amount": 120, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Top flatbreads and bake until cheese melts."}
            ]}],
            "scoring": {"overall_score": 16.3, "match_percentage": 21.0},
        },
        {
            "id": 700072,
            "image": "https://img.spoonacular.com/recipes/700072-556x370.jpg",
            "title": "Kale Caesar Salad",
            "readyInMinutes": 10,
            "servings": 2,
            "cuisines": ["american"],
            "dishTypes": ["salad", "lunch", "healthy"],
            "summary": "Kale tossed with Caesar dressing and croutons.",
            "extendedIngredients": [
                {"name": "kale", "amount": 120, "unit": "g", "measures": {"metric": {"amount": 120, "unitShort": "g"}}},
                {"name": "croutons", "amount": 40, "unit": "g", "measures": {"metric": {"amount": 40, "unitShort": "g"}}},
                {"name": "parmesan", "amount": 30, "unit": "g", "measures": {"metric": {"amount": 30, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Massage kale, toss with dressing and toppings."}
            ]}],
            "scoring": {"overall_score": 14.2, "match_percentage": 18.0},
        },
        {
            "id": 700073,
            "image": "https://img.spoonacular.com/recipes/700073-556x370.jpg",
            "title": "Sausage and Peppers",
            "readyInMinutes": 25,
            "servings": 3,
            "cuisines": ["italian", "american"],
            "dishTypes": ["main course", "dinner"],
            "summary": "Sautéed sausage with bell peppers and onions.",
            "extendedIngredients": [
                {"name": "sausage", "amount": 300, "unit": "g", "measures": {"metric": {"amount": 300, "unitShort": "g"}}},
                {"name": "bell peppers", "amount": 2, "unit": "", "measures": {"metric": {"amount": 2, "unitShort": ""}}},
                {"name": "onions", "amount": 1, "unit": "", "measures": {"metric": {"amount": 1, "unitShort": ""}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Brown sausage, add peppers and onions until tender."}
            ]}],
            "scoring": {"overall_score": 17.5, "match_percentage": 23.0},
        },
        {
            "id": 700074,
            "image": "https://img.spoonacular.com/recipes/700074-556x370.jpg",
            "title": "Garlic Naan",
            "readyInMinutes": 45,
            "servings": 4,
            "cuisines": ["indian"],
            "dishTypes": ["bread", "side dish"],
            "summary": "Soft skillet naan brushed with garlic butter.",
            "extendedIngredients": [
                {"name": "flour", "amount": 300, "unit": "g", "measures": {"metric": {"amount": 300, "unitShort": "g"}}},
                {"name": "yogurt", "amount": 120, "unit": "g", "measures": {"metric": {"amount": 120, "unitShort": "g"}}},
                {"name": "yeast", "amount": 1, "unit": "tsp", "measures": {"metric": {"amount": 1, "unitShort": "tsp"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Proof dough, roll, cook on skillet, brush with garlic butter."}
            ]}],
            "scoring": {"overall_score": 15.7, "match_percentage": 19.0},
        },
        {
            "id": 700075,
            "image": "https://img.spoonacular.com/recipes/700075-556x370.jpg",
            "title": "Greek Chicken Gyros",
            "readyInMinutes": 30,
            "servings": 3,
            "cuisines": ["greek", "mediterranean"],
            "dishTypes": ["main course", "lunch"],
            "summary": "Marinated chicken served in pita with tzatziki.",
            "extendedIngredients": [
                {"name": "chicken", "amount": 300, "unit": "g", "measures": {"metric": {"amount": 300, "unitShort": "g"}}},
                {"name": "pita bread", "amount": 3, "unit": "", "measures": {"metric": {"amount": 3, "unitShort": ""}}},
                {"name": "tzatziki", "amount": 120, "unit": "g", "measures": {"metric": {"amount": 120, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Grill chicken, assemble in pita with toppings."}
            ]}],
            "scoring": {"overall_score": 18.1, "match_percentage": 24.0},
        },
        {
            "id": 700076,
            "image": "https://img.spoonacular.com/recipes/700076-556x370.jpg",
            "title": "Pancit Bihon",
            "readyInMinutes": 28,
            "servings": 3,
            "cuisines": ["asian", "filipino"],
            "dishTypes": ["main course", "dinner"],
            "summary": "Filipino rice noodles stir-fried with chicken and vegetables.",
            "extendedIngredients": [
                {"name": "rice noodles", "amount": 200, "unit": "g", "measures": {"metric": {"amount": 200, "unitShort": "g"}}},
                {"name": "chicken", "amount": 200, "unit": "g", "measures": {"metric": {"amount": 200, "unitShort": "g"}}},
                {"name": "cabbage", "amount": 120, "unit": "g", "measures": {"metric": {"amount": 120, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Stir-fry ingredients, hydrate noodles, toss and serve."}
            ]}],
            "scoring": {"overall_score": 17.9, "match_percentage": 24.0},
        },
        {
            "id": 700077,
            "image": "https://img.spoonacular.com/recipes/700077-556x370.jpg",
            "title": "Veggie Frittata",
            "readyInMinutes": 22,
            "servings": 2,
            "cuisines": ["italian", "vegetarian"],
            "dishTypes": ["breakfast", "brunch"],
            "summary": "Oven-baked egg frittata with mixed vegetables.",
            "extendedIngredients": [
                {"name": "eggs", "amount": 4, "unit": "", "measures": {"metric": {"amount": 4, "unitShort": ""}}},
                {"name": "bell pepper", "amount": 1, "unit": "", "measures": {"metric": {"amount": 1, "unitShort": ""}}},
                {"name": "spinach", "amount": 60, "unit": "g", "measures": {"metric": {"amount": 60, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Whisk eggs, add veg, bake until set."}
            ]}],
            "scoring": {"overall_score": 14.5, "match_percentage": 18.0},
        },
        {
            "id": 700078,
            "image": "https://img.spoonacular.com/recipes/700078-556x370.jpg",
            "title": "Burrito Bowl",
            "readyInMinutes": 20,
            "servings": 2,
            "cuisines": ["mexican", "american"],
            "dishTypes": ["main course", "lunch"],
            "summary": "Rice bowl topped with beans, corn, and salsa.",
            "extendedIngredients": [
                {"name": "rice", "amount": 250, "unit": "g", "measures": {"metric": {"amount": 250, "unitShort": "g"}}},
                {"name": "black beans", "amount": 150, "unit": "g", "measures": {"metric": {"amount": 150, "unitShort": "g"}}},
                {"name": "corn", "amount": 100, "unit": "g", "measures": {"metric": {"amount": 100, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Fill bowl with rice and toppings."}
            ]}],
            "scoring": {"overall_score": 15.1, "match_percentage": 19.0},
        },
        {
            "id": 700079,
            "image": "https://img.spoonacular.com/recipes/700079-556x370.jpg",
            "title": "Chicken Noodle Soup",
            "readyInMinutes": 35,
            "servings": 4,
            "cuisines": ["american"],
            "dishTypes": ["soup", "starter"],
            "summary": "Comforting soup with chicken, noodles, and vegetables.",
            "extendedIngredients": [
                {"name": "chicken", "amount": 250, "unit": "g", "measures": {"metric": {"amount": 250, "unitShort": "g"}}},
                {"name": "noodles", "amount": 120, "unit": "g", "measures": {"metric": {"amount": 120, "unitShort": "g"}}},
                {"name": "carrots", "amount": 2, "unit": "", "measures": {"metric": {"amount": 2, "unitShort": ""}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Simmer broth with chicken and veg, add noodles."}
            ]}],
            "scoring": {"overall_score": 16.8, "match_percentage": 21.0},
        },
        {
            "id": 700080,
            "image": "https://img.spoonacular.com/recipes/700080-556x370.jpg",
            "title": "BBQ Chicken Salad",
            "readyInMinutes": 15,
            "servings": 2,
            "cuisines": ["american"],
            "dishTypes": ["salad", "lunch"],
            "summary": "Chopped salad with BBQ chicken and ranch dressing.",
            "extendedIngredients": [
                {"name": "chicken", "amount": 200, "unit": "g", "measures": {"metric": {"amount": 200, "unitShort": "g"}}},
                {"name": "corn", "amount": 80, "unit": "g", "measures": {"metric": {"amount": 80, "unitShort": "g"}}},
                {"name": "romaine", "amount": 100, "unit": "g", "measures": {"metric": {"amount": 100, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Toss all ingredients with dressing."}
            ]}],
            "scoring": {"overall_score": 15.9, "match_percentage": 20.0},
        },
        {
            "id": 700081,
            "image": "https://img.spoonacular.com/recipes/700081-556x370.jpg",
            "title": "Pad Thai",
            "readyInMinutes": 25,
            "servings": 2,
            "cuisines": ["thai", "asian"],
            "dishTypes": ["main course", "dinner"],
            "summary": "Rice noodles stir-fried with tamarind sauce, egg, and peanuts.",
            "extendedIngredients": [
                {"name": "rice noodles", "amount": 200, "unit": "g", "measures": {"metric": {"amount": 200, "unitShort": "g"}}},
                {"name": "egg", "amount": 1, "unit": "", "measures": {"metric": {"amount": 1, "unitShort": ""}}},
                {"name": "peanuts", "amount": 30, "unit": "g", "measures": {"metric": {"amount": 30, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Stir-fry noodles with sauce and add toppings."}
            ]}],
            "scoring": {"overall_score": 18.0, "match_percentage": 24.0},
        },
        {
            "id": 700082,
            "image": "https://img.spoonacular.com/recipes/700082-556x370.jpg",
            "title": "Beet and Goat Cheese Salad",
            "readyInMinutes": 15,
            "servings": 2,
            "cuisines": ["mediterranean"],
            "dishTypes": ["salad", "lunch"],
            "summary": "Roasted beets, creamy goat cheese, and walnuts.",
            "extendedIngredients": [
                {"name": "beets", "amount": 200, "unit": "g", "measures": {"metric": {"amount": 200, "unitShort": "g"}}},
                {"name": "goat cheese", "amount": 60, "unit": "g", "measures": {"metric": {"amount": 60, "unitShort": "g"}}},
                {"name": "walnuts", "amount": 30, "unit": "g", "measures": {"metric": {"amount": 30, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Combine ingredients over greens and dress."}
            ]}],
            "scoring": {"overall_score": 14.7, "match_percentage": 18.0},
        },
        {
            "id": 700083,
            "image": "https://img.spoonacular.com/recipes/700083-556x370.jpg",
            "title": "Tuna Melt Sandwich",
            "readyInMinutes": 10,
            "servings": 1,
            "cuisines": ["american"],
            "dishTypes": ["lunch", "quick"],
            "summary": "Tuna salad grilled with melted cheese on bread.",
            "extendedIngredients": [
                {"name": "tuna", "amount": 120, "unit": "g", "measures": {"metric": {"amount": 120, "unitShort": "g"}}},
                {"name": "bread", "amount": 2, "unit": "slices", "measures": {"metric": {"amount": 2, "unitShort": "slices"}}},
                {"name": "cheese", "amount": 40, "unit": "g", "measures": {"metric": {"amount": 40, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Assemble sandwich and grill until cheese melts."}
            ]}],
            "scoring": {"overall_score": 13.8, "match_percentage": 16.0},
        },
        {
            "id": 700084,
            "image": "https://img.spoonacular.com/recipes/700084-556x370.jpg",
            "title": "Mango Sticky Rice",
            "readyInMinutes": 30,
            "servings": 2,
            "cuisines": ["thai", "asian"],
            "dishTypes": ["dessert"],
            "summary": "Sweet coconut sticky rice with ripe mango.",
            "extendedIngredients": [
                {"name": "glutinous rice", "amount": 150, "unit": "g", "measures": {"metric": {"amount": 150, "unitShort": "g"}}},
                {"name": "coconut milk", "amount": 200, "unit": "ml", "measures": {"metric": {"amount": 200, "unitShort": "ml"}}},
                {"name": "mango", "amount": 1, "unit": "", "measures": {"metric": {"amount": 1, "unitShort": ""}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Cook sticky rice, sweeten coconut milk, serve with mango."}
            ]}],
            "scoring": {"overall_score": 15.3, "match_percentage": 19.0},
        },
        {
            "id": 700085,
            "image": "https://img.spoonacular.com/recipes/700085-556x370.jpg",
            "title": "Stuffed Bell Peppers",
            "readyInMinutes": 40,
            "servings": 4,
            "cuisines": ["american"],
            "dishTypes": ["main course", "dinner", "baking"],
            "summary": "Bell peppers stuffed with rice and meat, baked with cheese.",
            "extendedIngredients": [
                {"name": "bell peppers", "amount": 4, "unit": "", "measures": {"metric": {"amount": 4, "unitShort": ""}}},
                {"name": "ground beef", "amount": 300, "unit": "g", "measures": {"metric": {"amount": 300, "unitShort": "g"}}},
                {"name": "rice", "amount": 200, "unit": "g", "measures": {"metric": {"amount": 200, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Stuff peppers and bake until tender."}
            ]}],
            "scoring": {"overall_score": 17.2, "match_percentage": 23.0},
        },
        {
            "id": 700086,
            "image": "https://img.spoonacular.com/recipes/700086-556x370.jpg",
            "title": "Cajun Shrimp Tacos",
            "readyInMinutes": 18,
            "servings": 2,
            "cuisines": ["mexican", "american"],
            "dishTypes": ["main course", "lunch", "quick"],
            "summary": "Spicy shrimp tacos with lime slaw.",
            "extendedIngredients": [
                {"name": "shrimp", "amount": 250, "unit": "g", "measures": {"metric": {"amount": 250, "unitShort": "g"}}},
                {"name": "tortillas", "amount": 4, "unit": "", "measures": {"metric": {"amount": 4, "unitShort": ""}}},
                {"name": "cabbage", "amount": 100, "unit": "g", "measures": {"metric": {"amount": 100, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Sauté spiced shrimp, assemble tacos with slaw."}
            ]}],
            "scoring": {"overall_score": 17.8, "match_percentage": 24.0},
        },
        {
            "id": 700087,
            "image": "https://img.spoonacular.com/recipes/700087-556x370.jpg",
            "title": "Creamy Tomato Soup",
            "readyInMinutes": 25,
            "servings": 3,
            "cuisines": ["american", "italian"],
            "dishTypes": ["soup", "starter"],
            "summary": "Smooth tomato soup finished with cream.",
            "extendedIngredients": [
                {"name": "tomatoes", "amount": 600, "unit": "g", "measures": {"metric": {"amount": 600, "unitShort": "g"}}},
                {"name": "cream", "amount": 100, "unit": "ml", "measures": {"metric": {"amount": 100, "unitShort": "ml"}}},
                {"name": "onion", "amount": 1, "unit": "", "measures": {"metric": {"amount": 1, "unitShort": ""}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Simmer tomatoes and aromatics, blend and finish with cream."}
            ]}],
            "scoring": {"overall_score": 16.1, "match_percentage": 20.0},
        },
        {
            "id": 700088,
            "image": "https://img.spoonacular.com/recipes/700088-556x370.jpg",
            "title": "Veggie Sushi Rolls",
            "readyInMinutes": 40,
            "servings": 3,
            "cuisines": ["japanese", "asian"],
            "dishTypes": ["main course", "lunch"],
            "summary": "Simple maki rolls with cucumber, avocado, and carrot.",
            "extendedIngredients": [
                {"name": "sushi rice", "amount": 250, "unit": "g", "measures": {"metric": {"amount": 250, "unitShort": "g"}}},
                {"name": "nori", "amount": 4, "unit": "sheets", "measures": {"metric": {"amount": 4, "unitShort": "sheets"}}},
                {"name": "avocado", "amount": 1, "unit": "", "measures": {"metric": {"amount": 1, "unitShort": ""}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Spread rice on nori, add fillings, roll and slice."}
            ]}],
            "scoring": {"overall_score": 16.4, "match_percentage": 21.0},
        },
        {
            "id": 700089,
            "image": "https://img.spoonacular.com/recipes/700089-556x370.jpg",
            "title": "Eggplant Parmesan",
            "readyInMinutes": 45,
            "servings": 4,
            "cuisines": ["italian"],
            "dishTypes": ["main course", "dinner", "baking"],
            "summary": "Breaded eggplant layered with sauce and cheese.",
            "extendedIngredients": [
                {"name": "eggplant", "amount": 1, "unit": "", "measures": {"metric": {"amount": 1, "unitShort": ""}}},
                {"name": "tomato sauce", "amount": 400, "unit": "g", "measures": {"metric": {"amount": 400, "unitShort": "g"}}},
                {"name": "mozzarella", "amount": 200, "unit": "g", "measures": {"metric": {"amount": 200, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Bake breaded slices, layer with sauce and cheese, bake."}
            ]}],
            "scoring": {"overall_score": 17.1, "match_percentage": 23.0},
        },
        {
            "id": 700090,
            "image": "https://img.spoonacular.com/recipes/700090-556x370.jpg",
            "title": "Shakshuka",
            "readyInMinutes": 25,
            "servings": 2,
            "cuisines": ["middle eastern", "mediterranean"],
            "dishTypes": ["breakfast", "brunch", "main course"],
            "summary": "Eggs poached in spiced tomato sauce.",
            "extendedIngredients": [
                {"name": "eggs", "amount": 3, "unit": "", "measures": {"metric": {"amount": 3, "unitShort": ""}}},
                {"name": "tomatoes", "amount": 400, "unit": "g", "measures": {"metric": {"amount": 400, "unitShort": "g"}}},
                {"name": "bell pepper", "amount": 1, "unit": "", "measures": {"metric": {"amount": 1, "unitShort": ""}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Simmer sauce, make wells, crack eggs, cook until set."}
            ]}],
            "scoring": {"overall_score": 16.6, "match_percentage": 21.0},
        },
        {
            "id": 700091,
            "image": "https://img.spoonacular.com/recipes/700091-556x370.jpg",
            "title": "Fried Rice",
            "readyInMinutes": 15,
            "servings": 2,
            "cuisines": ["asian", "chinese"],
            "dishTypes": ["main course", "lunch", "quick"],
            "summary": "Day-old rice stir-fried with vegetables and egg.",
            "extendedIngredients": [
                {"name": "cooked rice", "amount": 300, "unit": "g", "measures": {"metric": {"amount": 300, "unitShort": "g"}}},
                {"name": "peas", "amount": 60, "unit": "g", "measures": {"metric": {"amount": 60, "unitShort": "g"}}},
                {"name": "egg", "amount": 1, "unit": "", "measures": {"metric": {"amount": 1, "unitShort": ""}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Stir-fry aromatics, add rice and veg, scramble in egg."}
            ]}],
            "scoring": {"overall_score": 15.8, "match_percentage": 19.0},
        },
        {
            "id": 700092,
            "image": "https://img.spoonacular.com/recipes/700092-556x370.jpg",
            "title": "Chili Garlic Ramen",
            "readyInMinutes": 12,
            "servings": 1,
            "cuisines": ["asian", "japanese"],
            "dishTypes": ["main course", "quick"],
            "summary": "Instant ramen elevated with chili garlic oil and egg.",
            "extendedIngredients": [
                {"name": "ramen noodles", "amount": 1, "unit": "pack", "measures": {"metric": {"amount": 1, "unitShort": "pack"}}},
                {"name": "garlic", "amount": 2, "unit": "cloves", "measures": {"metric": {"amount": 2, "unitShort": "cloves"}}},
                {"name": "egg", "amount": 1, "unit": "", "measures": {"metric": {"amount": 1, "unitShort": ""}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Cook ramen, stir in chili garlic oil, top with egg."}
            ]}],
            "scoring": {"overall_score": 13.7, "match_percentage": 16.0},
        },
        {
            "id": 700093,
            "image": "https://img.spoonacular.com/recipes/700093-556x370.jpg",
            "title": "Poke Bowl",
            "readyInMinutes": 15,
            "servings": 2,
            "cuisines": ["hawaiian", "asian"],
            "dishTypes": ["main course", "lunch"],
            "summary": "Sushi rice bowl topped with marinated fish and veggies.",
            "extendedIngredients": [
                {"name": "sushi rice", "amount": 250, "unit": "g", "measures": {"metric": {"amount": 250, "unitShort": "g"}}},
                {"name": "salmon", "amount": 200, "unit": "g", "measures": {"metric": {"amount": 200, "unitShort": "g"}}},
                {"name": "soy sauce", "amount": 2, "unit": "tbsp", "measures": {"metric": {"amount": 2, "unitShort": "tbsp"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Marinate fish, assemble bowl with rice and toppings."}
            ]}],
            "scoring": {"overall_score": 17.0, "match_percentage": 22.0},
        },
        {
            "id": 700094,
            "image": "https://img.spoonacular.com/recipes/700094-556x370.jpg",
            "title": "Chicken Alfredo",
            "readyInMinutes": 25,
            "servings": 2,
            "cuisines": ["italian", "american"],
            "dishTypes": ["main course", "dinner"],
            "summary": "Creamy fettuccine Alfredo with grilled chicken.",
            "extendedIngredients": [
                {"name": "fettuccine", "amount": 200, "unit": "g", "measures": {"metric": {"amount": 200, "unitShort": "g"}}},
                {"name": "chicken", "amount": 200, "unit": "g", "measures": {"metric": {"amount": 200, "unitShort": "g"}}},
                {"name": "cream", "amount": 200, "unit": "ml", "measures": {"metric": {"amount": 200, "unitShort": "ml"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Cook pasta, make Alfredo sauce, slice chicken, combine."}
            ]}],
            "scoring": {"overall_score": 18.4, "match_percentage": 26.0},
        },
        {
            "id": 700095,
            "image": "https://img.spoonacular.com/recipes/700095-556x370.jpg",
            "title": "Blueberry Pancakes",
            "readyInMinutes": 15,
            "servings": 2,
            "cuisines": ["american"],
            "dishTypes": ["breakfast", "baking", "quick"],
            "summary": "Fluffy pancakes with fresh blueberries.",
            "extendedIngredients": [
                {"name": "flour", "amount": 160, "unit": "g", "measures": {"metric": {"amount": 160, "unitShort": "g"}}},
                {"name": "milk", "amount": 220, "unit": "ml", "measures": {"metric": {"amount": 220, "unitShort": "ml"}}},
                {"name": "blueberries", "amount": 100, "unit": "g", "measures": {"metric": {"amount": 100, "unitShort": "g"}}},
            ],
            "analyzedInstructions": [{"steps": [
                {"number": 1, "step": "Prepare batter, fold in berries, cook on skillet."}
            ]}],
            "scoring": {"overall_score": 14.9, "match_percentage": 18.0},
        },
    ]

def _classify(recipe: Dict) -> List[str]:
    """Classify recipe using the same CMAB categorization as live data."""
    tags = [
        *[str(x) for x in recipe.get("dishTypes", [])],
        *[str(x) for x in recipe.get("cuisines", [])],
    ]
    return RecipeCategory.classify_recipe(str(recipe.get("title", "")), tags)


def find_mock_recipes_by_ingredients(ingredients: List[str], limit: int, ranking: int = 2) -> List[Dict]:
    """Find mock recipes that best match provided ingredients using fuzzy matching.

    Mimics Spoonacular's behavior roughly:
    - tokenizes and singularizes names, ignores common stopwords/units
    - computes usedIngredientCount and missedIngredientCount-like metrics
    - ranking=1 maximizes used ingredients; ranking=2 minimizes missed ingredients
    """
    if not ingredients:
        return []

    # --- lightweight fuzzy matcher (aligned with backend scorer) ---
    _STOPWORDS: Set[str] = {
        "of","and","a","the","fresh","pcs","piece","pieces","unit","units",
        "can","cans","bottle","bottles","pack","package","pkg","slices","slice","clove","cloves","tbsp","tsp","cup","cups"
    }

    def _normalize(s: str) -> str:
        return (s or "").strip().lower()

    def _strip_punct(s: str) -> str:
        import re
        return re.sub(r"[\"'`,.~!@#$%^&*()_+={}\[\\\\\]\\|:;<>/?]", " ", s)

    def _collapse_ws(s: str) -> str:
        import re
        return re.sub(r"\s+", " ", s).strip()

    def _singular(w: str) -> str:
        if not w:
            return w
        if w.endswith("oes") and len(w) > 3:
            return w[:-3]
        if w.endswith("ies") and len(w) > 3:
            return w[:-3] + "y"
        if any(w.endswith(suf) for suf in ["ches","shes","xes","zes","ses"]) and len(w) > 4:
            return w[:-2]
        if w.endswith("s") and not w.endswith("ss") and len(w) > 1:
            return w[:-1]
        return w

    def tokenize(name: str) -> List[str]:
        n = _collapse_ws(_strip_punct(_normalize(name)))
        out: List[str] = []
        for tok in n.split(" "):
            if not tok or tok in _STOPWORDS:
                continue
            out.append(_singular(tok))
        return out

    def jaccard(a: Set[str], b: Set[str]) -> float:
        if not a or not b:
            return 0.0
        inter = len(a & b)
        return inter / (len(a) + len(b) - inter)

    qnames = [str(n or "").strip() for n in ingredients if str(n or "").strip()]
    qtokens_list = [set(tokenize(n)) for n in qnames]
    if not qtokens_list:
        return []

    scored: List[Tuple[int, int, float, Dict]] = []  # (missed, used, avg_score, recipe)
    for r in get_mock_recommendations_raw():
        try:
            ing_names = [str(ing.get("name", "")).strip() for ing in (r.get("extendedIngredients") or [])]
            if not ing_names:
                continue
            used = 0
            scores: List[float] = []
            for iname in ing_names:
                itok = set(tokenize(iname))
                if not itok:
                    continue
                # Check best overlap against any query ingredient tokens
                best = 0.0
                subset_hit = False
                for qtok in qtokens_list:
                    if not qtok:
                        continue
                    score = jaccard(itok, qtok)
                    if score > best:
                        best = score
                    if itok.issubset(qtok) or qtok.issubset(itok):
                        subset_hit = True
                if best >= 0.34 or subset_hit:
                    used += 1
                    scores.append(best if best > 0 else (1.0 if subset_hit else 0.0))
            missed = max(0, len(ing_names) - used)
            avg_score = sum(scores) / len(scores) if scores else 0.0
            # Only include recipes with at least one fuzzy hit
            if used > 0:
                scored.append((missed, used, avg_score, r))
        except Exception:
            continue

    if not scored:
        return []

    # Apply ranking similar to Spoonacular
    if ranking == 1:
        # maximize used ingredients, break ties by fewer missed, then avg score desc
        scored.sort(key=lambda t: (t[1], -t[0], t[2]), reverse=True)
    else:
        # default and ranking=2: minimize missed ingredients, break ties by used desc, then avg score desc
        scored.sort(key=lambda t: (-t[0], t[1], t[2]), reverse=True)

    # Deduplicate by id while preserving order and respect limit
    out: List[Dict] = []
    seen_ids: Set[int] = set()
    for _, _, _, rec in scored:
        rid = rec.get("id")
        if rid in seen_ids:
            continue
        seen_ids.add(rid)
        out.append(rec)
        if len(out) >= max(1, int(limit) or 1):
            break
    return out


def pick_mock_recommendations_by_category(category: Optional[str], limit: int) -> List[Dict]:
    """Return up to limit mock recipes filtered by category, with sensible fallback.

    The category is matched against any classified tag for the recipe. If empty
    or 'general', we return the first N.
    """
    all_recipes = get_mock_recommendations_raw()
    c = (category or "").strip().lower()
    if not c or c == "general":
        return all_recipes[: max(1, int(limit) or 3)]
    filtered = [r for r in all_recipes if c in _classify(r)]
    if not filtered:
        filtered = all_recipes
    return filtered[: max(1, int(limit) or 3)]
