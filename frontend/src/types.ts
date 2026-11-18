export type Role =
  "farmer" | "buyer" | "administrator" | "logistics" | "transporter";
export interface User {
  id: number;
  name: string;
  email: string;
  role: Role;
  status: string;
  active: boolean;
  phone: string;
  region: string;
  location: string;
  farm_size_acres: number;
  crop_categories: string;
  business_name: string;
  verification_note: string;
  created_at: string;
}
export interface Produce {
  id: number;
  farmer_id: number;
  name: string;
  crop: string;
  description: string;
  available_kg: number;
  price_tzs: number;
  harvest_date: string;
  active: boolean;
  farmer_name: string;
  region: string;
  location: string;
}
export interface Order {
  id: number;
  buyer_id: number;
  farmer_id: number;
  status: string;
  total_tzs: number;
  delivery_address: string;
  note: string;
  created_at: string;
  buyer_name: string;
  farmer_name: string;
  items: {
    id: number;
    produce_id: number;
    produce_name: string;
    quantity_kg: number;
    unit_price_tzs: number;
  }[];
}
export interface Payment {
  id: number;
  order_id: number;
  provider: string;
  amount_tzs: number;
  status: string;
  reference: string;
  created_at: string;
}
export interface Receipt {
  number: string;
  order_id: number;
  payment_id: number;
  amount_tzs: number;
  created_at: string;
  buyer_name: string;
  farmer_name: string;
  provider: string;
  reference: string;
  currency: string;
  mode: string;
}
export interface Shipment {
  next_states: string[];
  id: number;
  order_id: number;
  transporter_id: number | null;
  status: string;
  tracking_code: string;
  transporter_name: string | null;
  farmer_name: string;
  buyer_name: string;
  pickup: string;
  destination: string;
  history: {
    id: number;
    status: string;
    location: string;
    note: string;
    created_at: string;
  }[];
}
export interface Notice {
  id: number;
  kind: string;
  message: string;
  read: boolean;
  sms_status: string;
  sms_reference: string;
  created_at: string;
  recipient?: string;
}
export interface MarketPrice {
  id: number;
  crop: string;
  region: string;
  price_tzs: number;
  observed_on: string;
  source: string;
}
export interface Report {
  users: number;
  farmers: number;
  buyers: number;
  pending_approvals: number;
  active_listings: number;
  orders: number;
  completed_orders: number;
  successful_payments: number;
  gross_sales_tzs: number;
  shipments: number;
  delivered_shipments: number;
  sms_simulated: number;
  definition: string;
  sales_by_produce: {
    produce: string;
    quantity_kg: number;
    sales_tzs: number;
  }[];
  sales_by_region: { region: string; sales_tzs: number }[];
  orders_by_status: { status: string; count: number }[];
}
