export type SupplierStatus = "active" | "suspended";
export type SupplierCountry = "US" | "UK";

export type ProductCategory =
  | "MEDICAL_SUPPLIES"
  | "LAB_CONSUMABLES"
  | "PPE"
  | "PHARMACEUTICALS"
  | "IT_EQUIPMENT"
  | "FACILITIES"
  | "DIAGNOSTIC_EQUIPMENT";

export const PRODUCT_CATEGORIES: ProductCategory[] = [
  "MEDICAL_SUPPLIES",
  "LAB_CONSUMABLES",
  "PPE",
  "PHARMACEUTICALS",
  "IT_EQUIPMENT",
  "FACILITIES",
  "DIAGNOSTIC_EQUIPMENT",
];

export type Supplier = {
  id: number;
  name: string;
  country: SupplierCountry;
  product_categories: ProductCategory[];
  contract_rate: number;
  updated_at: string;
  status: SupplierStatus;
};

export type SupplierCreate = {
  name: string;
  country: SupplierCountry;
  product_categories: ProductCategory[];
  contract_rate: number;
  status: SupplierStatus;
};
