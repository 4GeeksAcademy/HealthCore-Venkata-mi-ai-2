import { isLowStock, type InventoryProduct } from "@/types/inventory";

const gloves: InventoryProduct = {
  id: 1,
  name: "Nitrile exam gloves (box of 100)",
  sku: "HC-PPE-GLV-100",
  stock: 12,
  threshold: 24,
};

const pads: InventoryProduct = {
  id: 2,
  name: "Alcohol prep pads (box of 200)",
  sku: "HC-CLN-PAD-200",
  stock: 80,
  threshold: 30,
};

describe("isLowStock", () => {
  test("flags stock below the restock threshold", () => {
    expect(isLowStock(gloves)).toBe(true);
  });

  test("treats stock at or above the threshold as OK", () => {
    expect(isLowStock(pads)).toBe(false);
    expect(isLowStock({ ...pads, stock: 30 })).toBe(false);
  });
});
