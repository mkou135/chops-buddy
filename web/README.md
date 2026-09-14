# web

Thin Next.js client for the Chops Buddy API (DECISIONS #12). Deliberately plain: forms and lists, no design investment.

- `/sign-in`: Supabase email/password; sign-up also creates the API profile with a role.
- `/student`: start a 10/20/30-minute session, log each prescription, see the next state.
- `/student/history`: every session with its logs.
- `/teacher/students`: roster and add-student form.
- `/teacher/student/?id=`: assign targets (units are comma-separated; a triplet is one unit), remove them, set the student's school, schedule lessons and mark attendance and notes, manage contacts, read sessions and the validator's verdict on model-planned ones.
- `/teacher/schools`: schools you belong to, join by id, terms per school.
- `/teacher/schedule`: lessons across all students in a date window.

Static export (`next build` writes `out/`) deployed to GitHub Pages by `.github/workflows/pages.yml`. Copy `.env.example` to `.env.local` to run against a local API.

```bash
npm install && npm run dev      # http://localhost:3000
npm test                        # vitest
npm run lint && npm run build
```
