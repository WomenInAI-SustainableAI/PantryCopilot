"""
Recipe Scoring Service
Scores recipes based on inventory match, expiring ingredients, and user preferences
"""
from typing import List, Dict, Tuple, Set
from datetime import datetime, timedelta, date, timezone
from src.db.models import InventoryItem, Allergy

# --- Tunable scoring constants ---
# When a recipe has a high inventory match, give it a small explicit boost so
# near-cookable items consistently float to the top.
HIGH_MATCH_THRESHOLD = 80.0  # percent
HIGH_MATCH_BONUS = 5.0       # score points

# --- Fuzzy token-based ingredient matching helpers (ported from frontend) ---
_STOPWORDS: Set[str] = {
    "of","and","a","the","fresh","pcs","piece","pieces","unit","units",
    "can","cans","bottle","bottles","pack","package","pkg"
}

def _normalize(s: str) -> str:
    return (s or "").lower()

def _strip_punct(s: str) -> str:
    import re
    return re.sub(r"[\"'`,.~!@#$%^&*()_+={}\[\]\\|:;<>/?]", ' ', s)

def _collapse_ws(s: str) -> str:
    import re
    return re.sub(r'\s+', ' ', s).strip()

def _singular(w: str) -> str:
    if not w: return w
    if w.endswith('oes') and len(w) > 3: # tomatoes, potatoes
        return w[:-3]
    if w.endswith('ies') and len(w) > 3:
        return w[:-3] + 'y'
    if any(w.endswith(suf) for suf in ['ches','shes','xes','zes','ses']) and len(w) > 4:
        return w[:-2]
    if w.endswith('s') and not w.endswith('ss') and len(w) > 1:
        return w[:-1]
    return w

def tokenize(name: str) -> List[str]:
    n = _collapse_ws(_strip_punct(_normalize(name)))
    raw = [t for t in n.split(' ') if t]
    out: List[str] = []
    for tok in raw:
        if tok in _STOPWORDS:
            continue
        out.append(_singular(tok))
    return out

def jaccard(a: Set[str], b: Set[str]) -> float:
    if not a or not b: return 0.0
    inter = len(a & b)
    return inter / (len(a) + len(b) - inter)

def ingredient_matches_inventory(ingredient: str, inventory_names: List[str]) -> Tuple[bool, List[str]]:
    """Return (matched?, contributing inventory names) using token fuzzy match."""
    ing_tokens = set(tokenize(ingredient))
    if not ing_tokens:
        return False, []
    contributing: List[str] = []
    best_score = 0.0
    for inv in inventory_names:
        inv_tokens = set(tokenize(inv))
        if not inv_tokens:
            continue
        score = jaccard(ing_tokens, inv_tokens)
        # Accept if reasonable overlap (>= 0.34) or one side subset
        subset = ing_tokens.issubset(inv_tokens) or inv_tokens.issubset(ing_tokens)
        if score >= 0.34 or subset:
            contributing.append(inv)
            best_score = max(best_score, score)
    return len(contributing) > 0, contributing


def calculate_inventory_match_percentage(
    recipe_ingredients: List[str],
    user_inventory: List[InventoryItem]
) -> Tuple[float, List[str], List[str]]:
    """Fuzzy token inventory match percentage (mirrors frontend matching)."""
    if not recipe_ingredients:
        return 0.0, [], []
    inventory_names = [item.item_name for item in user_inventory]
    matched: List[str] = []
    missing: List[str] = []
    for ing in recipe_ingredients:
        ok, contributors = ingredient_matches_inventory(ing, inventory_names)
        if ok:
            matched.append(ing)
        else:
            missing.append(ing)
    match_percentage = (len(matched) / len(recipe_ingredients)) * 100.0
    return match_percentage, matched, missing


def calculate_expiry_urgency_score(
    recipe_ingredients: List[str],
    user_inventory: List[InventoryItem]
) -> Tuple[float, List[str]]:
    """
    Calculate urgency score based on expiring ingredients used in recipe.
    
    Args:
        recipe_ingredients: List of ingredient names from recipe
        user_inventory: User's inventory items
        
    Returns:
        Tuple of (urgency_score, expiring_ingredients_list)
    """
    # Always use UTC on the server
    today = datetime.now(timezone.utc)
    expiring_ingredients = []
    urgency_score = 0.0
    
    def _norm_dt(dt):
        if isinstance(dt, date) and not isinstance(dt, datetime):
            return datetime.combine(dt, datetime.min.time(), tzinfo=timezone.utc)
        if isinstance(dt, datetime):
            if getattr(dt, 'tzinfo', None) is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        return None

    inv_names = [it.item_name for it in user_inventory]
    for ingredient in recipe_ingredients:
        matched, contributors = ingredient_matches_inventory(ingredient, inv_names)
        if not matched:
            continue
        candidate_days: List[int] = []
        matched_names: List[str] = []
        for item in user_inventory:
            if item.item_name in contributors:
                expiry_dt = _norm_dt(item.expiry_date)
                if expiry_dt is not None:
                    candidate_days.append((expiry_dt - today).days)
                    matched_names.append(item.item_name)

        if not candidate_days:
            continue

        # Use the earliest expiry among matches for urgency scoring
        min_days = min(candidate_days)
        # Record unique names that are within urgency window
        if min_days <= 3:
            # Add unique item names
            for n in matched_names:
                if n not in expiring_ingredients:
                    expiring_ingredients.append(n)
            if min_days <= 0:
                urgency_score += 10
            elif min_days == 1:
                urgency_score += 8
            elif min_days == 2:
                urgency_score += 5
            else:
                urgency_score += 3
    
    return urgency_score, expiring_ingredients


def check_allergen_safety(
    recipe_ingredients: List[str],
    user_allergies: List[Allergy]
) -> Tuple[bool, List[str]]:
    """
    Check if recipe is safe based on user allergies.
    
    Args:
        recipe_ingredients: List of ingredient names from recipe
        user_allergies: User's allergies
        
    Returns:
        Tuple of (is_safe, allergens_found)
    """
    allergen_names = [str(allergy.allergen or "").strip().lower() for allergy in user_allergies]

    # Expand basic variants (singular/plural) and common synonyms for broader coverage
    synonyms = {
        # Category-style already handled upstream, but include here for safety
        "dairy": [
            "milk","cheese","butter","yogurt","cream","whey","casein","caseinate","ghee","curd","paneer","kefir","ricotta","mozzarella","parmesan","cheddar","buttermilk","custard","lactose"
        ],
        "nuts": [
            "almond","walnut","pecan","cashew","hazelnut","pistachio","macadamia","brazil nut","pine nut","nut","nuts"
        ],
        "tree nut": [
            "almond","walnut","pecan","cashew","hazelnut","pistachio","macadamia","brazil nut","pine nut","nut","nuts"
        ],
        "treenut": [
            "almond","walnut","pecan","cashew","hazelnut","pistachio","macadamia","brazil nut","pine nut","nut","nuts"
        ],
        "shellfish": ["shrimp","prawn","crab","lobster","crayfish","krill","shellfish"],
        "fish": ["fish","salmon","tuna","cod","haddock","tilapia","trout","anchovy","sardine","mackerel","bass"],
        "gluten": ["gluten","wheat","barley","rye","malt","semolina","farina","spelt","einkorn","emmer"],
        "wheat": ["wheat","semolina","spelt","einkorn","emmer","farina"],
        "soy": ["soy","soya","soybean","soybeans","soymilk","soy sauce","edamame","tofu","miso","tempeh"],
        "sesame": ["sesame","tahini","sesame oil","sesame seed","sesame seeds"],
        "mustard": ["mustard","mustard seed","mustard seeds","mustard powder"],
        "celery": ["celery","celeriac"],
        "lupin": ["lupin","lupine","lupine flour"],
        "sulfite": ["sulfite","sulfites","sulphite","sulphites","sulfur dioxide","e220","e221","e222","e223","e224","e225","e226","e227","e228"],
        "egg": ["egg","eggs","albumen"],
        # Broad bean/legume coverage for users who specify "beans"
        "beans": [
            "bean","beans","legume","legumes","chickpea","chickpeas","garbanzo","garbanzo beans","lentil","lentils",
            "kidney bean","kidney beans","black bean","black beans","pinto bean","pinto beans","cannellini","cannellini beans",
            "navy bean","navy beans","red bean","red beans","mung bean","mung beans","fava bean","fava beans","broad bean","broad beans",
            "pea","peas","split pea","split peas","edamame","soybean","soybeans"
        ],
    }

    expanded_allergens: set[str] = set()
    for a in allergen_names:
        if not a:
            continue
        expanded_allergens.add(a)
        # singular/plural variants
        if a.endswith("s") and len(a) > 1:
            expanded_allergens.add(a[:-1])
        else:
            expanded_allergens.add(a + "s")
        # synonyms
        if a in synonyms:
            for s in synonyms[a]:
                s = s.strip().lower()
                if s:
                    expanded_allergens.add(s)

    allergens_found: List[str] = []
    for ingredient in recipe_ingredients:
        ingredient_lower = str(ingredient or "").lower()
        if not ingredient_lower:
            continue
        for allergen in expanded_allergens:
            if allergen and allergen in ingredient_lower:
                allergens_found.append(allergen)
                # No break: capture multiple hits for debugging/telemetry

    is_safe = len(allergens_found) == 0
    return is_safe, allergens_found


def calculate_partial_usage_score(
    recipe_ingredients: Dict[str, float],
    user_inventory: List[InventoryItem]
) -> float:
    """
    Calculate score based on how well recipe uses partial quantities.
    Higher score for recipes that use up partial ingredients.
    
    Args:
        recipe_ingredients: Dictionary of ingredient names to quantities
        user_inventory: User's inventory items
        
    Returns:
        Partial usage score (0-10)
    """
    usage_score = 0.0
    matches = 0
    
    inv_names = [it.item_name for it in user_inventory]
    for ingredient_name, required_qty in recipe_ingredients.items():
        matched, contributors = ingredient_matches_inventory(ingredient_name, inv_names)
        if not matched:
            continue
        # Pick the first contributing inventory item for usage ratio approximation
        inv_item = next((it for it in user_inventory if it.item_name in contributors), None)
        if not inv_item:
            continue
        matches += 1
        usage_ratio = required_qty / inv_item.quantity if inv_item.quantity > 0 else 0
        if 0.5 <= usage_ratio <= 1.0:
            usage_score += 3
        elif 0.3 <= usage_ratio < 0.5:
            usage_score += 2
        elif usage_ratio < 0.3:
            usage_score += 1
    
    # Normalize to 0-10 scale
    if matches > 0:
        usage_score = min(10, (usage_score / matches) * 3)
    
    return usage_score


def calculate_overall_recipe_score(
    match_percentage: float,
    urgency_score: float,
    is_safe: bool,
    partial_usage_score: float,
    user_feedback_score: float = 0.0
) -> float:
    """
    Calculate overall recipe recommendation score.
    
    Args:
        match_percentage: Inventory match percentage (0-100)
        urgency_score: Expiry urgency score
        is_safe: Whether recipe is allergen-safe
        partial_usage_score: Partial usage score (0-10)
        user_feedback_score: Historical feedback score (-10 to +10)
        
    Returns:
        Overall score (0-100)
    """
    # Base score from inventory match (40% weight)
    score = match_percentage * 0.4
    
    # Urgency bonus (30% weight, capped at 30 points)
    score += min(30, urgency_score * 1.5)
    
    # Partial usage bonus (15% weight)
    score += partial_usage_score * 1.5
    
    # Feedback bonus/penalty (15% weight)
    score += user_feedback_score * 1.5
    
    # Safety penalty - heavily penalize unsafe recipes
    if not is_safe:
        score = score * 0.1  # 90% penalty for allergens
    
    # High-match explicit bonus
    if match_percentage >= HIGH_MATCH_THRESHOLD:
        score += HIGH_MATCH_BONUS

    # Cap at 100
    return min(100, max(0, score))


def rank_recipes(
    recipes: List[Dict],
    user_inventory: List[InventoryItem],
    user_allergies: List[Allergy],
    feedback_scores: Dict[str, float] = None
) -> List[Dict]:
    """
    Rank recipes based on all scoring factors.
    
    Args:
        recipes: List of recipe dictionaries
        user_inventory: User's inventory items
        user_allergies: User's allergies
        feedback_scores: Dictionary of recipe_id to feedback score
        
    Returns:
        Sorted list of recipes with scores
    """
    if feedback_scores is None:
        feedback_scores = {}
    
    scored_recipes = []
    
    for recipe in recipes:
        recipe_ingredients = recipe.get("ingredients", [])
        recipe_id = str(recipe.get("id", ""))
        
        # Calculate all scores
        match_pct, matched, missing = calculate_inventory_match_percentage(
            recipe_ingredients,
            user_inventory
        )
        
        urgency_score, expiring = calculate_expiry_urgency_score(
            recipe_ingredients,
            user_inventory
        )
        
        is_safe, allergens = check_allergen_safety(
            recipe_ingredients,
            user_allergies
        )
        
        # For partial usage, we'd need ingredient quantities from Spoonacular
        # Using a simplified version here
        partial_score = 5.0  # Default mid-range score
        
        feedback_score = feedback_scores.get(recipe_id, 0.0)
        
        overall_score = calculate_overall_recipe_score(
            match_pct,
            urgency_score,
            is_safe,
            partial_score,
            feedback_score
        )
        
        # Add scoring metadata to recipe
        recipe["scoring"] = {
            "overall_score": overall_score,
            "match_percentage": match_pct,
            "matched_ingredients": matched,
            "missing_ingredients": missing,
            "urgency_score": urgency_score,
            "expiring_ingredients": expiring,
            "is_allergen_safe": is_safe,
            "allergens_found": allergens,
            "partial_usage_score": partial_score,
            "feedback_score": feedback_score
        }
        
        scored_recipes.append(recipe)
    
    # Cold-start heuristic: if at least one recipe has a positive match, demote 0% matches
    try:
        any_positive_match = any((r.get("scoring", {}).get("match_percentage", 0.0) or 0.0) > 0 for r in scored_recipes)
        if any_positive_match:
            for r in scored_recipes:
                sc = r.get("scoring", {})
                if (sc.get("match_percentage", 0.0) or 0.0) == 0:
                    # apply a small penalty to move 0% matches below matched items
                    sc["overall_score"] = max(0.0, sc.get("overall_score", 0.0) - 5.0)
    except Exception:
        pass

    # Sort by overall score (descending); tie-breaker: higher match percentage first
    scored_recipes.sort(key=lambda x: (x["scoring"]["overall_score"], x["scoring"].get("match_percentage", 0.0)), reverse=True)
    
    return scored_recipes
