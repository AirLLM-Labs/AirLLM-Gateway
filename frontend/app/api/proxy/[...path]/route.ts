/**
 * Backend-for-frontend proxy.
 *
 * The browser only ever talks to this same-origin route, which forwards to the
 * gateway backend and injects the admin token server-side. This keeps the
 * admin token out of the browser and sidesteps CORS entirely.
 *
 * Example: GET /api/proxy/admin/models -> GET {BACKEND_URL}/admin/models
 */
import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const BACKEND_URL = (
  process.env.BACKEND_INTERNAL_URL ?? "http://localhost:4000"
).replace(/\/$/, "");
const ADMIN_TOKEN = process.env.ADMIN_API_KEY ?? "changeme-admin-key";

async function forward(req: NextRequest, path: string[]): Promise<NextResponse> {
  const search = req.nextUrl.search;
  const target = `${BACKEND_URL}/${path.join("/")}${search}`;

  const headers = new Headers();
  headers.set("X-Admin-Token", ADMIN_TOKEN);
  const contentType = req.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);

  const hasBody = !["GET", "HEAD"].includes(req.method);
  const body = hasBody ? await req.text() : undefined;

  let upstream: Response;
  try {
    upstream = await fetch(target, {
      method: req.method,
      headers,
      body,
      cache: "no-store",
    });
  } catch (err) {
    return NextResponse.json(
      { error: `Cannot reach gateway backend at ${BACKEND_URL}.` },
      { status: 502 },
    );
  }

  // 204 / empty bodies.
  if (upstream.status === 204) {
    return new NextResponse(null, { status: 204 });
  }

  const text = await upstream.text();
  return new NextResponse(text, {
    status: upstream.status,
    headers: {
      "content-type": upstream.headers.get("content-type") ?? "application/json",
    },
  });
}

type Ctx = { params: { path: string[] } };

export async function GET(req: NextRequest, { params }: Ctx) {
  return forward(req, params.path);
}
export async function POST(req: NextRequest, { params }: Ctx) {
  return forward(req, params.path);
}
export async function PUT(req: NextRequest, { params }: Ctx) {
  return forward(req, params.path);
}
export async function DELETE(req: NextRequest, { params }: Ctx) {
  return forward(req, params.path);
}
export async function PATCH(req: NextRequest, { params }: Ctx) {
  return forward(req, params.path);
}
