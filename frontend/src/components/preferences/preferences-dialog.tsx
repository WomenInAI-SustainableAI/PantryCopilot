"use client";

import { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
 
import type { UserPreferences } from "@/lib/types";
import { useAuth } from "@/lib/auth";

interface PreferencesDialogProps {
  children: React.ReactNode;
  preferences: UserPreferences;
  onUpdatePreferences: (preferences: UserPreferences) => void;
}

export default function PreferencesDialog({
  children,
  preferences,
  onUpdatePreferences,
}: PreferencesDialogProps) {
  const [open, setOpen] = useState(false);
  const { user } = useAuth();

  // Local editable fields; initialize safely to avoid undefined errors
  const [allergies, setAllergies] = useState((preferences.allergies || []).join(", "));
  const [dislikes, setDislikes] = useState((preferences.dislikes || []).join(", "));
  const [dietaryRestrictions, setDietaryRestrictions] = useState((preferences.dietaryRestrictions || []).join(", ") || "");
  const [preferredCuisines, setPreferredCuisines] = useState((preferences.preferredCuisines || []).join(", ") || "");

  // Keep dialog fields in sync when dialog opens or when preferences prop changes between users
  useEffect(() => {
    if (!open) return;
    setAllergies((preferences.allergies || []).join(", "));
    setDislikes((preferences.dislikes || []).join(", "));
    setDietaryRestrictions((preferences.dietaryRestrictions || []).join(", ") || "");
    setPreferredCuisines((preferences.preferredCuisines || []).join(", ") || "");
  }, [open, preferences]);

  const handleSave = async () => {
    const newPreferences: UserPreferences = {
      ...preferences,
      userId: user?.id || preferences.userId,
      allergies: allergies.split(",").map((s) => s.trim().toLowerCase()).filter(Boolean),
      dislikes: dislikes.split(",").map((s) => s.trim().toLowerCase()).filter(Boolean),
      dietaryRestrictions: dietaryRestrictions.split(",").map((s) => s.trim().toLowerCase()).filter(Boolean),
      preferredCuisines: preferredCuisines.split(",").map((s) => s.trim().toLowerCase()).filter(Boolean),
    };
    
    try {
      const { updateUserPreferences } = await import('@/app/actions');
      await updateUserPreferences(user?.id || preferences.userId, newPreferences);
      onUpdatePreferences(newPreferences);
      setOpen(false);
    } catch (error) {
      console.error('Failed to save preferences:', error);
      alert('Failed to save preferences. Please try again.');
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="font-headline">Cooking Preferences</DialogTitle>
        </DialogHeader>
        <div className="w-full space-y-4">
          <div className="grid gap-2">
            <Label htmlFor="cuisines">Preferred Cuisines</Label>
            <Textarea
              id="cuisines"
              placeholder="e.g., Italian, Asian, Mexican"
              value={preferredCuisines}
              onChange={(e) => setPreferredCuisines(e.target.value)}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="allergies">Allergies</Label>
            <Textarea
              id="allergies"
              placeholder="e.g., peanuts, shellfish"
              value={allergies}
              onChange={(e) => setAllergies(e.target.value)}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="dietary-restrictions">Dietary Restrictions</Label>
            <Textarea
              id="dietary-restrictions"
              placeholder="e.g., vegetarian, vegan, gluten-free"
              value={dietaryRestrictions}
              onChange={(e) => setDietaryRestrictions(e.target.value)}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="dislikes">Dislikes</Label>
            <Textarea
              id="dislikes"
              placeholder="e.g., cilantro, olives"
              value={dislikes}
              onChange={(e) => setDislikes(e.target.value)}
            />
          </div>
        </div>
        
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave}>Save Changes</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
