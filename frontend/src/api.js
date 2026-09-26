const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(url, options) {
  try {
    return await fetch(url, options);
  } catch {
    throw new Error(
      `Network request failed for ${url}. Check VITE_API_BASE_URL, backend availability, and CORS allowed origins.`
    );
  }
}

async function handle(res) {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      /* ignore parse errors */
    }
    throw new Error(detail || `Request failed with ${res.status}`);
  }
  return res.json();
}

export async function sendChatMessage(message, currentForm, currentRisk, history) {
  const res = await request(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      current_form: currentForm,
      current_risk: currentRisk,
      history,
    }),
  });
  return handle(res);
}

export async function uploadDocument(file, currentForm, currentRisk) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("current_form", JSON.stringify(currentForm));
  formData.append("current_risk", JSON.stringify(currentRisk));

  const res = await request(`${API_BASE}/api/upload`, {
    method: "POST",
    body: formData,
  });
  return handle(res);
}

export async function saveDeviation(form, riskAssessment) {
  const res = await request(`${API_BASE}/api/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ form, risk_assessment: riskAssessment }),
  });
  return handle(res);
}

export async function checkHealth() {
  const res = await request(`${API_BASE}/api/health`);
  return handle(res);
}
