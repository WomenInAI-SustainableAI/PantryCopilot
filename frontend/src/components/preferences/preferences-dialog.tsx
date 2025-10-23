"use client";

import { useState } from "react";
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
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { UserPreferences } from "@/lib/types";

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

  const [allergies, setAllergies] = useState(preferences.allergies.join(", "));
  const [dislikes, setDislikes] = useState(preferences.dislikes.join(", "));
  const [dietaryRestrictions, setDietaryRestrictions] = useState(preferences.dietaryRestrictions?.join(", ") || "");
  const [cookingSkillLevel, setCookingSkillLevel] = useState(preferences.cookingSkillLevel || "beginner");
  const [preferredCuisines, setPreferredCuisines] = useState(preferences.preferredCuisines?.join(", ") || "");

  const handleSave = async () => {
    const newPreferences: UserPreferences = {
      ...preferences,
      allergies: allergies.split(",").map((s) => s.trim().toLowerCase()).filter(Boolean),
      dislikes: dislikes.split(",").map((s) => s.trim().toLowerCase()).filter(Boolean),
      dietaryRestrictions: dietaryRestrictions.split(",").map((s) => s.trim().toLowerCase()).filter(Boolean),
      cookingSkillLevel: cookingSkillLevel as 'beginner' | 'intermediate' | 'advanced',
      preferredCuisines: preferredCuisines.split(",").map((s) => s.trim().toLowerCase()).filter(Boolean),
    };
    
    try {
      const { updateUserPreferences } = await import('@/app/actions');
      await updateUserPreferences(preferences.userId, newPreferences);
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
        <Tabs defaultValue="cooking" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="cooking">Cooking</TabsTrigger>
            <TabsTrigger value="dietary">Dietary</TabsTrigger>
          </TabsList>
          
          <TabsContent value="cooking" className="space-y-4">
            <div className="grid gap-2">
              <Label htmlFor="skill-level">Cooking Skill Level</Label>
              <Select value={cookingSkillLevel} onValueChange={setCookingSkillLevel}>
                <SelectTrigger>
                  <SelectValue placeholder="Select your skill level" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="beginner">Beginner</SelectItem>
                  <SelectItem value="intermediate">Intermediate</SelectItem>
                  <SelectItem value="advanced">Advanced</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="cuisines">Preferred Cuisines</Label>
              <Textarea
                id="cuisines"
                placeholder="e.g., Italian, Asian, Mexican"
                value={preferredCuisines}
                onChange={(e) => setPreferredCuisines(e.target.value)}
              />
            </div>
          </TabsContent>
          
          <TabsContent value="dietary" className="space-y-4">
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
              <Label htmlFor="dislikes">Dislikes</Label>
              <Textarea
                id="dislikes"
                placeholder="e.g., cilantro, olives"
                value={dislikes}
                onChange={(e) => setDislikes(e.target.value)}
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
          </TabsContent>
        </Tabs>
        
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
