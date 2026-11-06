/**
 * Calculator ratings: an aggregate count and average per calculator.
 *
 * Deliberately aggregate-only. We store a count, a total and one bucket per
 * score, and nothing that identifies a visitor. "Your rating" is remembered in
 * the visitor's own browser by `public/site/rating.js`, so the server never
 * needs to know who is asking. That keeps the privacy policy true: a rating is
 * the only thing that leaves the browser, and it leaves with no name attached.
 *
 * An edit is expressed by the client sending the score it is replacing
 * (`prev`). The server moves the total by the difference and leaves the count
 * alone, which is what makes a second tap an edit rather than a second vote.
 *
 * Storage is Upstash Redis over REST, so the route needs no client library.
 * Two variables are read, both injected by the Vercel-Upstash integration:
 * KV_REST_API_URL and KV_REST_API_TOKEN.
 */

const TOOL_ID = /^[a-z0-9][a-z0-9-]{0,79}$/
const STARS = 5

// A write cap per network per hour. Ratings are anonymous, so this is the only
// thing between a script and a skewed average. Deliberately generous: a shared
// office or campus NAT must not be locked out.
const WRITE_LIMIT = 30

function env(name: string): string {
  const v = process.env[name]
  if (!v) throw new Error(`${name} is not set`)
  return v
}

function headers() {
  return {
    Authorization: `Bearer ${env('KV_REST_API_TOKEN')}`,
    'Content-Type': 'application/json',
  }
}

/** Run Upstash commands in one round trip. Returns the `result` of each. */
async function redis(commands: (string | number)[][]): Promise<unknown[]> {
  const res = await fetch(`${env('KV_REST_API_URL')}/pipeline`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify(commands),
    cache: 'no-store',
  })
  if (!res.ok) throw new Error(`redis ${res.status}`)
  const data = (await res.json()) as { result?: unknown; error?: string }[]
  return data.map((d) => d.result)
}

/** A short-lived counter keyed by the caller's network, never by the caller. */
async function underWriteLimit(ip: string): Promise<boolean> {
  const hour = Math.floor(Date.now() / 3_600_000)
  const key = `rl:${ip}:${hour}`
  const [used] = await redis([['INCR', key]])
  if (Number(used) === 1) await redis([['EXPIRE', key, 7200]])
  return Number(used) <= WRITE_LIMIT
}

function callerIp(request: Request): string {
  const forwarded = request.headers.get('x-forwarded-for') || ''
  return forwarded.split(',')[0].trim() || 'unknown'
}

/** The seven keys that hold one calculator's tally, in a fixed order. */
function tallyKeys(tool: string): string[] {
  const keys = [`rat:${tool}:count`, `rat:${tool}:sum`]
  for (let i = 1; i <= STARS; i++) keys.push(`rat:${tool}:b${i}`)
  return keys
}

function payload(values: unknown[]) {
  const count = Number(values[0]) || 0
  const sum = Number(values[1]) || 0
  const buckets: number[] = []
  for (let i = 0; i < STARS; i++) buckets.push(Number(values[2 + i]) || 0)
  return {
    count,
    // One decimal, computed from the integers, so a rounded display can never
    // drift from the stored total.
    average: count ? Math.round((sum / count) * 10) / 10 : 0,
    distribution: buckets,
  }
}

export async function GET(request: Request) {
  const tool = new URL(request.url).searchParams.get('tool') || ''
  if (!TOOL_ID.test(tool)) {
    return Response.json({ error: 'bad tool id' }, { status: 400 })
  }
  try {
    const values = await redis([['MGET', ...tallyKeys(tool)]])
    return Response.json(payload(values), {
      headers: { 'cache-control': 'no-store' },
    })
  } catch {
    return Response.json({ count: 0, average: 0, unavailable: true })
  }
}

export async function POST(request: Request) {
  let body: { tool?: unknown; stars?: unknown; prev?: unknown }
  try {
    body = await request.json()
  } catch {
    return Response.json({ error: 'bad body' }, { status: 400 })
  }

  const tool = String(body.tool || '')
  const stars = Number(body.stars)
  const prev = Number(body.prev) || 0

  if (!TOOL_ID.test(tool) || !Number.isInteger(stars) || stars < 1 || stars > STARS) {
    return Response.json({ error: 'bad rating' }, { status: 400 })
  }

  const key = `rat:${tool}`
  const editing = prev >= 1 && prev <= STARS && prev !== stars
  const commands: (string | number)[][] = []

  if (editing) {
    // A move: the total shifts, the count does not.
    commands.push(['INCRBY', `${key}:sum`, stars - prev])
    commands.push(['INCRBY', `${key}:b${prev}`, -1])
    commands.push(['INCRBY', `${key}:b${stars}`, 1])
  } else if (!prev) {
    commands.push(['INCRBY', `${key}:sum`, stars])
    commands.push(['INCRBY', `${key}:count`, 1])
    commands.push(['INCRBY', `${key}:b${stars}`, 1])
  }

  try {
    if (!(await underWriteLimit(callerIp(request)))) {
      return Response.json({ error: 'too many' }, { status: 429 })
    }
    if (commands.length) await redis(commands)
    const values = await redis([['MGET', ...tallyKeys(tool)]])
    return Response.json(
      { ...payload(values), changed: editing, rereview: !editing && Boolean(prev) },
      { headers: { 'cache-control': 'no-store' } },
    )
  } catch {
    return Response.json({ error: 'unavailable' }, { status: 503 })
  }
}
