import { asOrder, asProduct } from "@/lib/inventory-api";
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

describe("asProduct", () => {
  test("maps ORM current_stock onto the stock column the UI displays", () => {
    const row = asProduct({
      id: 1,
      name: "Nitrile exam gloves (box of 100)",
      sku: "HC-PPE-GLV-100",
      current_stock: 12,
      threshold: 24,
    });
    expect(row.stock).toBe(12);
    expect(row.sku).toBe("HC-PPE-GLV-100");
  });
});

describe("asOrder", () => {
  test("prefers TinyDB email created_by and keeps product_name", () => {
    const row = asOrder({
      id: 1,
      product_id: 1,
      product_name: "Nitrile exam gloves (box of 100)",
      quantity: 40,
      type: "inbound",
      notes: "McKesson delivery — Austin clinic restock",
      created_at: "2026-09-11T12:05:00+00:00",
      user_uuid: "1",
      created_by: "ops.manager@healthcore.example",
    });
    expect(row.created_by).toBe("ops.manager@healthcore.example");
    expect(row.product_name).toBe("Nitrile exam gloves (box of 100)");
    expect(row.type).toBe("inbound");
  });

  test("falls back to user_uuid when created_by is absent", () => {
    const row = asOrder({
      id: 1,
      product_id: 1,
      product_name: "Pads",
      quantity: 80,
      type: "inbound",
      notes: "",
      created_at: "2026-09-11T12:05:00+00:00",
      user_uuid: "1",
    });
    expect(row.created_by).toBe("1");
  });
});
