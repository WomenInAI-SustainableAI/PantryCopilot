# **App Name**: PantryPilot

## Core Features:

- Inventory Management: Users can input their inventory items with name and quantity, with expiry automatically calculated using the input quantity. Firestore database will store the expiry date.
- Recipe Integration: Integrate with Spoonacular API to fetch relevant recipes based on user's inventory.
- Recipe Scoring: Score recipes based on the percentage of ingredients matched in the user's inventory and prioritize recipes using expiring ingredients.
- Preference Filtering: Filter recipes based on user specified allergies and dislikes.
- Explanation Engine: Provide a mini explanation of each recommended recipe including urgency (based on expiry dates), safety (based on allergies), and potential money saving impact.
- Recommendation Learning Tool: The tool continuously improves the suggestions using reinforcement learning based on user feedback for better recommendations over time.

## Style Guidelines:

- Primary color: Vibrant orange (#FF8C00) to evoke a sense of warmth and appetite, reflecting the culinary nature of the app. This is not teal.
- Background color: Soft beige (#F5F5DC), a desaturated hue of orange that offers a neutral and calming backdrop.
- Accent color: Mustard yellow (#E4BA4A) provides a complementary accent, ensuring that calls to action and important information stand out.
- Font pairing: 'Poppins' (sans-serif) for headlines, providing a geometric and modern feel, combined with 'PT Sans' (sans-serif) for body text, offering a clean and readable experience.
- Use food-related and clear icons, such as vegetables, cooking utensils, and expiry clock, to enhance user experience.
- Intuitive and clean layout to ensure that the user can easily navigate the app and quickly find the information they need.
- Subtle transitions and animations when displaying new recipes and updating inventory, creating a seamless user experience.