# DOC-DAT-001 Логическая модель данных и ERD

|**Версия**|**Статус**|**Дата создания**|**Дата обновления**|
|---|---|---|---|
|v0.2-test|Draft|2026-04-27|2026-04-27|

О документе: описывает логическую модель данных CRM_14 на основе схемы `mini_crm_simple`.

Для кого: для аналитика, backend, 1С-разработчика, frontend и преподавателя.

## 1. Назначение модели

Модель данных нужна, чтобы хранить:

- карточки лидов;
- текущие стадии;
- историю прохождения стадий;
- комментарии к событиям стадий;
- владельца лида;
- источник лида.

## 2. Тип БД

```text
Project mini_crm_simple {
  database_type: "PostgreSQL"
}
```

Принятое допущение: в презентации также указан 1С-контур. В документации PostgreSQL описывает логическую структуру данных, а 1С используется как учебная реализация/контур обмена.

## 

## 3. Enum

**`users`

```text
enum users {
  manager_1
  manager_2
  sales_head
}
```

Назначение: фиксирует пользователей, которые могут быть владельцами лидов или авторами комментариев.

|**Значение**|**Описание**|
|---|---|
|`manager_1`|менеджер 1|
|`manager_2`|менеджер 2|
|`sales_head`|руководитель отдела продаж|

Аналитик в текущей БД не хранится как значение enum, потому что он не является владельцем лида.

## 

## 4. Enum

**`lead_stage`

```text
enum lead_stage {
  new
  qualified
  proposal
  won
  lost
}
```

Назначение: фиксирует стадии воронки продаж.

|**Значение**|**Описание**|
|---|---|
|`new`|новый лид|
|`qualified`|квалифицированный лид|
|`proposal`|предложение|
|`won`|выигранный лид|
|`lost`|потерянный лид|

## 

## 5. Enum

**`sources_code`

```text
enum sources_code {
  advertisement
  website
  recommendation
  event
  other
}
```

Назначение: фиксирует источник поступления лида.

|**Значение**|**Описание**|
|---|---|
|`advertisement`|реклама|
|`website`|сайт|
|`recommendation`|рекомендация|
|`event`|мероприятие|
|`other`|другое|

## 

## 6. Таблица

**`leads`

```text
Table leads {
  id bigserial [pk]
  lead_uid unique
  source_code sources_code [not null]
  current_stage lead_stage [not null, default: 'new']
  owner users [not null]

  title varchar(255)
  notes text
}
```

Назначение: основная карточка лида.

|**Поле**|**Тип**|**Обязательность**|**Описание**|
|---|---|---|---|
|`id`|bigserial|да|внутренний первичный ключ|
|`lead_uid`|unique|да|внешний короткий ID для интерфейса и импорта|
|`source_code`|sources_code|да|источник лида|
|`current_stage`|lead_stage|да|текущая стадия, по умолчанию `new`|
|`owner`|users|да|владелец лида|
|`title`|varchar(255)|нет|название лида|
|`notes`|text|нет|заметки по лиду|

`lead_uid` — внешний короткий идентификатор для интерфейса и импорта. В тестовых данных он представляет собой случайный код из строчных символов и цифр, примерно пятизначный.

Принятое допущение: точный формат lead_uid нужно сверить с фактической реализацией. В тестовой версии описан короткий случайный код.

## 

## 7. Таблица

**`leads_stage`

```text
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
```

Назначение: история прохождения стадий.

|**Поле**|**Тип**|**Обязательность**|**Описание**|
|---|---|---|---|
|`id`|bigserial|да|первичный ключ события стадии|
|`lead_id`|bigint|да|ссылка на `leads.id`|
|`stage`|lead_stage|да|стадия|
|`entered_at`|timestamptz|да|время входа в стадию|
|`left_at`|timestamptz|нет|время выхода из стадии|
|`approved`|bool|нет|признак подтверждения события, по умолчанию `true`|

Индексы:

- `(lead_id, entered_at)` — быстрый поиск истории лида;
- `(lead_id, stage, entered_at) unique` — защита от дублей событий.

## 

## 8. Таблица

**`leads_comments`

```text
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

Назначение: комментарий к событию смены стадии.

|**Поле**|**Тип**|**Обязательность**|**Описание**|
|---|---|---|---|
|`id`|bigserial|да|первичный ключ комментария|
|`stage_event_id`|bigint|да|ссылка на `leads_stage.id`|
|`author`|users|да|автор комментария|
|`comment`|text|нет|текст комментария|

Комментарий не является обязательным.

## 9. Связи

|**Связь**|**Тип**|**Описание**|
|---|---|---|
|`leads.id → leads_stage.lead_id`|1:N|один лид имеет много событий стадий|
|`leads_stage.id → leads_comments.stage_event_id`|1:0..1|одно событие стадии может иметь один комментарий|
|`leads.owner → users`|enum|владелец лида|
|`leads.source_code → sources_code`|enum|источник лида|
|`leads.current_stage → lead_stage`|enum|текущая стадия|
|`leads_stage.stage → lead_stage`|enum|стадия в истории|

## 10. Что не добавляем в БД

По уточнению команды, в текущую модель не добавляются:

- таблица `sources`;
- таблица `users`;
- таблица `stage_return_requests`;
- таблица `imports`;
- поле `created_at` в `leads`;
- поле `updated_at` в `leads`;
- поле `created_by`;
- телефон клиента;
- email клиента;
- сумма сделки;
- название компании клиента;
- отдельная причина потери.

Причина потери может быть записана как комментарий, если это нужно в сценарии.

---
