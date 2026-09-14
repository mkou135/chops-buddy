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
