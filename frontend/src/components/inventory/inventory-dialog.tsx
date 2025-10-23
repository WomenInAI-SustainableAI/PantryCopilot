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
import { addDays, differenceInDays, format } from "date-fns";
import { Badge } from "../ui/badge";
import { PlusCircle, Trash2, Edit } from "lucide-react";
import { addInventoryItem, deleteInventoryItem, updateInventoryItem } from "@/app/actions";
import { useAuth } from "@/lib/auth";

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
  const [editingItem, setEditingItem] = useState<InventoryFormItem | null>(null);
  const [newItem, setNewItem] = useState({
    name: "",
    quantity: "",
    unit: "",
    purchaseDate: format(new Date(), "yyyy-MM-dd"),
    shelfLife: "",
  });

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
      const shelfLife = parseInt(newItem.shelfLife, 10);
      const expiryDate = addDays(purchaseDate, shelfLife);

      if (!user) throw new Error('User not authenticated');
      const userId = user.id;
      
      if (editingItem) {
        // Update existing item via API
        const updatedItem = await updateInventoryItem(userId, editingItem.id, {
          item_name: newItem.name,
          quantity: parseFloat(newItem.quantity),
          unit: newItem.unit
        });
        
        const updatedInventory = inventory.map(item => 
          item.id === editingItem.id 
            ? { ...item, name: updatedItem.item_name, quantity: updatedItem.quantity, unit: updatedItem.unit }
            : item
        );
        onUpdateInventory(updatedInventory);
      } else {
        // Add new item
        const apiItem = await addInventoryItem(userId, {
          item_name: newItem.name,
          quantity: parseFloat(newItem.quantity),
          unit: newItem.unit,
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
      setEditingItem(null);
    } catch (error) {
      console.error('Failed to add inventory item:', error);
      alert('Failed to add item. Please try again.');
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
    const days = differenceInDays(new Date(expiryDate), new Date());
    if (days < 0) return <Badge variant="destructive">Expired</Badge>;
    if (days <= 3) return <Badge variant="destructive">Expires in {days}d</Badge>;
    if (days <= 7) return <Badge variant="secondary" className="bg-accent text-accent-foreground">Expires in {days}d</Badge>;
    return <Badge variant="outline">Expires in {days}d</Badge>;
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
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
                <Input
                  id="unit"
                  value={newItem.unit}
                  onChange={(e) => setNewItem({ ...newItem, unit: e.target.value })}
                  placeholder="e.g., pcs"
                />
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
              <Label htmlFor="shelfLife">Shelf Life (days) - Optional</Label>
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
              <Button onClick={handleSaveItem} className="flex-1">
                {editingItem ? (
                  <><Edit className="mr-2 h-4 w-4" /> Update Item</>
                ) : (
                  <><PlusCircle className="mr-2 h-4 w-4" /> Add Item</>
                )}
              </Button>
              {editingItem && (
                <Button onClick={() => setEditingItem(null)} variant="outline">
                  Cancel
                </Button>
              )}
            </div>
          </div>
          <div className="md:col-span-2">
            <h3 className="font-semibold font-headline mb-4">Current Inventory</h3>
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
                  {inventory.map((item) => (
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
                              setNewItem({
                                name: item.name,
                                quantity: item.quantity.toString(),
                                unit: item.unit,
                                purchaseDate: format(new Date(), "yyyy-MM-dd"),
                                shelfLife: "",
                              });
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
