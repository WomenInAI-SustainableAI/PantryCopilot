"use client";

import { CircleUser } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { useAuth } from "@/lib/auth";
import UserSettingsDialog from "@/components/settings/user-settings-dialog";
import type { UserSettings } from "@/lib/types";

interface HeaderProps {
  settings?: UserSettings;
  onUpdateSettings?: (settings: UserSettings) => void;
}

export default function Header({ settings, onUpdateSettings }: HeaderProps) {
  const { user, logout } = useAuth();

  const defaultSettings: UserSettings = {
    userId: user?.id || '',
    name: user?.name || '',
    email: user?.email || '',
  };

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-4 border-b bg-background px-4 sm:static sm:h-auto sm:border-0 sm:bg-transparent sm:px-6">
      <SidebarTrigger className="md:hidden" />

      <div className="flex w-full items-center justify-end">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="outline"
              size="icon"
              className="overflow-hidden rounded-full"
            >
              <CircleUser className="h-5 w-5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>{user?.name || 'My Account'}</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {settings && onUpdateSettings ? (
              <UserSettingsDialog
                settings={settings}
                onUpdateSettings={onUpdateSettings}
              >
                <DropdownMenuItem onSelect={(e) => e.preventDefault()}>
                  Settings
                </DropdownMenuItem>
              </UserSettingsDialog>
            ) : (
              <UserSettingsDialog
                settings={defaultSettings}
                onUpdateSettings={() => {}}
              >
                <DropdownMenuItem onSelect={(e) => e.preventDefault()}>
                  Settings
                </DropdownMenuItem>
              </UserSettingsDialog>
            )}
            <DropdownMenuItem>Support</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={logout}>Logout</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
