"use client";

import { useMemo, useState } from "react";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { InventoryItem, InventoryFormItem } from "@/lib/types";
import { addDays, differenceInDays, differenceInHours, format } from "date-fns";
import { getExpiryInfo } from "@/lib/expiry";
import { Badge } from "../ui/badge";
import { PlusCircle, Trash2, Edit, Info } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { addInventoryItem, deleteInventoryItem, updateInventoryItem, getExpiredInventory } from "@/app/actions";
import { useAuth } from "@/lib/auth";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface InventoryDialogProps {
  children: React.ReactNode;
  inventory: InventoryFormItem[];
  onUpdateInventory: (inventory: InventoryFormItem[]) => void;
}

export default function InventoryDialog({
  children,
  inventory,
  onUpdateInventory,
}: InventoryDialogProps) {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<string>("current");
  const [editingItem, setEditingItem] = useState<InventoryFormItem | null>(null);
  const [newItem, setNewItem] = useState({
    name: "",
    quantity: "",
    unit: "",
    purchaseDate: format(new Date(), "yyyy-MM-dd"),
    shelfLife: "",
  });
  const [customUnit, setCustomUnit] = useState("");

  const universalUnits = [
    { value: "pcs", label: "pcs" },
    { value: "piece", label: "piece" },
    { value: "bunch", label: "bunch" },
    { value: "clove", label: "clove" },
    { value: "slice", label: "slice" },
    { value: "can", label: "can" },
    { value: "jar", label: "jar" },
  ];
  const metricUnits = [
    { value: "ml", label: "ml" },
    { value: "l", label: "l" },
    { value: "g", label: "g" },
    { value: "kg", label: "kg" },
  ];
  const usUnits = [
    { value: "tsp", label: "tsp" },
    { value: "tbsp", label: "tbsp" },
    { value: "cup", label: "cup" },
    { value: "fl oz", label: "fl oz" },
    { value: "pint", label: "pint" },
    { value: "quart", label: "quart" },
    { value: "gallon", label: "gallon" },
    { value: "oz", label: "oz" },
    { value: "lb", label: "lb" },
  ];
  const availableUnits = [
    ...metricUnits,
    ...usUnits,
    ...universalUnits,
  ];

  // Expired items state
  const [expiredItems, setExpiredItems] = useState<InventoryItem[]>([]);
  const [loadingExpired, setLoadingExpired] = useState(false);

  const loadExpired = async () => {
    if (!user?.id) return;
    setLoadingExpired(true);
    try {
      const list = await getExpiredInventory(user.id);
      setExpiredItems(Array.isArray(list) ? list : []);
    } catch (e) {
      setExpiredItems([]);
    } finally {
      setLoadingExpired(false);
    }
  };

  // When dialog opens or when switching to the expired tab, load expired items
  // Also reload after deletions handled below
  

  // Compute if there are changes while editing to disable Update button when unchanged
  const isEditing = !!editingItem;
  const noChanges = useMemo(() => {
    if (!editingItem) return false;
    const baselinePurchaseDate = format(new Date(editingItem.purchaseDate), "yyyy-MM-dd");
    const baselineShelfLife = Math.max(
      0,
      differenceInDays(new Date(editingItem.expiryDate), new Date(editingItem.purchaseDate))
    );
    const formShelfLife = parseInt(newItem.shelfLife || "0", 10);
    const formQuantity = parseFloat(newItem.quantity || "0");
    return (
      newItem.name.trim() === editingItem.name &&
      formQuantity === editingItem.quantity &&
      newItem.unit.trim() === editingItem.unit &&
      newItem.purchaseDate === baselinePurchaseDate &&
      formShelfLife === baselineShelfLife
    );
  }, [editingItem, newItem]);

  const handleSaveItem = async () => {
    if (
      !newItem.name ||
      !newItem.quantity ||
      !newItem.unit ||
      !newItem.purchaseDate
    ) {
      alert("Please fill required fields.");
      return;
    }

    try {
      const purchaseDate = new Date(newItem.purchaseDate);
      // If shelfLife not provided while editing, preserve existing shelf life based on current item
      const derivedShelfLife = editingItem
        ? (newItem.shelfLife
            ? parseInt(newItem.shelfLife, 10)
            : differenceInDays(new Date(editingItem.expiryDate), new Date(editingItem.purchaseDate)))
        : parseInt(newItem.shelfLife, 10);
      const shelfLife = isNaN(derivedShelfLife as any) ? 0 : derivedShelfLife;
  const expiryDate = addDays(purchaseDate, shelfLife);
  // Normalize to end-of-day like backend create does
  const expiryEOD = new Date(expiryDate);
  expiryEOD.setHours(23, 59, 59, 999);

      if (!user) throw new Error('User not authenticated');
      const userId = user.id;
      
      const effectiveUnit = newItem.unit === "__custom" ? customUnit.trim() : newItem.unit;
      if (editingItem) {
        // Update existing item via API, including expiry_date
        const updatedItem = await updateInventoryItem(userId, editingItem.id, {
          item_name: newItem.name,
          quantity: parseFloat(newItem.quantity),
          unit: effectiveUnit,
          // Send ISO string; backend (Pydantic) will parse to datetime
          expiry_date: expiryEOD.toISOString(),
        });

        const updatedInventory = inventory.map(item =>
          item.id === editingItem.id
            ? {
                ...item,
                name: updatedItem.item_name,
                quantity: updatedItem.quantity,
                unit: updatedItem.unit,
                // Prefer API response; fallback to computed value
                expiryDate: updatedItem.expiry_date || expiryEOD.toISOString(),
                // Keep purchaseDate as chosen in the form for consistency
                purchaseDate: newItem.purchaseDate,
                shelfLife: shelfLife,
              }
            : item
        );
        onUpdateInventory(updatedInventory);
      } else {
        // Add new item
        const apiItem = await addInventoryItem(userId, {
          item_name: newItem.name,
          quantity: parseFloat(newItem.quantity),
          unit: effectiveUnit,
          purchase_date: newItem.purchaseDate,
          shelf_life_days: newItem.shelfLife ? parseInt(newItem.shelfLife) : undefined
        });

        const newItemData: InventoryFormItem = {
          id: apiItem.id,
          name: apiItem.item_name,
          quantity: apiItem.quantity,
          unit: apiItem.unit,
          purchaseDate: purchaseDate.toISOString(),
          expiryDate: apiItem.expiry_date,
          shelfLife,
        };
        
        onUpdateInventory([...inventory, newItemData]);
      }
      setNewItem({
        name: "",
        quantity: "",
        unit: "",
        purchaseDate: format(new Date(), "yyyy-MM-dd"),
        shelfLife: "",
      });
      setCustomUnit("");
      setEditingItem(null);
    } catch (error) {
      console.error('Failed to save inventory item:', error);
      alert('Failed to save item. Please try again.');
    }
  };

  const handleRemoveItem = async (id: string) => {
    try {
      if (!user) throw new Error('User not authenticated');
      const userId = user.id;
      await deleteInventoryItem(userId, id);
      onUpdateInventory(inventory.filter((item) => item.id !== id));
    } catch (error) {
      console.error('Failed to delete inventory item:', error);
      alert('Failed to delete item. Please try again.');
    }
  };

  const getExpiryBadge = (expiryDate: string) => {
    const { text, severity } = getExpiryInfo(expiryDate);
    if (severity === "expired") return <Badge variant="destructive">{text}</Badge>;
    if (severity === "urgent") return <Badge variant="destructive">{text}</Badge>;
    if (severity === "soon") return <Badge variant="secondary" className="bg-accent text-accent-foreground">{text}</Badge>;
    return <Badge variant="outline">{text}</Badge>;
  };

  return (
    <Dialog open={open} onOpenChange={(v) => {
      setOpen(v);
      if (v) {
        // Load expired list on open so it's ready if user clicks the tab
        loadExpired();
      }
    }}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="max-w-4xl">
        <DialogHeader>
          <DialogTitle className="font-headline">Manage Inventory</DialogTitle>
          <DialogDescription>
            Add, edit, or remove items from your pantry.
          </DialogDescription>
        </DialogHeader>
  <div className="grid md:grid-cols-3 gap-8 py-4">
          <div className="md:col-span-1 space-y-4">
            <h3 className="font-semibold font-headline">{editingItem ? 'Edit Item' : 'Add New Item'}</h3>
            <div className="space-y-2">
              <Label htmlFor="name">Item Name</Label>
              <Input
                id="name"
                value={newItem.name}
                onChange={(e) => setNewItem({ ...newItem, name: e.target.value })}
                placeholder="e.g., Tomatoes"
              />
            </div>
              <div className="grid grid-cols-2 gap-2">
              <div className="space-y-2">
                <Label htmlFor="quantity">Quantity</Label>
                <Input
                  id="quantity"
                  type="number"
                  value={newItem.quantity}
                  onChange={(e) =>
                    setNewItem({ ...newItem, quantity: e.target.value })
                  }
                  placeholder="e.g., 5"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="unit">Unit</Label>
                  <div className="space-y-2">
                    <Select
                      value={newItem.unit || ""}
                      onValueChange={(val) => {
                        if (val === "__custom") {
                          setNewItem({ ...newItem, unit: "__custom" });
                          if (!customUnit) setCustomUnit("");
                        } else {
                          setNewItem({ ...newItem, unit: val });
                        }
                      }}
                    >
                      <SelectTrigger id="unit">
                        <SelectValue placeholder="Select unit" />
                      </SelectTrigger>
                      <SelectContent className="max-h-48 overflow-y-auto">
                        {availableUnits.map((u) => (
                          <SelectItem key={u.value} value={u.value}>{u.label}</SelectItem>
                        ))}
                        <SelectItem value="__custom">Custom…</SelectItem>
                      </SelectContent>
                    </Select>
                    {newItem.unit === "__custom" && (
                      <Input
                        id="customUnit"
                        placeholder="Enter custom unit"
                        value={customUnit}
                        onChange={(e) => setCustomUnit(e.target.value)}
                      />
                    )}
                  </div>
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="purchaseDate">Purchase Date</Label>
              <Input
                id="purchaseDate"
                type="date"
                value={newItem.purchaseDate}
                onChange={(e) =>
                  setNewItem({ ...newItem, purchaseDate: e.target.value })
                }
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Label htmlFor="shelfLife">Shelf Life (days) - Optional</Label>
                <TooltipProvider delayDuration={0}>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        aria-label="Shelf life auto-calculation info"
                        className="text-muted-foreground hover:text-foreground"
                      >
                        <Info className="h-4 w-4" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent className="max-w-xs">
                      <p>
                        Leave blank to auto-calculate using
                        {" "}
                        <a
                          href="https://catalog.data.gov/dataset/fsis-foodkeeper-data"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="underline"
                        >
                          FSIS/USDA FoodKeeper
                        </a>
                        {" "}guidance based on the item name.
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
              <Input
                id="shelfLife"
                type="number"
                value={newItem.shelfLife}
                onChange={(e) =>
                  setNewItem({ ...newItem, shelfLife: e.target.value })
                }
                placeholder="Auto-calculated if empty"
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={handleSaveItem} className="flex-1" disabled={isEditing && noChanges}>
                {editingItem ? (
                  <><Edit className="mr-2 h-4 w-4" /> Update Item</>
                ) : (
                  <><PlusCircle className="mr-2 h-4 w-4" /> Add Item</>
                )}
              </Button>
              {editingItem && (
                <Button
                  onClick={() => {
                    setEditingItem(null);
                    setNewItem({
                      name: "",
                      quantity: "",
                      unit: "",
                      purchaseDate: format(new Date(), "yyyy-MM-dd"),
                      shelfLife: "",
                    });
                  }}
                  variant="outline"
                >
                  Cancel
                </Button>
              )}
            </div>
          </div>
          <div className="md:col-span-2">
            <Tabs value={activeTab} onValueChange={(v) => {
              setActiveTab(v);
              if (v === 'expired') loadExpired();
            }}>
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold font-headline">Inventory</h3>
                <TabsList>
                  <TabsTrigger value="current">Current</TabsTrigger>
                  <TabsTrigger value="expired">Expired</TabsTrigger>
                </TabsList>
              </div>

              <TabsContent value="current">
                <div className="border rounded-lg max-h-96 overflow-auto">
                  <Table>
                    <TableHeader className="sticky top-0 bg-muted/50">
                      <TableRow>
                        <TableHead>Item</TableHead>
                        <TableHead>Quantity</TableHead>
                        <TableHead>Expiry</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {inventory.filter((item) => {
                        // Hide expired items from current tab
                        const d = new Date(item.expiryDate);
                        return !isNaN(d.getTime()) && differenceInDays(d, new Date()) >= 0;
                      }).map((item) => (
                        <TableRow key={item.id}>
                          <TableCell className="font-medium">{item.name}</TableCell>
                          <TableCell>
                            {item.quantity} {item.unit}
                          </TableCell>
                          <TableCell>{getExpiryBadge(item.expiryDate)}</TableCell>
                          <TableCell className="text-right">
                            <div className="flex gap-1 justify-end">
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => {
                                  setEditingItem(item);
                                  // Prefill purchaseDate from item and compute shelf life from existing dates
                                  const purchaseDateISO = item.purchaseDate ? new Date(item.purchaseDate) : new Date();
                                  const expiryDateISO = item.expiryDate ? new Date(item.expiryDate) : addDays(purchaseDateISO, 0);
                                  const currentShelfLife = Math.max(
                                    0,
                                    differenceInDays(expiryDateISO, purchaseDateISO)
                                  );
                                  // If item unit isn't in options, switch to custom and seed value
                                  const unitInList = [...availableUnits.map(u => u.value)].includes(item.unit);
                                  setNewItem({
                                    name: item.name,
                                    quantity: item.quantity.toString(),
                                    unit: unitInList ? item.unit : "__custom",
                                    purchaseDate: format(purchaseDateISO, "yyyy-MM-dd"),
                                    shelfLife: String(currentShelfLife),
                                  });
                                  if (!unitInList) setCustomUnit(item.unit);
                                }}
                              >
                                <Edit className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleRemoveItem(item.id)}
                              >
                                <Trash2 className="h-4 w-4 text-destructive" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </TabsContent>

              <TabsContent value="expired">
                <div className="border rounded-lg max-h-96 overflow-auto">
                  {loadingExpired ? (
                    <div className="p-4 text-sm text-muted-foreground">Loading expired…</div>
                  ) : expiredItems.length === 0 ? (
                    <div className="p-4 text-sm text-muted-foreground">No expired items.</div>
                  ) : (
                    <Table>
                      <TableHeader className="sticky top-0 bg-muted/50">
                        <TableRow>
                          <TableHead>Item</TableHead>
                          <TableHead>Quantity</TableHead>
                          <TableHead>Expired</TableHead>
                          <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {expiredItems.map((item) => (
                          <TableRow key={item.id}>
                            <TableCell className="font-medium">{item.item_name}</TableCell>
                            <TableCell>
                              {item.quantity} {item.unit}
                            </TableCell>
                            <TableCell>
                              {/* Always destructive badge since in this tab all are expired */}
                              <Badge variant="destructive">Expired on {new Date(item.expiry_date as any).toLocaleDateString()}</Badge>
                            </TableCell>
                            <TableCell className="text-right">
                              <div className="flex gap-1 justify-end">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={async () => {
                                    if (!user?.id) return;
                                    await deleteInventoryItem(user.id, item.id);
                                    await loadExpired();
                                  }}
                                >
                                  <Trash2 className="h-4 w-4 text-destructive" />
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </div>
                {expiredItems.length > 0 && (
                  <div className="mt-3 flex justify-end">
                    <Button
                      variant="destructive"
                      onClick={async () => {
                        if (!user?.id) return;
                        for (const it of expiredItems) {
                          try { await deleteInventoryItem(user.id, it.id); } catch {}
                        }
                        await loadExpired();
                      }}
                    >
                      Delete All Expired
                    </Button>
                  </div>
                )}
              </TabsContent>
            </Tabs>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
