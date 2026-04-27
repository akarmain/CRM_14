const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api/v1';

export const ROLE_OPTIONS = [
  { value: 'manager_1', label: 'Менеджер 1' },
  { value: 'manager_2', label: 'Менеджер 2' },
  { value: 'analyst', label: 'Аналитик' },
  { value: 'sales_head', label: 'Руководитель отдела продаж' },
];

export const OWNER_OPTIONS = [
  { value: 'manager_1', label: 'Менеджер 1' },
  { value: 'manager_2', label: 'Менеджер 2' },
  { value: 'sales_head', label: 'Руководитель отдела продаж' },
];

export const SOURCE_OPTIONS = [
  { value: 'website', label: 'Сайт' },
  { value: 'advertisement', label: 'Реклама' },
  { value: 'recommendation', label: 'Рекомендация' },
  { value: 'event', label: 'Событие' },
  { value: 'other', label: 'Другое' },
];

export const STAGE_OPTIONS = [
  { value: 'new', label: 'Новый' },
  { value: 'qualified', label: 'Квалификация' },
  { value: 'proposal', label: 'Предложение' },
  { value: 'won', label: 'Успешно' },
  { value: 'lost', label: 'Потерян' },
];

export class ApiError extends Error {
  constructor(message, status, detail = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

function buildQuery(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') {
      return;
    }
    query.set(key, value);
  });
  const asString = query.toString();
  return asString ? `?${asString}` : '';
}

async function parseError(response) {
  const text = await response.text();
  if (!text) {
    throw new ApiError('Запрос завершился ошибкой.', response.status);
  }

  let payload = null;
  try {
    payload = JSON.parse(text);
  } catch {
    throw new ApiError(text, response.status);
  }

  const detail = payload?.detail ?? payload;
  if (typeof detail === 'string') {
    throw new ApiError(detail, response.status, payload);
  }
  if (detail?.message) {
    throw new ApiError(detail.message, response.status, payload);
  }
  throw new ApiError('Запрос завершился ошибкой.', response.status, payload);
}

async function request(path, options = {}) {
  const { responseType = 'json', ...init } = options;
  const headers = new Headers(init.headers ?? {});
  const nextInit = { ...init, headers, credentials: 'include' };

  if (init.body && !(init.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  if (headers.get('Content-Type') === 'application/json' && typeof init.body !== 'string') {
    nextInit.body = JSON.stringify(init.body);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, nextInit);

  if (!response.ok) {
    await parseError(response);
  }

  if (response.status === 204) {
    return null;
  }

  if (responseType === 'blob') {
    return response;
  }

  if (responseType === 'text') {
    return response.text();
  }

  return response.json();
}

export function getRoleLabel(role) {
  return ROLE_OPTIONS.find((option) => option.value === role)?.label ?? role;
}

export function getStageLabel(stage) {
  return STAGE_OPTIONS.find((option) => option.value === stage)?.label ?? stage;
}

export function getSourceLabel(sourceCode) {
  return SOURCE_OPTIONS.find((option) => option.value === sourceCode)?.label ?? sourceCode;
}

export function getLeadDisplayName(lead) {
  return lead.title?.trim() || 'Без названия';
}

export function getForwardTargets(stage) {
  if (stage === 'new') return ['qualified'];
  if (stage === 'qualified') return ['proposal'];
  if (stage === 'proposal') return ['won', 'lost'];
  return [];
}

export async function fetchSession() {
  try {
    return await request('/session/me');
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      return null;
    }
    throw error;
  }
}

export function selectRole(role) {
  return request('/session/role', { method: 'POST', body: { role } });
}

export function clearSession() {
  return request('/session/role', { method: 'DELETE' });
}

export function fetchLeads(filters = {}) {
  return request(`/leads${buildQuery(filters)}`);
}

export function fetchLeadDetail(leadUid) {
  return request(`/leads/${leadUid}`);
}

export function createLead(payload) {
  return request('/leads', { method: 'POST', body: payload });
}

export function updateLead(leadUid, payload) {
  return request(`/leads/${leadUid}`, { method: 'PATCH', body: payload });
}

export function deleteLead(leadUid) {
  return request(`/leads/${leadUid}`, { method: 'DELETE' });
}

export function moveLeadStage(leadUid, stage, comment = null) {
  return request(`/leads/${leadUid}/stage`, {
    method: 'POST',
    body: { stage, comment },
  });
}

export function requestReturnToPreviousStage(leadUid, comment) {
  return request(`/leads/${leadUid}/return-requests`, {
    method: 'POST',
    body: { comment },
  });
}

export function fetchReturnRequests(filters = {}) {
  return request(`/return-requests${buildQuery(filters)}`);
}

export function approveReturnRequest(requestId, reviewComment) {
  return request(`/return-requests/${requestId}/approve`, {
    method: 'POST',
    body: { review_comment: reviewComment },
  });
}

export function rejectReturnRequest(requestId, reviewComment) {
  return request(`/return-requests/${requestId}/reject`, {
    method: 'POST',
    body: { review_comment: reviewComment },
  });
}

export function fetchReportsSummary(filters = {}) {
  return request(`/reports/summary${buildQuery(filters)}`);
}

export function fetchAuditLog(filters = {}) {
  return request(`/audit-log${buildQuery(filters)}`);
}

export function importLeads(file) {
  const formData = new FormData();
  formData.append('file', file);
  return request('/leads/import', { method: 'POST', body: formData });
}

export async function exportLeads(fileType, filters = {}) {
  const query = buildQuery({ file_type: fileType, ...filters });
  const response = await request(`/leads/export${query}`, { responseType: 'blob' });
  const disposition = response.headers.get('content-disposition') ?? '';
  const filenameMatch = disposition.match(/filename="([^"]+)"/);
  const filename = filenameMatch?.[1] ?? `leads.${fileType}`;
  const blob = await response.blob();
  return { blob, filename };
}
