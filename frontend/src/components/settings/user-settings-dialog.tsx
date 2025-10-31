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
import { Input } from "@/components/ui/input";
import { Button as UIButton } from "@/components/ui/button";
import type { UserSettings } from "@/lib/types";

interface UserSettingsDialogProps {
  children: React.ReactNode;
  settings: UserSettings;
  onUpdateSettings: (settings: UserSettings) => void;
}

export default function UserSettingsDialog({
  children,
  settings,
  onUpdateSettings,
}: UserSettingsDialogProps) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState(settings?.name || "");
  const [email, setEmail] = useState(settings?.email || "");

  // Sync fields when dialog opens or when settings prop changes (e.g., after logout/login)
  useEffect(() => {
    if (!open) return;
    setName(settings?.name || "");
    setEmail(settings?.email || "");
  }, [open, settings]);

  const handleSave = async () => {
    const newSettings: UserSettings = {
      ...settings,
      name,
      email,
    };
    
    try {
      const { updateUserSettings } = await import('@/app/actions');
      await updateUserSettings(settings.userId, newSettings);
      onUpdateSettings(newSettings);
      setOpen(false);
    } catch (error) {
      console.error('Failed to save settings:', error);
      alert('Failed to save settings. Please try again.');
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="font-headline">Account Settings</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              placeholder="Your name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="your.email@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          {/* Measurement system preference removed as requested */}
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