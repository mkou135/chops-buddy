# web

Thin Next.js client for the Chops Buddy API (DECISIONS #12). Deliberately plain: forms and lists, no design investment.

- `/sign-in`: Supabase email/password; sign-up also creates the API profile with a role.
- `/student`: start a 10/20/30-minute session, log each prescription, see the next state.
- `/student/history`: every session with its logs.
- `/teacher/students`: roster and add-student form.
- `/teacher/student/?id=`: assign targets (units are comma-separated; a triplet is one unit), remove them, read the student's sessions and the validator's verdict on model-planned ones.

Static export (`next build` writes `out/`) deployed to GitHub Pages by `.github/workflows/pages.yml`. Copy `.env.example` to `.env.local` to run against a local API.

```bash
npm install && npm run dev      # http://localhost:3000
npm test                        # vitest
npm run lint && npm run build
```
