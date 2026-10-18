import { Shipment, SupportTicket, Invoice } from '../types/logistics';

export const MOCK_SHIPMENTS: Record<string, Shipment> = {
  'SL1004': {
    id: 'SL1004',
    status: 'In Transit',
    statusColor: 'blue',
    origin: 'Bhiwandi Hub, Mumbai, MH',
    currentLocation: 'Ahmedabad Distribution Center',
    destination: 'B-402, Riverfront Heights, Ashram Road, Ahmedabad, GJ',
    expectedDelivery: '8 October 2026',
    carrier: 'LogiFlow Express Air',
    item: 'Electronic Components (Fragile)',
    weight: '2.8 kg',
    progressStep: 3,
    timeline: [
      { title: 'Order Confirmed', time: '05 Oct 2026, 10:30 AM', location: 'Merchant Warehouse', done: true },
      { title: 'Picked Up', time: '05 Oct 2026, 03:15 PM', location: 'Bhiwandi Gateway Hub', done: true },
      { title: 'In Transit', time: '07 Oct 2026, 02:45 PM', location: 'Ahmedabad Distribution Center', current: true },
      { title: 'Out for Delivery', time: 'Expected 08 Oct, 09:30 AM', location: 'Ashram Road Station', done: false },
      { title: 'Delivered', time: 'Expected 08 Oct, 04:00 PM', location: 'Riverfront Heights', done: false }
    ]
  },
  'SL1002': {
    id: 'SL1002',
    status: 'Delayed',
    statusColor: 'amber',
    origin: 'Electronic City, Bengaluru, KA',
    currentLocation: 'Pune Central Transshipment Hub',
    destination: '45 Lake View Residency, Pune, MH',
    previousExpectedDelivery: '7 October 2026',
    expectedDelivery: '9 October 2026',
    delayReason: 'Operational delay due to heavy rainfall highway diversion',
    carrier: 'LogiFlow Surface Connect',
    item: 'Apparel & Fabric Package',
    weight: '1.4 kg',
    progressStep: 3,
    timeline: [
      { title: 'Order Confirmed', time: '04 Oct 2026, 09:00 AM', location: 'Bengaluru DC', done: true },
      { title: 'Picked Up', time: '04 Oct 2026, 02:00 PM', location: 'Bengaluru Gate', done: true },
      { title: 'In Transit (Delayed)', time: '07 Oct 2026, 11:30 AM', location: 'Pune Transshipment Hub', current: true },
      { title: 'Out for Delivery', time: 'Expected 09 Oct, 10:00 AM', location: 'Pune Station', done: false },
      { title: 'Delivered', time: 'Expected 09 Oct, 05:00 PM', location: 'Customer Doorstep', done: false }
    ]
  },
  'SL1003': {
    id: 'SL1003',
    status: 'Under Review',
    statusColor: 'rose',
    origin: 'Sector 62, Noida, UP',
    currentLocation: 'Jaipur Sorting Center',
    destination: '12 Sunrise Apartments, Jaipur, RJ',
    expectedDelivery: '7 October 2026 (Delivered with Claim)',
    carrier: 'LogiFlow Priority Air',
    item: 'Glassware & Decorative Set',
    weight: '3.1 kg',
    progressStep: 5,
    hasDamageReport: true,
    timeline: [
      { title: 'Order Confirmed', time: '03 Oct 2026, 11:00 AM', location: 'Noida Hub', done: true },
      { title: 'Picked Up', time: '03 Oct 2026, 04:30 PM', location: 'Delhi Air Cargo', done: true },
      { title: 'In Transit', time: '05 Oct 2026, 08:00 AM', location: 'Jaipur Sorting Center', done: true },
      { title: 'Out for Delivery', time: '07 Oct 2026, 09:15 AM', location: 'Jaipur Delivery Station', done: true },
      { title: 'Delivered (Damage Reported)', time: '07 Oct 2026, 01:20 PM', location: 'Delivered to Customer', current: true }
    ]
  },
  'SL1001': {
    id: 'SL1001',
    status: 'Delivered',
    statusColor: 'emerald',
    origin: 'Chennai Port Hub, TN',
    currentLocation: 'Hyderabad Final Station',
    destination: 'Plot 88, Jubilee Hills, Hyderabad, TS',
    expectedDelivery: '04 October 2026 (Delivered)',
    carrier: 'LogiFlow Surface Connect',
    item: 'Office Documents & Supplies',
    weight: '0.8 kg',
    progressStep: 5,
    timeline: [
      { title: 'Order Confirmed', time: '01 Oct 2026', location: 'Chennai DC', done: true },
      { title: 'Picked Up', time: '01 Oct 2026', location: 'Chennai Hub', done: true },
      { title: 'In Transit', time: '02 Oct 2026', location: 'Vijayawada Crossdock', done: true },
      { title: 'Out for Delivery', time: '04 Oct 2026', location: 'Jubilee Hills Station', done: true },
      { title: 'Delivered', time: '04 Oct 2026, 03:45 PM', location: 'Signed by Rahul Patel', done: true }
    ]
  }
};

export const MOCK_TICKETS: SupportTicket[] = [
  {
    id: 'LGT-1024',
    shipmentId: 'SL1003',
    issue: 'Damaged Package',
    status: 'Under Review',
    statusColor: 'amber',
    createdAt: '07 Oct 2026, 05:10 PM',
    description: 'Customer reported crushed outer box and broken inner items upon unboxing.',
    resolutionETA: 'Within 24 Hours'
  },
  {
    id: 'LGT-1021',
    shipmentId: 'SL1002',
    issue: 'Delivery Delay Inquiry',
    status: 'Resolved',
    statusColor: 'emerald',
    createdAt: '06 Oct 2026, 11:30 AM',
    description: 'Estimated delivery updated to 9 Oct 2026 due to weather rerouting. Customer notified via SMS.',
    resolutionETA: 'Resolved'
  }
];

export const MOCK_INVOICES: Invoice[] = [
  {
    id: 'INV-2045',
    shipmentId: 'SL1004',
    amount: 1250,
    status: 'Paid',
    date: '7 October 2026',
    paymentMethod: 'UPI Auto-Debit',
    items: [
      { name: 'Express Freight (Mumbai to Ahmedabad)', amount: 850 },
      { name: 'Fragile Anti-Shock Handling', amount: 200 },
      { name: 'Doorstep Linehaul Surcharge', amount: 59.32 },
      { name: 'Integrated GST (18%)', amount: 140.68 }
    ]
  },
  {
    id: 'INV-2046',
    shipmentId: 'SL1001',
    amount: 850,
    status: 'Paid',
    date: '4 October 2026',
    paymentMethod: 'Corporate Card',
    items: [
      { name: 'Standard Surface Delivery (Chennai to Hyderabad)', amount: 720.34 },
      { name: 'GST (18%)', amount: 129.66 }
    ]
  }
];
