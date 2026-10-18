export interface CustomerProfile {
  name: string;
  email: string;
  mobile: string;
  customerId: string;
  isGuest?: boolean;
}

export interface ShipmentTimelineEvent {
  title: string;
  time: string;
  location: string;
  done?: boolean;
  current?: boolean;
}

export interface Shipment {
  id: string;
  status: 'In Transit' | 'Delayed' | 'Under Review' | 'Delivered';
  statusColor: string;
  origin: string;
  currentLocation: string;
  destination: string;
  expectedDelivery: string;
  previousExpectedDelivery?: string;
  delayReason?: string;
  carrier: string;
  item: string;
  weight: string;
  progressStep: number;
  hasDamageReport?: boolean;
  timeline: ShipmentTimelineEvent[];
}

export interface SupportTicket {
  id: string;
  shipmentId: string;
  issue: string;
  status: 'Under Review' | 'Resolved' | 'In Progress';
  statusColor: string;
  createdAt: string;
  description: string;
  resolutionETA: string;
}

export interface Invoice {
  id: string;
  shipmentId: string;
  amount: number;
  status: 'Paid' | 'Pending';
  date: string;
  paymentMethod: string;
  items: { name: string; amount: number }[];
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  timestamp: string;
  text: string;
  showQuickActions?: boolean;
  metadata?: {
    type?: 'shipment_card' | 'delay_card' | 'ticket_card' | 'invoice_card' | 'human_support_card' | 'refund_card';
    shipment?: Shipment;
    ticket?: SupportTicket;
    invoice?: Invoice;
    refund?: {
      shipmentId: string;
      amount: number;
      reason: string;
      status: string;
    };
    quickReplies?: string[];
  };
}
