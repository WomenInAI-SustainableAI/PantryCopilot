"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
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

  const handleSave = () => {
    const newPreferences: UserPreferences = {
      ...preferences,
      allergies: allergies.split(",").map((s) => s.trim().toLowerCase()).filter(Boolean),
      dislikes: dislikes.split(",").map((s) => s.trim().toLowerCase()).filter(Boolean),
    };
    onUpdatePreferences(newPreferences);
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="font-headline">Dietary Preferences</DialogTitle>
          <DialogDescription>
            Help us tailor recommendations for you. Enter items separated by commas.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
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
