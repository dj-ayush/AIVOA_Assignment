import { FORM_SECTIONS, RISK_FIELDS } from "../constants";
import StatusBadge from "./StatusBadge";

function ChevronIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
      <path d="M6 9l6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function Field({ field, value, highlighted }) {
  const isEmpty = value === null || value === undefined || value === "";
  const classNames = [
    "field-value",
    isEmpty ? "field-empty" : "",
    highlighted ? "field-highlighted" : "",
    field.multiline ? "field-multiline" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={`field ${field.full ? "field-full" : ""}`}>
      <label>{field.label}</label>
      <div className={classNames} title={isEmpty ? undefined : value}>
        <span>{isEmpty ? field.placeholder : value}</span>
        {!isEmpty && <span className="ai-field-indicator">AI</span>}
        {field.dropdown && <ChevronIcon />}
      </div>
    </div>
  );
}

export default function DeviationForm({ form, risk, status, changedFields, onCommit, onReset, committing, lastSavedRecord }) {
  const isReady = status === "ready_to_save";

  return (
    <div className="form-panel">
      <div className="form-header">
        <div>
          <h1>Log Deviation</h1>
          <p className="form-subtitle">DeviationIQ | API &amp; FDF Quality Assurance</p>
        </div>
        <StatusBadge status={status} />
      </div>

      <div className="form-scroll">
        {FORM_SECTIONS.map((section) => (
          <div className="form-section" key={section.title}>
            <div className="section-title">{section.title}</div>
            <div className="field-grid">
              {section.fields.map((field) => (
                <Field
                  key={field.key}
                  field={field}
                  value={form[field.key]}
                  highlighted={changedFields.includes(field.key)}
                />
              ))}
            </div>
          </div>
        ))}

        <div className="risk-panel">
          <div className="risk-panel-title">
            <ShieldIcon />
            Impact Assessment
          </div>
          <div className="field-grid">
            {RISK_FIELDS.map((field) => (
              <Field
                key={field.key}
                field={field}
                value={risk[field.key]}
                highlighted={changedFields.includes(field.key)}
              />
            ))}
          </div>
        </div>

        {lastSavedRecord && <div className="save-confirmation">Saved deviation {lastSavedRecord}</div>}

        <div className="form-actions">
          <button className="reset-btn" type="button" onClick={onReset} disabled={committing}>
            Reset Deviation
          </button>
          <button className="commit-btn" disabled={!isReady || committing} onClick={onCommit}>
            {committing ? "Saving..." : "Save Deviation"}
          </button>
        </div>
      </div>
    </div>
  );
}

function ShieldIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 3l7 3v6c0 4.5-3 8-7 9-4-1-7-4.5-7-9V6l7-3z" strokeLinejoin="round" />
    </svg>
  );
}
