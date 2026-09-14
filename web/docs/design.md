# Chops Buddy MVP Design Document

## 1. Product Overview
Chops Buddy is a web-based platform that helps saxophone teachers manage students, assignments, and practice summaries while guiding students through structured practice sessions. The MVP targets saxophone instruction only and is built on a Next.js frontend with Supabase for authentication, data storage, and serverless APIs.

## 2. Goals & Non-Goals
### Goals
- Allow teachers to manually add/manage students.
- Capture teacher availability and track scheduled lessons.
- Enable teachers to assign scale-based homework.
- Generate guided practice sessions that walk students through assigned scales with tuner support.
- Record practice duration and aggregate metrics without storing raw audio.
- Allow students to send follow-up questions on assignments.

### Non-Goals (Future Considerations)
- Automatic student self-registration or guardian roles.
- Third-party calendar integration (Google/Apple).
- Full-length piece assignments (defer due to copyright).
- Advanced analytics beyond total practice time (e.g., intonation scoring) in MVP.
- Audio recording storage.
- Comprehensive mobile apps (focus on mobile-friendly web with optional PWA wrapper).

## 3. Personas & Primary User Journeys
### Teacher (primary MVP persona)
- Create account, set profile, add students.
- Define recurring availability and view schedule.
- Record lesson notes, assign scale homework.
- Review student practice summaries and respond to questions.

### Student
- Log in, review assigned scales.
- Launch guided practice session for each assignment.
- Track practice time, mark completion steps, ask questions.

## 4. Core Flows
1. **Teacher Onboarding**
   - Auth with Supabase, fill profile (instrument specialization, studio info).
   - Create student records manually (name, contact, proficiency, instrument type).
2. **Availability & Scheduling**
   - Teacher sets weekly availability slots (time ranges, weekdays).
   - Teachers book lessons with students or mark availability for manual scheduling.
3. **Assignment Management**
   - Teacher selects student, chooses scale assignment template (key, tempo target).
   - Optionally add notes, due date, and practice time goal.
4. **Guided Practice**
   - Student selects assignment → sees session outline (warm-up, scale reps).
   - Start session: tuner UI validates notes via Web Audio API, practice timer runs.
   - Student marks attempts complete, notes struggles/questions.
5. **Review & Feedback**
   - Practice sessions summarize minutes practiced, attempts completed, student comments.
   - Teacher dashboard highlights recent activity and outstanding questions.

## 5. Information Architecture & Data Model (Supabase)
| Table | Key Fields | Notes |
|-------|------------|-------|
| `profiles` | `id`, `role` (`teacher`/`student`), name, instrument, timezone | Extends Supabase auth users. |
| `students` | `id`, `teacher_id`, `profile_id`, proficiency, notes | Many-to-one with teachers. |
| `availability_slots` | `id`, `teacher_id`, `weekday`, `start_time`, `end_time`, recurrence metadata | Supports recurring weekly slots. |
| `lessons` | `id`, `teacher_id`, `student_id`, `scheduled_at`, `duration`, `status`, `notes` | Connects to availability. |
| `assignments` | `id`, `teacher_id`, `student_id`, `scale_key`, `octave_range`, `tempo_goal`, `due_date`, `notes`, `status` | Scales only in MVP. |
| `practice_sessions` | `id`, `assignment_id`, `student_id`, `started_at`, `ended_at`, `duration_minutes`, `completion_status` | Derived metrics only. |
| `practice_steps` | `id`, `practice_session_id`, `step_type` (warmup, repetition), `metadata` (JSON for tempo targets etc.), `status` | Guides session flow. |
| `practice_metrics` | `practice_session_id`, `metric_type` (time_spent), `value` | Extensible for future metrics. |
| `questions` | `id`, `practice_session_id`, `student_id`, `teacher_id`, `content`, `status`, `response` | Facilitates Q&A. |

Row Level Security ensures teachers view only their students’ data and students only see their own records.

## 6. System Architecture
- **Frontend**: Next.js App Router with TypeScript; React Query/SWR for data fetching; Tailwind or Chakra for UI; PWA configuration for mobile-friendly tuner access.
- **Backend**: Supabase Database + Auth; Supabase Edge Functions for business logic (e.g., assignment creation, summarizing practice sessions).
- **Audio Processing**: Client-side Web Audio API with pitch detection (e.g., YIN/autocorrelation) implemented in a dedicated hook/library. Device permission prompts, fallbacks for unsupported browsers, guidance for mobile Safari/Chrome.
- **State Management**: Minimal global state via React Context (auth profile) and server state via React Query.
- **CI/CD & Maintenance**: GitHub Actions for linting (ESLint), type-checking (TypeScript `tsc --noEmit`), and future unit tests. Prettier formatting enforced via lint-staged & Husky. Documentation stored in `/docs`.

## 7. Page Map & Primary UI Elements

### 7.1 Teacher Experience
| Page | Key Sections | Primary Buttons / Controls |
|------|--------------|----------------------------|
| **Auth Pages** (Sign Up / Login) | Supabase Auth UI, CTA to request student invite | `Create Account`, `Log In`, `Forgot Password` |
| **Teacher Onboarding Wizard** | Profile setup (photo, timezone), studio details | `Save & Continue`, `Skip for now` |
| **Dashboard** | Summary cards (active students, upcoming lessons, practice minutes), recent questions | `Add Student`, `Schedule Lesson`, `Create Assignment`, `Respond` (to questions) |
| **Students List** | Search/filter by name, status | `Add Student`, `View Profile` |
| **Student Detail** | Profile info, lesson history, assignments list, practice log | `Edit Student`, `Add Assignment`, `Message Student` |
| **Availability Management** | Weekly calendar view, list of slots | `Add Availability`, `Edit`, `Delete`, `Copy Week` |
| **Lesson Scheduler** | Calendar interface, slot picker, lesson form | `Schedule`, `Reschedule`, `Cancel Lesson` |
| **Assignment Composer** | Scale selector, parameters (key, tempo, octave, repetitions), due date | `Create Assignment`, `Save Draft`, `Assign Later` |
| **Assignment Detail** | Overview, linked practice sessions, metrics | `Mark Complete`, `Archive`, `Duplicate` |
| **Practice Summary** | Table of sessions, filters (date range) | `Export CSV` (future), `View Session` |
| **Question Inbox** | Threads from students | `Reply`, `Mark Resolved`, `Archive` |
| **Settings** | Profile, notifications, tuner settings, PWA install prompt | `Update Profile`, `Manage Notifications`, `Install App` (PWA prompt) |

### 7.2 Student Experience
| Page | Key Sections | Primary Buttons / Controls |
|------|--------------|----------------------------|
| **Auth Pages** | Supabase magic link or password login | `Log In`, `Request Access` |
| **Student Dashboard** | Assigned scales, upcoming lesson, streak/prompt | `Start Practice`, `View Assignment`, `Ask Question` |
| **Assignment Detail** | Scale instructions, teacher notes, due date, time goal | `Start Guided Session`, `Mark Complete`, `Ask Question` |
| **Guided Practice Session** | Step-by-step interface: tuner readout, metronome, practice timer, progress tracker | `Start Timer`, `Record Attempt`, `Complete Step`, `Pause`, `Finish Session`, `Report Issue` |
| **Practice Log** | Timeline/list of sessions | `View Details`, `Filter by Assignment` |
| **Questions & Messages** | Threaded conversation with teacher | `New Message`, `Attach Recording` (future), `Mark Resolved` |
| **Profile & Settings** | Instrument, goals, device setup tips for tuner | `Update Profile`, `Configure Audio`, `Install App` |

### 7.3 Shared / Global Components
- **Navigation Bar**: Role-based items (Dashboard, Students/Assignments, Practice, Messages, Settings).
- **Notifications Drawer**: Alerts for new assignments, upcoming lessons, responses.
- **Help & Support Modal**: Documentation links, contact form.
- **Mobile Considerations**: Bottom navigation for small screens, large touch targets for tuner controls.

## 8. Guided Practice Feature Design
1. **Session Initialization**: Student selects assignment → fetch scale metadata and predetermined practice steps (e.g., warm-up breath, scale ascending, descending).
2. **Audio Calibration**: Prompt to allow microphone, display input-level meter, allow selection of instrument transposition (alto vs tenor).
3. **Pitch Detection Module**:
   - Real-time frequency analysis with tolerance thresholds per note.
   - Visual feedback: color-coded intonation indicator, note name display.
   - Support for alternate fingerings (future).
4. **Step Tracking & Timer**:
   - Each step includes recommended repetitions/time.
   - Timer records total active practice minutes; idle detection warns if no audio detected.
5. **Session Completion**:
   - Summary modal with total time, steps completed, notes field.
   - Option to send question to teacher.
6. **Data Storage**:
   - Write session record (start/end, duration).
   - Aggregate per-assignment metrics, update teacher dashboard.

## 9. Questions & Messaging
- Inline chat linked to practice sessions for context.
- Email notifications (via Supabase functions/SMTP) optional for new messages.

## 10. Maintenance & Quality
- **Documentation**: `/docs` directory housing this design doc, API specs, setup instructions.
- **Testing Strategy**: Start with unit tests for utility functions, integration tests for critical flows (auth, assignment creation) using Playwright later.
- **Code Quality**: ESLint + Prettier, strict TypeScript, commit hooks.
- **Observability**: Log important events (practice session creation, assignments) to Supabase logs; plan future integration with analytics (e.g., PostHog).
- **Accessibility & UX**: ARIA-friendly controls, keyboard navigation, color contrast compliance, accessible tuner feedback.
- **Security & Privacy**: Supabase RLS policies, audit logging for user actions, secure microphone permissions, privacy policy covering audio processing without storage.

## 11. Rollout Plan
1. Implement Supabase schema and seed with sample data.
2. Build teacher onboarding and student management UI.
3. Develop assignment workflows and guided practice player.
4. Integrate basic practice metrics dashboards.
5. Conduct alpha testing with personal studio; gather feedback.
6. Iterate on tuner accuracy and UI polish; prepare for beta release.

## 12. Future Enhancements
- Gamification (streaks, badges).
- Intonation scoring, rhythm analysis.
- Broader repertoire and exercise library.
- Mobile-native apps if demand requires.
- Multi-instrument support and content marketplace.
