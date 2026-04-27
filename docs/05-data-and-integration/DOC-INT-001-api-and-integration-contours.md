# DOC-INT-001 API и интеграционные контуры

|**Версия**|**Статус**|**Дата создания**|**Дата обновления**|
|---|---|---|---|
|v0.2-test|Draft|2026-04-27|2026-04-27|

О документе: описывает рабочий backend API CRM_14 и связь с 1С.

## 1. Общий подход

API CRM_14 считается рабочим backend API на тестовых данных. Это не просто мок, но учебная реализация без production-контура.

Backend связан с 1С через HTTP-методы. 1С-разработчик настраивает таблицы/базу и методы для связи с Python.

Принятое допущение: endpoints ниже оформлены как тестовая спецификация. Их нужно сверить с фактическим backend перед финальной сдачей.

## 2. Предполагаемые endpoints

### 

### GET

**`/leads`

Назначение: получить список лидов.

Параметры:

- `owner`;
- `source_code`;
- `stage`;
- `date_from`;
- `date_to`;
- `role`.

Ответ:

```json
[
  {
    "id": 1,
    "lead_uid": "a1b2c",
    "title": "Заявка с сайта",
    "notes": "Клиент интересуется услугой",
    "source_code": "website",
    "current_stage": "new",
    "owner": "manager_1"
  }
]
```

### 

### POST

**`/leads`

Назначение: создать лида.

Запрос:

```json
{
  "lead_uid": "x7k91",
  "title": "Новый лид",
  "notes": "Первичный контакт",
  "source_code": "website",
  "owner": "manager_1"
}
```

Ответ `201 Created`:

```json
{
  "id": 25,
  "lead_uid": "x7k91",
  "current_stage": "new",
  "status": "created"
}
```

### 

### PATCH

**`/leads/{id}/stage`

Назначение: изменить стадию лида.

Запрос:

```json
{
  "target_stage": "qualified",
  "comment": "Лид прошёл первичную проверку"
}
```

Ответ:

```json
{
  "lead_id": 25,
  "previous_stage": "new",
  "current_stage": "qualified",
  "status": "updated"
}
```

### 

### GET

**`/leads/{id}/history`

Назначение: получить историю стадий лида.

Ответ:

```json
{
  "lead_id": 25,
  "lead_uid": "x7k91",
  "history": [
    {
      "stage": "new",
      "entered_at": "2026-04-06T10:00:00Z",
      "left_at": "2026-04-06T11:20:00Z",
      "approved": true,
      "comment": "Создан лид"
    },
    {
      "stage": "qualified",
      "entered_at": "2026-04-06T11:20:00Z",
      "left_at": null,
      "approved": true,
      "comment": "Лид квалифицирован"
    }
  ]
}
```

### 

### POST

**`/import`

Назначение: импорт CSV/XLSX.

Ответ:

```json
{
  "imported": 80,
  "skipped_duplicates": 15,
  "invalid_rows": 5,
  "status": "completed"
}
```

### 

### GET

**`/export/excel`

Назначение: экспорт данных в Excel.

Ответ:

```json
{
  "file_name": "crm14_leads_export.xlsx",
  "rows": 100,
  "status": "generated"
}
```

### 

### GET

**`/report/funnel`

Назначение: отчёт по воронке.

Ответ:

```json
{
  "total_leads": 100,
  "conversion": 0.24,
  "stages": {
    "new": 20,
    "qualified": 30,
    "proposal": 25,
    "won": 15,
    "lost": 10
  },
  "avg_stage_duration_hours": {
    "new": 3.4,
    "qualified": 8.2,
    "proposal": 14.7
  }
}
```

### 

### POST

**`/stage-return-requests`

Назначение: запросить возврат стадии.

Принятое допущение: отдельной таблицы возвратов нет, endpoint нужно сверить с реализацией.

Запрос:

```json
{
  "lead_id": 25,
  "target_stage": "new",
  "reason": "Стадия была изменена ошибочно"
}
```

### 

### POST

**`/stage-return-requests/{id}/approve`

Назначение: одобрить возврат стадии.

### 

### POST

**`/stage-return-requests/{id}/reject`

Назначение: отклонить возврат стадии.

## 3. HTTP-статусы

|**Код**|**Ситуация**|
|---|---|
|200|успешное получение или обновление|
|201|лид создан|
|400|ошибка валидации|
|403|действие запрещено для роли|
|404|лид не найден|
|409|дубль `lead_uid`|
|422|некорректный формат данных|
|500|внутренняя ошибка сервера|

## 4. Интеграция с 1С

1С используется как учебный контур хранения/обмена. 1С-разработчик:

- настраивает таблицы / базу;
- создаёт HTTP-методы;
- обеспечивает связь 1С с Python/backend;
- участвует в согласовании структуры данных.

Принятое допущение: нужно уточнить, какие именно объекты 1С созданы: справочник, регистр, документ, обработка или HTTP-сервис.

---
