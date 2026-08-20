export type SupplierStatus = "active" | "suspended";
export type SupplierCountry = "USA" | "UK";
export type SupplierCurrency = "USD" | "GBP";

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

export function currencyForCountry(country: SupplierCountry): SupplierCurrency {
  return country === "USA" ? "USD" : "GBP";
}

export type Supplier = {
  id: number;
  name: string;
  country: SupplierCountry;
  categories: ProductCategory[];
  monthly_rate: number;
  currency: SupplierCurrency;
  updated_at: string;
  status: SupplierStatus;
};

export type SupplierCreate = {
  name: string;
  country: SupplierCountry;
  categories: ProductCategory[];
  monthly_rate: number;
  currency: SupplierCurrency;
  status: SupplierStatus;
};
