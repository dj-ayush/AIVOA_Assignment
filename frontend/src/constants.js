export const EMPTY_FORM = {
  complaint_source: null,
  customer_name: null,
  product_name: null,
  product_strength: null,
  batch_lot_number: null,
  affected_quantity: null,
  manufacturing_date: null,
  expiry_date: null,
  originating_site_block: null,
  impacted_npm: null,
  complaint_category: null,
  complaint_description: null,
};

export const EMPTY_RISK = {
  severity: null,
  suggested_next_action: null,
  initial_risk_assessment: null,
};

// Layout config for the left-hand form. Each section renders a group of
// fields; `dropdown: true` adds a chevron affordance since these are
// AI-populated, not manually editable.
export const FORM_SECTIONS = [
  {
    title: "1. Origin & Reporter Details",
    fields: [
      { key: "complaint_source", label: "Deviation Source", dropdown: true, placeholder: "Awaiting AI classification..." },
      { key: "customer_name", label: "Reporter Name / Role", placeholder: "Awaiting AI extraction..." },
    ],
  },
  {
    title: "2. Product & Batch Identification",
    fields: [
      { key: "product_name", label: "Product Name (API/FDF)", placeholder: "Awaiting AI extraction..." },
      { key: "product_strength", label: "Product Strength / Grade", placeholder: "Awaiting AI extraction..." },
      { key: "batch_lot_number", label: "Batch / Lot Number", placeholder: "Awaiting AI extraction..." },
      { key: "affected_quantity", label: "Affected Quantity", placeholder: "Awaiting AI extraction..." },
      { key: "manufacturing_date", label: "Manufacturing Date", placeholder: "Awaiting AI extraction..." },
      { key: "expiry_date", label: "Expiry Date", placeholder: "Awaiting AI extraction..." },
    ],
  },
  {
    title: "3. Facility & Material Impact",
    fields: [
      { key: "originating_site_block", label: "Originating Site Block", dropdown: true, placeholder: "Awaiting AI classification..." },
      { key: "impacted_npm", label: "Impacted Non-Product Materials (NPM)", placeholder: "e.g., Primary packaging..." },
    ],
  },
  {
    title: "4. Deviation Details",
    fields: [
      { key: "complaint_category", label: "Deviation Category", placeholder: "Awaiting AI classification..." },
      {
        key: "complaint_description",
        label: "Deviation Details",
        placeholder: "AI will synthesize the deviation into a formal QMS description...",
        multiline: true,
        full: true,
      },
    ],
  },
];

export const RISK_FIELDS = [
  { key: "severity", label: "Severity Assessment", placeholder: "Pending analysis..." },
  { key: "suggested_next_action", label: "Recommended Action", placeholder: "Pending analysis..." },
  {
    key: "initial_risk_assessment",
    label: "Impact Assessment",
    placeholder: "AI will generate impact, containment, and investigation context once the deviation is parsed...",
    multiline: true,
    full: true,
  },
];
