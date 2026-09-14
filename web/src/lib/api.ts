/**
 * Typed client for the FastAPI service. Types mirror api/src/chops_buddy/api/schemas.py.
 * Every call sends the Supabase access token as a Bearer header.
 */

export type Level = "beginner" | "intermediate" | "advanced";
export type InstrumentFamily = "wind" | "brass" | "voice" | "strings" | "keyboard" | "percussion";
export type TargetKind = "scale" | "technique" | "repertoire";
export type Mode = "working" | "isolating" | "chaining" | "mastered";

export type Profile = { id: string; role: "teacher" | "student"; display_name: string };
export type Student = {
  id: string;
  teacher_id: string;
  school_id: string | null;
  display_name: string;
  level: Level;
  instrument_family: InstrumentFamily;
  is_active: boolean;
};
export type TargetState = {
  mode: Mode;
  tempo: number;
  fragment: [number, number];
  chain_base: [number, number];
  chain_len: number;
  fails_here: number;
  mastery_streak: number;
};
export type Target = {
  id: string;
  kind: TargetKind;
  title: string;
  target_tempo: number;
  units: string[];
  phrases: [number, number][] | null;
  start_tempo: number | null;
  threshold_override: number | null;
  position: number;
  is_active: boolean;
  state: TargetState;
};
export type StudentDetail = Student & { targets: Target[] };
export type Prescription = {
  id: string;
  target_id: string;
  mode: Mode;
  fragment: [number, number];
  tempo: number;
  threshold: number;
  minutes: number;
  instruction: string;
};
export type Segment = {
  kind: "long_tones" | TargetKind;
  target_id: string | null;
  prescription: Prescription | null;
  minutes: number;
  instruction: string;
};
export type SessionPlan = { segments: Segment[]; deferred: string[]; plan_hash: string };
export type LogEntry = {
  id: string;
  prescription_id: string;
  tempo_used: number;
  best_consecutive: number;
  break_unit: number | null;
  felt_difficulty: number;
  free_text: string | null;
  state_after: TargetState;
  created_at: string;
};
export type Session = {
  id: string;
  student_id: string;
  duration_minutes: number;
  source: "engine" | "llm";
  plan: SessionPlan;
  created_at: string;
  completed_at: string | null;
  llm_report: { violations: string[]; repaired: boolean; coaching_note: string | null } | null;
  logs: LogEntry[];
};

export type TargetCreate = {
  kind: TargetKind;
  title: string;
  target_tempo: number;
  units: string[];
  phrases?: [number, number][] | null;
  start_tempo?: number | null;
  threshold_override?: number | null;
};
export type LogCreate = {
  prescription_id: string;
  tempo_used: number;
  best_consecutive: number;
  break_unit?: number | null;
  felt_difficulty: number;
  free_text?: string | null;
};

// --- CRM (M6)
export type School = { id: string; name: string; suburb: string | null };
export type Term = { id: string; school_id: string; name: string; starts_on: string; ends_on: string };
export type LessonStatus = "scheduled" | "completed" | "cancelled" | "missed";
export type AttendanceStatus = "present" | "absent" | "late" | "cancelled";
export type Attendance = { status: AttendanceStatus; note: string | null };
export type Lesson = {
  id: string;
  student_id: string;
  student_display_name: string;
  term_id: string | null;
  scheduled_at: string;
  duration_minutes: number;
  status: LessonStatus;
  notes: string;
  attendance: Attendance | null;
};
export type Contact = {
  id: string;
  student_id: string;
  name: string;
  relationship: string;
  phone: string | null;
  email: string | null;
  is_primary: boolean;
};

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(`${status} ${detail}`);
  }
}

export type TokenSource = () => Promise<string | null>;

export function createApi(baseUrl: string, getToken: TokenSource, fetchImpl: typeof fetch = fetch) {
  async function call<T>(method: string, path: string, body?: unknown): Promise<T> {
    const token = await getToken();
    const headers: Record<string, string> = { Accept: "application/json" };
    if (token) headers.Authorization = `Bearer ${token}`;
    if (body !== undefined) headers["Content-Type"] = "application/json";
    const res = await fetchImpl(`${baseUrl}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (res.status === 204) return undefined as T;
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = typeof data?.detail === "string" ? data.detail : JSON.stringify(data?.detail ?? res.statusText);
      throw new ApiError(res.status, detail);
    }
    return data as T;
  }

  return {
    me: () => call<Profile>("GET", "/me"),
    createProfile: (role: Profile["role"], display_name: string) =>
      call<Profile>("POST", "/me/profile", { role, display_name }),
    // teacher
    listStudents: () => call<Student[]>("GET", "/teacher/students"),
    createStudent: (body: { display_name: string; level: Level; instrument_family: InstrumentFamily }) =>
      call<Student>("POST", "/teacher/students", body),
    getStudent: (id: string) => call<StudentDetail>("GET", `/teacher/students/${id}`),
    assignTarget: (studentId: string, body: TargetCreate) =>
      call<Target>("POST", `/teacher/students/${studentId}/targets`, body),
    deactivateTarget: (targetId: string) => call<void>("DELETE", `/teacher/targets/${targetId}`),
    studentHistory: (studentId: string) => call<Session[]>("GET", `/teacher/students/${studentId}/history`),
    updateStudent: (id: string, body: Partial<Pick<Student, "display_name" | "level" | "instrument_family" | "school_id" | "is_active">>) =>
      call<Student>("PATCH", `/teacher/students/${id}`, body),
    // crm
    listSchools: () => call<School[]>("GET", "/teacher/schools"),
    createSchool: (body: { name: string; suburb?: string | null }) => call<School>("POST", "/teacher/schools", body),
    joinSchool: (id: string) => call<void>("POST", `/teacher/schools/${id}/join`),
    schoolStudents: (id: string) => call<Student[]>("GET", `/teacher/schools/${id}/students`),
    listTerms: (schoolId: string) => call<Term[]>("GET", `/teacher/schools/${schoolId}/terms`),
    createTerm: (schoolId: string, body: { name: string; starts_on: string; ends_on: string }) =>
      call<Term>("POST", `/teacher/schools/${schoolId}/terms`, body),
    studentLessons: (studentId: string) => call<Lesson[]>("GET", `/teacher/students/${studentId}/lessons`),
    createLesson: (studentId: string, body: { scheduled_at: string; duration_minutes: number; term_id?: string | null; notes?: string }) =>
      call<Lesson>("POST", `/teacher/students/${studentId}/lessons`, body),
    updateLesson: (id: string, body: Partial<Pick<Lesson, "scheduled_at" | "duration_minutes" | "status" | "notes">>) =>
      call<Lesson>("PATCH", `/teacher/lessons/${id}`, body),
    setAttendance: (id: string, body: Attendance) => call<Lesson>("PUT", `/teacher/lessons/${id}/attendance`, body),
    schedule: (from: string, to: string) => call<Lesson[]>("GET", `/teacher/lessons?from=${from}&to=${to}`),
    listContacts: (studentId: string) => call<Contact[]>("GET", `/teacher/students/${studentId}/contacts`),
    createContact: (studentId: string, body: Omit<Contact, "id" | "student_id">) =>
      call<Contact>("POST", `/teacher/students/${studentId}/contacts`, body),
    deleteContact: (id: string) => call<void>("DELETE", `/teacher/contacts/${id}`),
    // student
    myTargets: () => call<Target[]>("GET", "/me/targets"),
    createSession: (duration_minutes: 10 | 20 | 30) => call<Session>("POST", "/me/sessions", { duration_minutes }),
    submitLog: (body: LogCreate) => call<LogEntry>("POST", "/me/logs", body),
    myHistory: () => call<Session[]>("GET", "/me/history"),
  };
}

export type Api = ReturnType<typeof createApi>;

/** Units covered by a fragment, as labels, for display next to a prescription. */
export function fragmentLabel(units: string[], fragment: [number, number]): string {
  const [start, end] = fragment;
  if (start === 0 && end === units.length) return "whole passage";
  return units.slice(start, end).join(" · ");
}
