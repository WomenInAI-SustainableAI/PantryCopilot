"use client";

import Link from "next/link";
import {
  Home,
  Settings,
  Package,
  UtensilsCrossed,
  LifeBuoy,
} from "lucide-react";

import {
  SidebarHeader,
  SidebarContent as MainContent,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarFooter,
} from "@/components/ui/sidebar";
import Logo from "../icons/logo";
import InventoryDialog from "../inventory/inventory-dialog";
import PreferencesDialog from "../preferences/preferences-dialog";
import type { InventoryFormItem, UserPreferences } from "@/lib/types";

interface SidebarContentProps {
  inventory: InventoryFormItem[];
  onUpdateInventory: (inventory: InventoryFormItem[]) => void;
  preferences: UserPreferences;
  onUpdatePreferences: (preferences: UserPreferences) => void;
}

export default function SidebarContent({
  inventory,
  onUpdateInventory,
  preferences,
  onUpdatePreferences,
}: SidebarContentProps) {
  return (
    <>
      <SidebarHeader className="border-b">
        <div className="flex items-center gap-2">
          <Logo className="w-8 h-8 text-primary" />
          <h1 className="font-headline text-2xl font-bold text-primary">
            PantryPilot
          </h1>
        </div>
      </SidebarHeader>
      <MainContent>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild isActive>
              <Link href="/">
              <Home />
              <span>Dashboard</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <InventoryDialog
              inventory={inventory}
              onUpdateInventory={onUpdateInventory}
            >
              <SidebarMenuButton>
                <Package />
                <span>Inventory</span>
              </SidebarMenuButton>
            </InventoryDialog>
          </SidebarMenuItem>
          <SidebarMenuItem>
             <PreferencesDialog preferences={preferences} onUpdatePreferences={onUpdatePreferences}>
              <SidebarMenuButton>
                <Settings />
                <span>Preferences</span>
              </SidebarMenuButton>
            </PreferencesDialog>
          </SidebarMenuItem>
        </SidebarMenu>
      </MainContent>
      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild>
              <Link href="#">
              <LifeBuoy />
              <span>Support</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </>
  );
}
