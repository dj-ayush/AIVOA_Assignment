"""
Domain and API schemas for the DeviationIQ backend.

Design note on "patch" semantics:
For the edit-deviation flow we do NOT ask the LLM to repeat the whole form
back to us (models can subtly reword text even when told not to, which would
violate the "preserve everything else" requirement). Instead the LLM returns
a *patch* object shaped exactly like the form/risk models, where a field is
either a new value or `null` ("no change"). The backend merges the patch onto
the current state in plain Python, which guarantees untouched fields are
byte-for-byte preserved.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class DeviationForm(BaseModel):
    complaint_source: Optional[str] = Field(
        None, description="How the deviation was reported, e.g. Pharmacy, Email, Phone, Distributor, Physician, Patient"
    )
    customer_name: Optional[str] = Field(None, description="Reporter name, role, department, site, or company that raised the deviation")
    product_name: Optional[str] = Field(None, description="Full name of the pharmaceutical product or API")
    product_strength: Optional[str] = Field(None, description="Strength or grade, e.g. '500 mg' or 'IP/BP'")
    batch_lot_number: Optional[str] = Field(None, description="Batch or lot number of the affected product")
    affected_quantity: Optional[str] = Field(None, description="Quantity affected, e.g. '12 capsules' or '50 kg (2 HDPE Drum)'")
    manufacturing_date: Optional[str] = Field(None, description="Manufacturing date of the batch, as stated by the user")
    expiry_date: Optional[str] = Field(None, description="Expiry date of the batch, or 'Not Provided' if genuinely unknown")
    originating_site_block: Optional[str] = Field(None, description="Explicitly stated manufacturing site, area, block, suite, or line; leave null if not provided")
    impacted_npm: Optional[str] = Field(None, description="Impacted non-product materials, e.g. primary packaging, HDPE drums")
    complaint_category: Optional[str] = Field(None, description="Deviation category, e.g. 'Manufacturing Process Deviation - Tablet Weight Excursion'")
    complaint_description: Optional[str] = Field(None, description="Concise, formal QMS-style synthesis of the deviation")


class RiskAssessment(BaseModel):
    severity: Optional[str] = Field(None, description="One of: Minor, Major, Critical")
    suggested_next_action: Optional[str] = Field(None, description="Recommended next step for QA")
    initial_risk_assessment: Optional[str] = Field(None, description="1-2 sentence impact, product quality risk, containment, and investigation status")


class ExtractionOutput(BaseModel):
    """Used for brand-new deviations and document extraction, where the form starts empty."""
    form: DeviationForm
    risk_assessment: RiskAssessment
    reply_message: str = Field(description="Short chat reply confirming what was extracted, in the copilot's voice")


class PatchOutput(BaseModel):
    """Used for corrections to an in-progress deviation. Null fields mean 'no change'."""
    form_patch: DeviationForm
    risk_patch: RiskAssessment
    reply_message: str = Field(description="Short chat reply confirming exactly which field(s) were updated")


class IntentResult(BaseModel):
    intent: Literal["new_deviation", "edit_fields", "general"]


# ---- API layer ----

class ChatRequest(BaseModel):
    message: str
    current_form: DeviationForm = Field(default_factory=DeviationForm)
    current_risk: RiskAssessment = Field(default_factory=RiskAssessment)
    history: List[Dict[str, str]] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    form: DeviationForm
    risk_assessment: RiskAssessment
    changed_fields: List[str]
    status: Literal["pending_triage", "ready_to_save"]
    intent: Optional[str] = None
    observability: Optional[Dict[str, Any]] = None
