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
import { addInventoryItem, deleteInventoryItem, updateInventoryItem, getExpiredInventory, bulkConsumeInventory, getInventory } from "@/app/actions";
import { AlertDialog, AlertDialogAction, AlertDialogContent, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
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
  const [bulkOpen, setBulkOpen] = useState(false);
  const [bulkRows, setBulkRows] = useState<Array<{ name: string; quantity: string; unit: string }>>([
    { name: "", quantity: "", unit: "g" },
  ]);
  const [bulkSummaryOpen, setBulkSummaryOpen] = useState(false);
  type BulkSummaryItem =
    | { type: 'quantity'; name: string; oldQty: number; newQty: number; unit: string }
    | { type: 'status'; name: string; status: string };
  const [bulkSummaryItems, setBulkSummaryItems] = useState<BulkSummaryItem[]>([]);
  const [bulkSummaryNote, setBulkSummaryNote] = useState<string | undefined>(undefined);
  // Inventory names for validation and suggestions
  const inventoryNames = useMemo(() => {
    const seen = new Set<string>();
    const out: string[] = [];
    for (const it of inventory) {
      const raw = String(it.name || "");
      const key = raw.toLowerCase().trim();
      if (!key) continue;
      if (!seen.has(key)) { seen.add(key); out.push(raw); }
    }
    return out.sort((a, b) => a.localeCompare(b));
  }, [inventory]);
  const inventoryNameSet = useMemo(() => new Set(inventoryNames.map(n => n.toLowerCase().trim())), [inventoryNames]);
  const inventoryNameUnitMap = useMemo(() => {
    const map = new Map<string, string>();
    for (const it of inventory) {
      const key = String(it.name || "").toLowerCase().trim();
      if (key && !map.has(key)) map.set(key, it.unit);
    }
    return map;
  }, [inventory]);

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
    <>
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
                <div className="flex items-center gap-2">
                  <Button size="sm" variant="outline" onClick={() => setBulkOpen(true)}>Bulk Consume</Button>
                  <TabsList>
                  <TabsTrigger value="current">Current</TabsTrigger>
                  <TabsTrigger value="expired">Expired</TabsTrigger>
                  </TabsList>
                </div>
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
    {/* Bulk Consume Dialog */}
    <Dialog open={bulkOpen} onOpenChange={setBulkOpen}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="font-headline">Bulk Consume</DialogTitle>
          <DialogDescription>Subtract multiple ingredients from your inventory at once.</DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          {/* Column headers (single row) */}
          <div className="grid grid-cols-12 gap-2 text-xs text-muted-foreground px-1">
            <div className="col-span-6">Name</div>
            <div className="col-span-3">Quantity</div>
            <div className="col-span-3">Unit</div>
          </div>
          {bulkRows.map((row, idx) => (
            <div key={idx} className="grid grid-cols-12 gap-2 items-end">
              <div className="col-span-6 space-y-1">
                <Input
                  value={row.name}
                  list="inventory-names"
                  onChange={(e) => {
                    const v = e.target.value;
                    setBulkRows((prev) => prev.map((r, i) => {
                      if (i !== idx) return r;
                      const lc = v.toLowerCase().trim();
                      // If exact inventory match, snap unit to that item's unit
                      const snapUnit = inventoryNameUnitMap.get(lc);
                      return snapUnit ? { ...r, name: v, unit: snapUnit } : { ...r, name: v };
                    }));
                  }}
                  placeholder="e.g., chicken breast"
                />
                {!!row.name.trim() && !inventoryNameSet.has(row.name.trim().toLowerCase()) && (
                  <p className="text-xs text-destructive">Not in inventory</p>
                )}
              </div>
              <div className="col-span-3 space-y-1">
                <Input
                  type="number"
                  value={row.quantity}
                  onChange={(e) => {
                    const v = e.target.value;
                    setBulkRows((prev) => prev.map((r, i) => i === idx ? { ...r, quantity: v } : r));
                  }}
                  placeholder="e.g., 300"
                />
              </div>
              <div className="col-span-3 space-y-1">
                <Select
                  value={row.unit}
                  onValueChange={(val) => setBulkRows((prev) => prev.map((r, i) => i === idx ? { ...r, unit: val } : r))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Unit" />
                  </SelectTrigger>
                  <SelectContent className="max-h-48">
                    {availableUnits.map((u) => (
                      <SelectItem key={`bulk-${idx}-${u.value}`} value={u.value}>{u.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="col-span-12 flex justify-end">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setBulkRows((prev) => prev.filter((_, i) => i !== idx))}
                  disabled={bulkRows.length <= 1}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
          {/* Datalist for name suggestions */}
          <datalist id="inventory-names">
            {inventoryNames.map((n) => (
              <option value={n} key={n} />
            ))}
          </datalist>
          <div className="flex justify-between pt-2">
            <Button variant="outline" onClick={() => setBulkRows((prev) => [...prev, { name: "", quantity: "", unit: "g" }])}>
              <PlusCircle className="h-4 w-4 mr-2" /> Add Row
            </Button>
            <div className="flex gap-2">
              <Button variant="ghost" onClick={() => setBulkOpen(false)}>Cancel</Button>
              <Button
                onClick={async () => {
                  if (!user?.id) return;
                  const items = bulkRows
                    .map(r => ({ name: r.name.trim(), quantity: parseFloat(r.quantity || '0'), unit: r.unit }))
                    .filter(r => r.name && r.quantity > 0);
                  if (items.length === 0) { setBulkOpen(false); return; }
                  // Validate all names are present in inventory
                  const missing = items.filter(it => !inventoryNameSet.has(it.name.toLowerCase().trim())).map(it => it.name);
                  if (missing.length > 0) {
                    alert(`These names are not in your inventory: \n- ${missing.join("\n- ")}`);
                    return;
                  }
                  // Snapshot old totals by name before consuming
                  const targetNames = Array.from(new Set(items.map(i => i.name.toLowerCase().trim())));
                  const aggregateTotals = (list: InventoryFormItem[]) => {
                    const totals = new Map<string, number>();
                    const units = new Map<string, string>();
                    for (const it of list) {
                      const key = String(it.name || '').toLowerCase().trim();
                      if (!targetNames.includes(key)) continue;
                      totals.set(key, (totals.get(key) || 0) + (it.quantity || 0));
                      if (!units.has(key)) units.set(key, it.unit || '');
                    }
                    return { totals, units };
                  };
                  const beforeAgg = aggregateTotals(inventory);
                  const res = await bulkConsumeInventory(user.id, items);
                  if (!res.ok) {
                    alert(res.message || 'Failed to apply bulk consumption');
                    return;
                  }
                  // Refresh inventory from API and update parent
                  try {
                    const apiInv = await getInventory(user.id);
                    const formInventory: InventoryFormItem[] = apiInv.map(item => ({
                      id: item.id,
                      name: item.item_name,
                      quantity: item.quantity,
                      unit: item.unit,
                      purchaseDate: item.added_at,
                      expiryDate: item.expiry_date,
                      shelfLife: 7,
                    }));
                    // Compute new totals and prepare cooked-style summary (old -> new) (removed)
                    const afterAgg = aggregateTotals(formInventory);
                    const v = (n: number) => {
                      const r = Math.round((n + Number.EPSILON) * 100) / 100;
                      return Number.isInteger(r) ? r.toString() : r.toString();
                    };
                    const byRequestedOrder = Array.from(new Set(items.map(i => i.name)));
                    const summaryItems: BulkSummaryItem[] = [];
                    for (const displayName of byRequestedOrder) {
                      const key = displayName.toLowerCase().trim();
                      const oldQty = beforeAgg.totals.get(key) || 0;
                      const newQty = afterAgg.totals.get(key) || 0;
                      const unit = afterAgg.units.get(key) || beforeAgg.units.get(key) || items.find(i => i.name.toLowerCase().trim() === key)?.unit || '';
                      const removed = Math.max(0, oldQty - newQty);
                      // Only show if there was any change or if item existed
                      if (oldQty > 0 || removed > 0) {
                        summaryItems.push({ type: 'quantity', name: displayName, oldQty, newQty, unit });
                      } else {
                        // fallback when not found or zero
                        summaryItems.push({ type: 'status', name: displayName, status: 'not found in inventory' });
                      }
                    }
                    setBulkSummaryItems(summaryItems);
                    setBulkSummaryNote(res.message);
                    setBulkSummaryOpen(true);
                    onUpdateInventory(formInventory);
                  } catch {}
                  setBulkOpen(false);
                  // Reset rows
                  setBulkRows([{ name: '', quantity: '', unit: 'g' }]);
                }}
              >
                Apply
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
    {/* Bulk Consume Result Popup */}
    <AlertDialog open={bulkSummaryOpen} onOpenChange={setBulkSummaryOpen}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Inventory updated</AlertDialogTitle>
        </AlertDialogHeader>
        <div className="text-sm text-muted-foreground">
          {bulkSummaryNote && (
            <p className="mb-2 text-foreground">{bulkSummaryNote}</p>
          )}
          <ul className="list-disc pl-5 space-y-1 text-foreground">
            {bulkSummaryItems.map((it, idx) => {
              if (it.type === 'quantity') {
                const delta = it.oldQty - it.newQty;
                const v = (n: number) => {
                  const r = Math.round((n + Number.EPSILON) * 100) / 100;
                  return Number.isInteger(r) ? r.toString() : r.toString();
                };
                return (
                  <li key={idx}>
                    {it.name}: {v(it.oldQty)} {it.unit} <span className="mx-1">→</span> {v(it.newQty)} {it.unit} <span className="text-destructive font-medium">({delta > 0 ? '-' : ''}{v(Math.abs(delta))} {it.unit})</span>
                  </li>
                );
              }
              return (<li key={idx}>{it.name}: {it.status}</li>);
            })}
          </ul>
        </div>
        <AlertDialogFooter>
          <AlertDialogAction onClick={() => setBulkSummaryOpen(false)}>OK</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
    </>
  );
}
