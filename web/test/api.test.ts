import { describe, expect, it, vi } from "vitest";

import { ApiError, createApi, fragmentLabel } from "../src/lib/api";

function fakeFetch(status: number, body: unknown) {
  return vi.fn(async () => ({
    status,
    ok: status >= 200 && status < 300,
    statusText: "x",
    json: async () => body,
  })) as unknown as typeof fetch;
}

describe("createApi", () => {
  it("sends the bearer token and JSON body", async () => {
    const f = fakeFetch(201, { id: "s", source: "engine" });
    const api = createApi("https://api.test", async () => "tok", f);
    await api.createSession(20);
    const [url, init] = (f as unknown as { mock: { calls: [string, RequestInit][] } }).mock.calls[0];
    expect(url).toBe("https://api.test/me/sessions");
    expect(init.method).toBe("POST");
    expect((init.headers as Record<string, string>).Authorization).toBe("Bearer tok");
    expect(init.body).toBe(JSON.stringify({ duration_minutes: 20 }));
  });

  it("raises ApiError with the API's detail code", async () => {
    const api = createApi("https://api.test", async () => null, fakeFetch(409, { detail: "nothing_to_practise" }));
    await expect(api.createSession(10)).rejects.toMatchObject({ status: 409, detail: "nothing_to_practise" } satisfies Partial<ApiError>);
  });

  it("treats 204 as void", async () => {
    const api = createApi("https://api.test", async () => "t", fakeFetch(204, undefined));
    await expect(api.deactivateTarget("x")).resolves.toBeUndefined();
  });
});

describe("fragmentLabel", () => {
  const units = ["b1", "b2", "b3-triplet", "b4"];
  it("names the whole passage", () => expect(fragmentLabel(units, [0, 4])).toBe("whole passage"));
  it("lists the units in a fragment", () => expect(fragmentLabel(units, [1, 3])).toBe("b2 · b3-triplet"));
});
