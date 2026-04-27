# DOC-STD-001 Правила именования и версионирования

|**Версия**|**Статус**|**Дата создания**|**Дата обновления**|
|---|---|---|---|
|v0.2-test|Draft|2026-04-27|2026-04-27|

О документе: описывает правила оформления документации CRM_14.

## 1. Код документа

Формат:

```text
DOC-AREA-NNN-document-name.md
```

Примеры:

```text
DOC-GOV-001-project-charter.md
DOC-REQ-001-user-stories-and-moscow.md
DOC-DAT-001-logical-data-model-and-erd.md
```

## 2. Версии

Используются версии:

- `v0.1` — первичная версия;
- `v0.2-test` — тестовая сборка документации;
- `v1.0` — финальная версия для сдачи.

## 3. Статусы

- Draft;
- Test documentation;
- Final draft;
- Final.

## 4. Пометки спорных мест

Все спорные или требующие проверки места отмечаются так:

```html
Принятое допущение: описание, что нужно проверить.
```

Даты, требующие ручной замены:

```html
2026-...
```

## 5. Правила содержания

- не добавлять таблицы БД, которых нет в схеме;
- не писать, что есть полноценная авторизация;
- явно указывать учебный характер проекта;
- не включать персональные данные;
- отделять Must Have от Should/Could;
- фиксировать бизнес-правила движения стадий;
- сверять документацию с презентацией и демо.

---

# Приложение A. Сводка бизнес-правил

## BR-001. Порядок стадий

```text
new → qualified → proposal → won/lost
```

## BR-002. Запрет пропуска стадий

Нельзя перевести лид из `new` сразу в `proposal`.

## BR-003. Завершение только из proposal

Перевод в `won` или `lost` возможен только из `proposal`.

## BR-004. Возврат назад

Возврат на предыдущую стадию возможен только через запрос и одобрение РОП.

## BR-005. Отклонение возврата

Если РОП отклоняет возврат, заявка удаляется или закрывается, а стадия лида не меняется.

Принятое допущение: если в реализации заявка не удаляется, а получает статус rejected, формулировку нужно поправить.

## BR-006. Менеджер видит только своих лидов

Менеджер не имеет доступа к чужим лидам.

## BR-007. Аналитик только смотрит

Аналитик не создаёт, не редактирует и не переводит лиды.

## BR-008. РОП имеет полный доступ

РОП видит все лиды и может управлять стадиями.

## BR-009. Дубли импорта

Дубликаты определяются по `lead_uid` и пропускаются.

## BR-010. Закрытые лиды

Закрытые лиды `won/lost` можно редактировать.

Принятое допущение: пользователь указал, что закрытые лиды можно редактировать. В финальной версии стоит проверить, как именно это реализовано в интерфейсе.

---

# Приложение B. Тестовая DBML-схема

```dbml
Project mini_crm_simple {
  database_type: "PostgreSQL"
}

enum users {
  manager_1
  manager_2
  sales_head
}

enum lead_stage {
  new
  qualified
  proposal
  won
  lost
}

enum sources_code {
  advertisement
  website
  recommendation
  event
  other
}

Table leads {
  id bigserial [pk]
  lead_uid unique
  source_code sources_code [not null]
  current_stage lead_stage [not null, default: 'new']
  owner users [not null]

  title varchar(255)
  notes text
}

Table leads_stage {
  id bigserial [pk]
  lead_id bigint [not null, ref: > leads.id]
  stage lead_stage [not null]
  entered_at timestamptz [not null]
  left_at timestamptz
  approved bool [default: true]

  indexes {
    (lead_id, entered_at)
    (lead_id, stage, entered_at) [unique]
  }

  Note: "Это lead_stages из ТЗ: (lead_id, stage, entered_at, left_at)."
}

Table leads_comments {
  id bigserial [pk]
  stage_event_id bigint [not null, ref: > leads_stage.id] 
  author users [not null] 
  comment text

  indexes {
    (stage_event_id) [unique]
  }

  Note: "Комментарий при смене стадии. Можно хранить пустым, если у вас это необязательно."
}
```

---

# Приложение C. Что нужно проверить вручную перед финальной версией

1. 2026-04-03 — точная дата начала.
2. 2026-04-05 — дата CP1.
3. 2026-04-12 — дата CP2.
4. 2026-04-20 — дата CP3.
5. 2026-05-01 — дата финальной сдачи.
6. Принятое допущение: db implementation — как именно соотносятся PostgreSQL, 1С и backend.
7. Принятое допущение: api fact — фактические endpoints.
8. Принятое допущение: return implementation — где хранится заявка возврата.
9. Принятое допущение: created at — есть ли дата создания лида.
10. Принятое допущение: kanban dnd — есть ли drag-and-drop.
11. Принятое допущение: 1c details — какие объекты реально сделаны в 1С.
12. Принятое допущение: performance threshold — точный порог времени отчёта.
13. Принятое допущение: import manager — кто реально может импортировать.
14. Принятое допущение: team roles — финальное распределение ролей.
15. Принятое допущение: closed leads edit — как редактируются закрытые лиды.

---
