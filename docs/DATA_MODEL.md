# Data model

Status: v1 for M2. Tables for the CRM milestone (M6: lessons, attendance, contacts, terms) are listed in §5 as planned, not migrated.

Principles:
- The engine owns the shape of target state, prescriptions, and plans. Those are stored as JSONB snapshots of the engine's pydantic models, never re-modelled as columns. The engine is the schema for them (DECISIONS #16).
- The API is the only writer. It connects as one role; authorisation is in the service layer (DECISIONS #9).
- Every table has `created_at`; mutable tables also have `updated_at`. All timestamps are `timestamptz`. Primary keys are `uuid` with `gen_random_uuid()`.
- Identity comes from Supabase Auth: `profiles.id` equals `auth.users.id` (the JWT `sub`).

## 1. Identity

### `profiles`
| column | type | notes |
|---|---|---|
| id | uuid PK | Supabase Auth user id (JWT `sub`) |
| role | text | `teacher` or `student` |
| display_name | text | |
| email | text | copied from auth for display |

A student who has not signed in yet has a `students` row with `profile_id` null. Sign-in links the two in M5 (class-code flow).

## 2. Teaching structure

### `schools`
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| name | text | |
| suburb | text null | |

### `school_memberships`
| column | type | notes |
|---|---|---|
| teacher_id | uuid FK profiles | |
| school_id | uuid FK schools | |
| PK | (teacher_id, school_id) | |

### `students`
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| teacher_id | uuid FK profiles | owning teacher; the authorisation anchor in M2 |
| school_id | uuid FK schools null | required from M6 |
| profile_id | uuid FK profiles null unique | set when the student signs in |
| display_name | text | |
| level | text | `beginner`, `intermediate`, `advanced` (engine `Level`) |
| instrument_family | text | engine `InstrumentFamily` |
| is_active | bool | default true |

Index: `(teacher_id, is_active)`.

## 3. Practice

### `targets`
One assigned thing to practise. Mirrors engine `Target` plus ownership.

| column | type | notes |
|---|---|---|
| id | uuid PK | |
| student_id | uuid FK students | |
| kind | text | `scale`, `technique`, `repertoire` |
| title | text | |
| target_tempo | int | 20–300 |
| units | jsonb | `list[str]`, at least one |
| phrases | jsonb null | `list[[start, end]]` |
| start_tempo | int null | |
| threshold_override | int null | 3–10 |
| position | int | assignment order; drives E-50 within-kind order |
| is_active | bool | deactivating a target removes it from sessions; re-assigning creates a new row (E-47 reset) |
| created_by | uuid FK profiles | |

Index: `(student_id, is_active, position)`.

### `target_states`
| column | type | notes |
|---|---|---|
| target_id | uuid PK FK targets | |
| state | jsonb | engine `TargetState` |
| version | int | incremented on every `apply`; optimistic concurrency for log submission |
| updated_at | timestamptz | |

### `practice_sessions`
| column | type | notes |
|---|---|---|
| id | uuid PK | |
| student_id | uuid FK students | |
| duration_minutes | int | 10, 20, 30 |
| plan | jsonb | engine `SessionPlan` |
| plan_hash | text | E-70, denormalised for querying |
| source | text | `engine` or `llm` (DoD A4) |
| completed_at | timestamptz null | set when every prescription has a log entry |

Index: `(student_id, created_at desc)`.

### `prescriptions`
One row per engine `Prescription` issued in a session. Log entries reference this id (E-21).

| column | type | notes |
|---|---|---|
| id | uuid PK | the id the engine was given by the API |
| session_id | uuid FK practice_sessions | |
| target_id | uuid FK targets | |
| position | int | segment order |
| snapshot | jsonb | engine `Prescription` |

### `log_entries`
The student's self-report. Mirrors engine `LogEntry`.

| column | type | notes |
|---|---|---|
| id | uuid PK | |
| prescription_id | uuid FK prescriptions unique | one entry per prescription |
| student_id | uuid FK students | denormalised for history queries |
| tempo_used | int | |
| best_consecutive | int | |
| break_unit | int null | |
| felt_difficulty | int | 1–5 |
| free_text | text null | ≤500 chars; read by the LLM layer only |
| state_after | jsonb | `TargetState` after `apply`, for history and evals |

## 4. Write paths

- **Assign**: insert `targets` + `target_states` with `initial_state()` in one transaction.
- **Next session**: load active targets and states → `compose()` with ids minted by the API → insert `practice_sessions` + `prescriptions`. With the LLM layer enabled (M3), the proposal is validated first and `source` records which won.
- **Log**: load prescription snapshot and current state → `apply()` → update `target_states` (checking `version`) → insert `log_entries` with `state_after`.

## 5. Planned for M6 (not migrated yet)

`terms` (school_id, name, starts_on, ends_on), `lessons` (student_id, teacher_id, term_id, scheduled_at, duration_minutes, status, notes), `attendance` (lesson_id, status, note), `contacts` (student_id, name, relationship, phone, email, is_primary).
