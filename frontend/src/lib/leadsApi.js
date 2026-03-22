const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1';

const UI_TO_API_ROLE = {
  'Менеджер 1': 'manager_1',
  'Менеджер 2': 'manager_2',
  'Руководитель отдела продаж': 'sales_head',
  'Аналитик': 'analyst',
};

const API_TO_UI_ROLE = {
  manager_1: 'Менеджер 1',
  manager_2: 'Менеджер 2',
  sales_head: 'Руководитель отдела продаж',
  analyst: 'Аналитик',
};

const UI_TO_API_SOURCE = {
  Сайт: 'website',
  Реклама: 'advertisement',
  Рекомендация: 'recommendation',
  Событие: 'event',
  Другое: 'other',
};

const API_TO_UI_SOURCE = {
  website: 'Сайт',
  advertisement: 'Реклама',
  recommendation: 'Рекомендация',
  event: 'Событие',
  other: 'Другое',
};

const UI_TO_API_STAGE = {
  Новый: 'new',
  Квалификация: 'qualified',
  Предложение: 'proposal',
  Успешно: 'won',
  Потерян: 'lost',
};

const API_TO_UI_STAGE = {
  new: 'Новый',
  qualified: 'Квалификация',
  proposal: 'Предложение',
  won: 'Успешно',
  lost: 'Потерян',
};

async function request(path, init = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init.headers ?? {}),
    },
    ...init,
  });

  if (response.status === 204) {
    return null;
  }

  const text = await response.text();
  const payload = text ? JSON.parse(text) : null;

  if (!response.ok) {
    const detail = payload?.detail;
    const message =
      typeof detail === 'string'
        ? detail
        : detail?.message ?? 'Не удалось выполнить запрос к FastAPI.';
    throw new Error(message);
  }

  return payload;
}

function mapLeadFromApi(lead) {
  return {
    uniqueKey: lead.lead_uid,
    leadUid: lead.lead_uid,
    customId: lead.lead_uid,
    name: lead.title ?? 'Без названия',
    description: lead.notes ?? '',
    source: API_TO_UI_SOURCE[lead.source_code] ?? lead.source_code,
    sourceCode: lead.source_code,
    manager: API_TO_UI_ROLE[lead.owner] ?? lead.owner,
    owner: lead.owner,
    status: API_TO_UI_STAGE[lead.current_stage] ?? lead.current_stage,
    stage: lead.current_stage,
  };
}

function mapCreateLeadPayload(lead, role) {
  return {
    owner: UI_TO_API_ROLE[role],
    title: lead.title.trim(),
    notes: lead.description.trim(),
    source_code: UI_TO_API_SOURCE[lead.source] ?? 'other',
  };
}

export async function fetchLeads() {
  const leads = await request('/leads');
  return leads.map(mapLeadFromApi);
}

export async function createLead(lead, role) {
  const created = await request('/leads', {
    method: 'POST',
    body: JSON.stringify(mapCreateLeadPayload(lead, role)),
  });

  return mapLeadFromApi(created);
}

export async function createLeadsBatch(leads, role) {
  const created = [];

  for (const lead of leads) {
    created.push(await createLead(lead, role));
  }

  return created;
}

export async function removeLead(leadUid) {
  await request(`/leads/${leadUid}`, { method: 'DELETE' });
}

export async function moveLeadStage(leadUid, status, role) {
  const moved = await request(`/leads/${leadUid}/stage`, {
    method: 'POST',
    body: JSON.stringify({
      stage: UI_TO_API_STAGE[status],
      author: UI_TO_API_ROLE[role],
      comment: null,
    }),
  });

  return mapLeadFromApi(moved.lead);
}

export function getLeadIds(leads) {
  return leads.map((lead) => lead.leadUid);
}
