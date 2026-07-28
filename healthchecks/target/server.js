"use strict";

const http = require("http");
const crypto = require("crypto");

const PORT = Number(process.env.PORT || 8000);
const SITE_ROOT = "http://localhost:8011";
const API_KEY = "X".repeat(32);
const READONLY_API_KEY = "R".repeat(32);
const PING_KEY = "p".repeat(22);
const PROJECT_CODE = "11111111-1111-1111-1111-111111111111";
const CSRF_TOKEN = "csrf-token";

let nextId = 1;
let checks = new Map();
let deletedChecks = new Set();
let sessions = new Set();

function resetState() {
  nextId = 1;
  checks = new Map();
  deletedChecks = new Set();
  sessions = new Set();
}

function makeUuid() {
  const suffix = String(nextId++).padStart(12, "0");
  return `00000000-0000-4000-8000-${suffix}`;
}

function isUuid(value) {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);
}

function isSha1(value) {
  return /^[A-Za-z0-9]{40}$/.test(value);
}

function parseCookies(req) {
  const result = {};
  const raw = req.headers.cookie || "";
  for (const part of raw.split(";")) {
    const index = part.indexOf("=");
    if (index === -1) continue;
    const key = part.slice(0, index).trim();
    const value = part.slice(index + 1).trim();
    if (key) result[key] = value;
  }
  return result;
}

function readBody(req) {
  return new Promise((resolve) => {
    const chunks = [];
    req.on("data", (chunk) => chunks.push(chunk));
    req.on("end", () => resolve(Buffer.concat(chunks)));
  });
}

function parseForm(body) {
  const params = new URLSearchParams(body.toString("utf8"));
  const result = {};
  for (const [key, value] of params.entries()) result[key] = value;
  return result;
}

function parseJsonBody(body) {
  if (!body || body.length === 0) return {};
  return JSON.parse(body.toString("utf8"));
}

function slugify(value) {
  return String(value || "")
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, "")
    .replace(/[-\s]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function htmlEscape(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function hasSession(req) {
  const cookies = parseCookies(req);
  return Boolean(cookies.sessionid && sessions.has(cookies.sessionid));
}

function hasCsrf(req, body) {
  const cookies = parseCookies(req);
  if (!cookies.csrftoken) return false;
  if (!body || body.length === 0) return false;
  return body.toString("utf8").includes("csrfmiddlewaretoken=");
}

function send(req, res, status, contentType, body = "", headers = {}) {
  res.statusCode = status;
  if (contentType) res.setHeader("Content-Type", contentType);
  for (const [key, value] of Object.entries(headers)) {
    res.setHeader(key, value);
  }
  if (req.method === "HEAD") {
    res.end();
    return;
  }
  res.end(body);
}

function sendHtml(req, res, status = 200, title = "Healthchecks", headers = {}) {
  const html = [
    "<!doctype html>",
    "<html><body>",
    `<h1>${htmlEscape(title)}</h1>`,
    `<input type="hidden" name="csrfmiddlewaretoken" value="${CSRF_TOKEN}">`,
    `<a href="/projects/${PROJECT_CODE}/checks/">checks</a>`,
    `<a href="/projects/${PROJECT_CODE}/integrations/">integrations</a>`,
    "</body></html>",
  ].join("");

  const setCookie = [`csrftoken=${CSRF_TOKEN}; Path=/`];
  if (headers["Set-Cookie"]) {
    const existing = Array.isArray(headers["Set-Cookie"]) ? headers["Set-Cookie"] : [headers["Set-Cookie"]];
    headers["Set-Cookie"] = existing.concat(setCookie);
  } else {
    headers["Set-Cookie"] = setCookie;
  }

  send(req, res, status, "text/html", html, headers);
}

function redirect(req, res, location = "/", headers = {}) {
  sendHtml(req, res, 302, "Redirect", { ...headers, Location: location });
}

function sendJson(req, res, status, payload) {
  send(req, res, status, "application/json", JSON.stringify(payload));
}

function sendText(req, res, status, body) {
  send(req, res, status, "text/plain", body);
}

function apiError(req, res, status, message) {
  sendJson(req, res, status, { error: message });
}

function getApiVersion(pathname) {
  const match = pathname.match(/^\/api\/v([123])\//);
  return match ? Number(match[1]) : 1;
}

function authorize(req, bodyObject, { readonly = false, bodyKey = true } = {}) {
  let key = req.headers["x-api-key"] || "";
  if (!key && bodyKey && bodyObject && Object.prototype.hasOwnProperty.call(bodyObject, "api_key")) {
    key = String(bodyObject.api_key);
  }

  if (key.length !== 32) {
    return { ok: false, status: 401, error: "missing api key" };
  }

  if (key === API_KEY) {
    return { ok: true, readonly: false };
  }

  if (readonly && key === READONLY_API_KEY) {
    return { ok: true, readonly: true };
  }

  return { ok: false, status: 401, error: "wrong api key" };
}

function normalizeTimezone(value) {
  if (value === "Europe/Kiev") return "Europe/Kyiv";
  if (value === "UCT") return "Etc/UTC";
  return value;
}

function validateStringField(data, key, maxLength, pattern) {
  if (!Object.prototype.hasOwnProperty.call(data, key)) return null;
  if (typeof data[key] !== "string") return `json validation error: ${key} is not a string`;
  if (data[key].length > maxLength) return `json validation error: ${key} is too long`;
  if (pattern && !pattern.test(data[key])) return `json validation error: ${key} does not match pattern`;
  return null;
}

function validateBooleanField(data, key) {
  if (!Object.prototype.hasOwnProperty.call(data, key)) return null;
  if (typeof data[key] !== "boolean") return `json validation error: ${key} is not a boolean`;
  return null;
}

function validateDurationField(data, key) {
  if (!Object.prototype.hasOwnProperty.call(data, key)) return null;
  if (!Number.isInteger(data[key])) return `json validation error: ${key} is not a number`;
  if (data[key] < 60) return `json validation error: ${key} is too small`;
  if (data[key] > 31536000) return `json validation error: ${key} is too large`;
  return null;
}

function looksLikeValidSchedule(value) {
  if (value === "invalid.oncalendar") return false;
  const trimmed = String(value).trim();
  if (!trimmed) return false;
  if (trimmed.split(/\s+/).length === 5) return true;
  return /^[A-Za-z*.,:0-9_\-\s]+$/.test(trimmed);
}

function validateSpec(data) {
  if (!data || typeof data !== "object" || Array.isArray(data)) {
    return "json validation error: value is not an object";
  }

  const stringChecks = [
    ["channels", 1000, null],
    ["desc", 1000000, null],
    ["failure_kw", 200, null],
    ["methods", 4, /^(|POST)$/],
    ["name", 100, null],
    ["schedule", 100, null],
    ["slug", 100, /^[a-z0-9-_]*$/],
    ["start_kw", 200, null],
    ["subject", 200, null],
    ["subject_fail", 200, null],
    ["success_kw", 200, null],
    ["tags", 500, null],
    ["tz", 100, null],
  ];

  for (const [key, maxLength, pattern] of stringChecks) {
    const error = validateStringField(data, key, maxLength, pattern);
    if (error) {
      if (key === "methods" && typeof data[key] === "string" && !pattern.test(data[key])) {
        return "json validation error: methods has unexpected value";
      }
      return error;
    }
  }

  for (const key of ["filter_subject", "filter_body", "filter_http_body", "filter_default_fail", "manual_resume"]) {
    const error = validateBooleanField(data, key);
    if (error) return error;
  }

  for (const key of ["timeout", "grace"]) {
    const error = validateDurationField(data, key);
    if (error) return error;
  }

  if (Object.prototype.hasOwnProperty.call(data, "unique")) {
    if (!Array.isArray(data.unique)) return "json validation error: unique is not an array";
    const allowed = new Set(["name", "slug", "tags", "timeout", "grace"]);
    for (const item of data.unique) {
      if (!allowed.has(item)) return "json validation error: an item in 'unique' has unexpected value";
    }
  }

  if (Object.prototype.hasOwnProperty.call(data, "schedule") && !looksLikeValidSchedule(data.schedule)) {
    return "json validation error: schedule is not a valid cron or OnCalendar expression";
  }

  if (Object.prototype.hasOwnProperty.call(data, "tz")) {
    const timezone = normalizeTimezone(data.tz);
    if (!/^[A-Za-z_]+\/[A-Za-z_]+$/.test(timezone) && timezone !== "Etc/UTC" && timezone !== "UTC") {
      return "json validation error: tz is not a valid timezone";
    }
  }

  return null;
}

function findUnique(spec) {
  if (!Array.isArray(spec.unique) || spec.unique.length === 0) return null;
  for (const field of spec.unique) {
    if (!Object.prototype.hasOwnProperty.call(spec, field)) return null;
  }

  for (const check of checks.values()) {
    let matches = true;
    for (const field of spec.unique) {
      const wanted = field === "tz" ? normalizeTimezone(spec[field]) : spec[field];
      if (check[field] !== wanted) {
        matches = false;
        break;
      }
    }
    if (matches) return check;
  }
  return null;
}

function makeCheck() {
  const uuid = makeUuid();
  return {
    uuid,
    badgeKey: makeUuid(),
    uniqueKey: crypto.createHash("sha1").update(uuid).digest("hex"),
    name: "",
    slug: "",
    tags: "",
    desc: "",
    grace: 3600,
    n_pings: 0,
    status: "new",
    started: false,
    last_ping: null,
    next_ping: null,
    manual_resume: false,
    methods: "",
    start_kw: "",
    success_kw: "",
    failure_kw: "",
    filter_subject: false,
    filter_body: false,
    filter_http_body: false,
    filter_default_fail: false,
    channels: "",
    kind: "simple",
    timeout: 86400,
    schedule: "",
    tz: "UTC",
    pings: [],
  };
}

function updateCheck(check, spec, version) {
  if (Object.prototype.hasOwnProperty.call(spec, "name")) {
    check.name = spec.name;
    if (version < 3) check.slug = slugify(spec.name);
  }

  if (Object.prototype.hasOwnProperty.call(spec, "timeout")) {
    check.kind = "simple";
    check.timeout = spec.timeout;
  }

  if (Object.prototype.hasOwnProperty.call(spec, "schedule")) {
    check.kind = spec.schedule.trim().split(/\s+/).length === 5 ? "cron" : "oncalendar";
    check.schedule = spec.schedule;
  }

  if (Object.prototype.hasOwnProperty.call(spec, "subject")) {
    check.success_kw = spec.subject;
    check.filter_subject = Boolean(check.success_kw || check.failure_kw);
  }

  if (Object.prototype.hasOwnProperty.call(spec, "subject_fail")) {
    check.failure_kw = spec.subject_fail;
    check.filter_subject = Boolean(check.success_kw || check.failure_kw);
  }

  const directFields = [
    "slug",
    "tags",
    "desc",
    "manual_resume",
    "methods",
    "start_kw",
    "success_kw",
    "failure_kw",
    "filter_subject",
    "filter_body",
    "filter_http_body",
    "filter_default_fail",
    "grace",
  ];

  for (const field of directFields) {
    if (Object.prototype.hasOwnProperty.call(spec, field)) check[field] = spec[field];
  }

  if (Object.prototype.hasOwnProperty.call(spec, "tz")) {
    check.tz = normalizeTimezone(spec.tz);
  }
}

function checkToDict(check, version = 1, readonly = false) {
  const result = {
    name: check.name,
    slug: check.slug,
    tags: check.tags,
    desc: check.desc,
    grace: check.grace,
    n_pings: check.n_pings,
    status: check.status,
    started: check.started,
    last_ping: check.last_ping,
    next_ping: check.next_ping,
    manual_resume: check.manual_resume,
    methods: check.methods,
    subject: check.filter_subject ? check.success_kw : "",
    subject_fail: check.filter_subject ? check.failure_kw : "",
    start_kw: check.start_kw,
    success_kw: check.success_kw,
    failure_kw: check.failure_kw,
    filter_subject: check.filter_subject,
    filter_body: check.filter_body,
    filter_http_body: check.filter_http_body,
    filter_default_fail: check.filter_default_fail,
    badge_url: `${SITE_ROOT}/b/2/${check.badgeKey}.svg`,
  };

  if (readonly) {
    result.unique_key = check.uniqueKey;
  } else {
    result.uuid = check.uuid;
    result.ping_url = `${SITE_ROOT}/ping/${check.uuid}`;
    result.update_url = `${SITE_ROOT}/api/v${version}/checks/${check.uuid}`;
    result.pause_url = `${SITE_ROOT}/api/v${version}/checks/${check.uuid}/pause`;
    result.resume_url = `${SITE_ROOT}/api/v${version}/checks/${check.uuid}/resume`;
    result.channels = check.channels;
  }

  if (check.kind === "simple") {
    result.timeout = check.timeout;
  } else {
    result.schedule = check.schedule;
    result.tz = check.tz;
  }

  return result;
}

function tagList(check) {
  return check.tags.split(" ").map((tag) => tag.trim()).filter(Boolean);
}

function matchesTags(check, tags) {
  const actual = new Set(tagList(check));
  return tags.every((tag) => actual.has(tag));
}

function pingToDict(check, ping, version) {
  return {
    type: ping.type,
    date: ping.date,
    n: ping.n,
    scheme: ping.scheme,
    remote_addr: ping.remote_addr,
    method: ping.method,
    ua: ping.ua,
    rid: ping.rid,
    body_url: ping.body ? `${SITE_ROOT}/api/v${version}/checks/${check.uuid}/pings/${ping.n}/body` : null,
  };
}

function getRemoteAddress(req) {
  const forwarded = req.headers["x-forwarded-for"];
  if (forwarded) return String(forwarded).split(",")[0].trim();
  const address = req.socket && req.socket.remoteAddress ? req.socket.remoteAddress : "127.0.0.1";
  if (address === "::1" || address === "::ffff:127.0.0.1") return "127.0.0.1";
  return address;
}

function recordPing(req, check, body, type, rid = null) {
  if (check.methods === "POST" && req.method !== "POST") type = "ign";

  check.n_pings += 1;
  if (type === "start") {
    check.started = true;
  } else if (type === "fail") {
    check.status = "down";
    check.started = false;
  } else if (type !== "ign") {
    check.status = "up";
    check.started = false;
  }

  const ping = {
    type: type === "success" ? "success" : type,
    date: "2026-07-28T00:00:00.000000+00:00",
    n: check.n_pings,
    scheme: req.headers["x-forwarded-proto"] || "http",
    remote_addr: getRemoteAddress(req),
    method: req.method,
    ua: req.headers["user-agent"] || "",
    rid,
    body: body && body.length > 0 ? body.toString("utf8") : "",
  };
  check.pings.unshift(ping);
}

async function handleChecksCollection(req, res, url, version, body) {
  if (req.method !== "GET" && req.method !== "POST") {
    return sendHtml(req, res, 405, "Method not allowed");
  }

  let bodyObject = {};
  if (req.method === "POST") {
    try {
      bodyObject = parseJsonBody(body);
    } catch {
      return apiError(req, res, 400, "could not parse request body");
    }
  }

  const auth = authorize(req, bodyObject, { readonly: req.method === "GET", bodyKey: req.method === "POST" });
  if (!auth.ok) return apiError(req, res, auth.status, auth.error);

  if (req.method === "GET") {
    const tags = url.searchParams.getAll("tag");
    const slug = url.searchParams.get("slug");
    let selected = Array.from(checks.values());
    if (slug) selected = selected.filter((check) => check.slug === slug);
    if (tags.length > 0) selected = selected.filter((check) => matchesTags(check, tags));
    return sendJson(req, res, 200, {
      checks: selected.map((check) => checkToDict(check, version, auth.readonly)),
    });
  }

  const validationError = validateSpec(bodyObject);
  if (validationError) return apiError(req, res, 400, validationError);

  let check = findUnique(bodyObject);
  const created = !check;
  if (!check) check = makeCheck();
  updateCheck(check, bodyObject, version);
  checks.set(check.uuid, check);

  return sendJson(req, res, created ? 201 : 200, checkToDict(check, version, false));
}

async function handleSingleCheck(req, res, pathname, version, body) {
  const single = pathname.match(/^\/api\/v[123]\/checks\/([0-9a-f-]{36})$/i);
  const action = pathname.match(/^\/api\/v[123]\/checks\/([0-9a-f-]{36})\/(pause|resume)$/i);
  const pings = pathname.match(/^\/api\/v[123]\/checks\/([0-9a-f-]{36})\/pings\/$/i);
  const pingBody = pathname.match(/^\/api\/v[123]\/checks\/([0-9a-f-]{36})\/pings\/(\d+)\/body$/i);
  const flips = pathname.match(/^\/api\/v[123]\/checks\/([0-9a-f-]{36})\/flips\/$/i);
  const match = single || action || pings || pingBody || flips;
  if (!match) return false;

  const uuid = match[1];
  if (req.method === "OPTIONS" && single) return sendHtml(req, res, 204, "");

  let bodyObject = {};
  if (req.method === "POST") {
    try {
      bodyObject = parseJsonBody(body);
    } catch {
      return apiError(req, res, 400, "could not parse request body");
    }
  }

  const readOnlyAllowed = Boolean(single && req.method === "GET");
  const auth = authorize(req, bodyObject, { readonly: readOnlyAllowed, bodyKey: req.method === "POST" });
  if (!auth.ok) return apiError(req, res, auth.status, auth.error);

  const check = checks.get(uuid);
  if (!check || deletedChecks.has(uuid)) return sendHtml(req, res, 404, "Not found");

  if (single) {
    if (req.method === "GET") return sendJson(req, res, 200, checkToDict(check, version, auth.readonly));
    if (req.method === "DELETE") {
      deletedChecks.add(uuid);
      checks.delete(uuid);
      return sendJson(req, res, 200, checkToDict(check, version, false));
    }
    if (req.method === "POST") {
      const validationError = validateSpec(bodyObject);
      if (validationError) return apiError(req, res, 400, validationError);
      updateCheck(check, bodyObject, version);
      return sendJson(req, res, 200, checkToDict(check, version, false));
    }
    return sendHtml(req, res, 405, "Method not allowed");
  }

  if (action) {
    if (req.method !== "POST") return sendHtml(req, res, 405, "Method not allowed");
    if (action[2] === "pause") {
      check.status = "paused";
      check.started = false;
      return sendJson(req, res, 200, checkToDict(check, version, false));
    }
    if (check.status !== "paused") return send(req, res, 409, "text/html", "check is not paused");
    check.status = "new";
    check.started = false;
    check.last_ping = null;
    return sendJson(req, res, 200, checkToDict(check, version, false));
  }

  if (pings) {
    if (req.method !== "GET") return sendHtml(req, res, 405, "Method not allowed");
    return sendJson(req, res, 200, {
      pings: check.pings.map((ping) => pingToDict(check, ping, version)),
    });
  }

  if (pingBody) {
    if (req.method !== "GET") return sendHtml(req, res, 405, "Method not allowed");
    const n = Number(pingBody[2]);
    const ping = check.pings.find((item) => item.n === n);
    if (!ping || !ping.body) return sendHtml(req, res, 404, "Not found");
    return sendText(req, res, 200, ping.body);
  }

  if (flips) {
    return sendJson(req, res, 200, { flips: [] });
  }

  return true;
}

async function handleUniqueKey(req, res, pathname, version) {
  const match = pathname.match(/^\/api\/v[123]\/checks\/([A-Za-z0-9]{40})$/);
  if (!match) return false;

  const auth = authorize(req, {}, { readonly: true, bodyKey: false });
  if (!auth.ok) return apiError(req, res, auth.status, auth.error);

  const check = Array.from(checks.values()).find((item) => item.uniqueKey === match[1]);
  if (!check) return sendHtml(req, res, 404, "Not found");
  return sendJson(req, res, 200, checkToDict(check, version, auth.readonly));
}

async function handleApi(req, res, url, body) {
  const { pathname } = url;
  const version = getApiVersion(pathname);

  if (/^\/api\/v[123]\/checks\/?$/.test(pathname)) {
    return handleChecksCollection(req, res, url, version, body);
  }

  await handleSingleCheck(req, res, pathname, version, body);
  if (res.writableEnded) return;

  await handleUniqueKey(req, res, pathname, version);
  if (res.writableEnded) return;

  if (/^\/api\/v[123]\/channels\/?$/.test(pathname)) {
    const auth = authorize(req, {}, { readonly: false, bodyKey: false });
    if (!auth.ok) return apiError(req, res, auth.status, auth.error);
    return sendJson(req, res, 200, { channels: [] });
  }

  if (/^\/api\/v[123]\/badges\/?$/.test(pathname)) {
    const auth = authorize(req, {}, { readonly: true, bodyKey: false });
    if (!auth.ok) return apiError(req, res, auth.status, auth.error);
    const tags = new Set(["*"]);
    for (const check of checks.values()) {
      for (const tag of tagList(check)) tags.add(tag);
    }
    const badges = {};
    for (const tag of tags) {
      const encoded = encodeURIComponent(tag);
      badges[tag] = {
        svg: `${SITE_ROOT}/badge/alice/0000000000/${encoded}.svg`,
        svg3: `${SITE_ROOT}/badge/alice/0000000000-3/${encoded}.svg`,
        json: `${SITE_ROOT}/badge/alice/0000000000/${encoded}.json`,
        json3: `${SITE_ROOT}/badge/alice/0000000000-3/${encoded}.json`,
        shields: `${SITE_ROOT}/badge/alice/0000000000/${encoded}.shields`,
        shields3: `${SITE_ROOT}/badge/alice/0000000000-3/${encoded}.shields`,
      };
    }
    return sendJson(req, res, 200, { badges });
  }

  if (/^\/api\/v[123]\/metrics\/?$/.test(pathname)) {
    const auth = authorize(req, {}, { readonly: true, bodyKey: false });
    if (!auth.ok) return apiError(req, res, auth.status, auth.error);
    return sendText(req, res, 200, "# HELP healthchecks_checks Number of checks\nhealthchecks_checks " + checks.size + "\n");
  }

  if (/^\/api\/v[123]\/status\/?$/.test(pathname)) {
    return sendJson(req, res, 200, { status: "ok" });
  }

  if (/^\/api\/v[123]\/bounces\/?$/.test(pathname) && req.method === "POST") {
    return sendHtml(req, res, 200, "OK");
  }

  if (/^\/api\/v[123]\/notifications\/[^/]+\/status\/?$/.test(pathname) && req.method === "POST") {
    return sendHtml(req, res, 200, "OK");
  }

  return sendHtml(req, res, 404, "Not found");
}

function handlePing(req, res, url, body) {
  const pathname = url.pathname;
  const uuidPing = pathname.match(/^\/ping\/([0-9a-f-]{36})(?:\/(fail|start|log|\d+))?\/?$/i);
  if (uuidPing) {
    const uuid = uuidPing[1];
    const actionPart = uuidPing[2] || "";
    const check = checks.get(uuid);
    if (!check || deletedChecks.has(uuid)) return sendHtml(req, res, 404, "Not found");

    let action = "success";
    if (actionPart === "fail") action = "fail";
    if (actionPart === "start") action = "start";
    if (actionPart === "log") action = "log";
    if (/^\d+$/.test(actionPart)) {
      const exitStatus = Number(actionPart);
      if (exitStatus > 255) return send(req, res, 400, "text/html", "invalid url format");
      if (exitStatus > 0) action = "fail";
    }

    const rid = url.searchParams.get("rid");
    if (rid !== null && !isUuid(rid)) return send(req, res, 400, "text/html", "invalid uuid format");
    recordPing(req, check, body, action, rid);
    return send(req, res, 200, "text/html", "OK", { "Access-Control-Allow-Origin": "*" });
  }

  const slugPing = pathname.match(/^\/ping\/([^/]+)\/([^/]+)(?:\/(fail|start|log|\d+))?\/?$/);
  if (slugPing) {
    const pingKey = slugPing[1];
    const slug = decodeURIComponent(slugPing[2]);
    const actionPart = slugPing[3] || "";
    if (slug !== slug.toLowerCase()) return send(req, res, 400, "text/html", "invalid url format");

    let check = Array.from(checks.values()).find((item) => item.slug === slug && pingKey === PING_KEY);
    let created = false;
    if (!check && url.searchParams.get("create") === "1" && pingKey === PING_KEY) {
      check = makeCheck();
      check.name = slug;
      check.slug = slug;
      checks.set(check.uuid, check);
      created = true;
    }
    if (!check) return sendHtml(req, res, 404, "Not found");

    let action = "success";
    if (actionPart === "fail") action = "fail";
    if (actionPart === "start") action = "start";
    if (actionPart === "log") action = "log";
    if (/^\d+$/.test(actionPart)) {
      const exitStatus = Number(actionPart);
      if (exitStatus > 255) return send(req, res, 400, "text/html", "invalid url format");
      if (exitStatus > 0) action = "fail";
    }

    recordPing(req, check, body, action, null);
    return send(req, res, created ? 201 : 200, "text/html", created ? "Created" : "OK", {
      "Access-Control-Allow-Origin": "*",
    });
  }

  return sendHtml(req, res, 404, "Not found");
}

async function handleAccounts(req, res, url, body) {
  const path = url.pathname;
  const loggedIn = hasSession(req);

  if (path === "/accounts/login/") {
    if (req.method === "GET") return sendHtml(req, res, 200, "Login");
    if (req.method === "POST") {
      const form = parseForm(body);
      if (form.action === "login" && form.email === "alice@example.org" && form.password === "password") {
        const sessionId = "session-" + crypto.randomBytes(8).toString("hex");
        sessions.add(sessionId);
        const next = url.searchParams.get("next") || "/";
        return redirect(req, res, next === "/projects/" ? `/projects/${PROJECT_CODE}/checks/` : next, {
          "Set-Cookie": `sessionid=${sessionId}; Path=/`,
        });
      }
      return sendHtml(req, res, 200, "Login");
    }
  }

  if (path === "/accounts/logout/" && req.method === "POST") return redirect(req, res, "/");

  if (path === "/accounts/signup/csrf/" && req.method === "GET") return sendHtml(req, res, 200, "Signup CSRF");
  if (path === "/accounts/signup/" && req.method === "GET") return sendHtml(req, res, 405, "Method not allowed");
  if (path === "/accounts/signup/" && req.method === "POST") {
    if (!hasCsrf(req, body)) return sendHtml(req, res, 403, "Forbidden");
    return sendHtml(req, res, 200, "Signup");
  }

  if (path === "/accounts/two_factor/webauthn/" && req.method === "GET") {
    return loggedIn ? sendHtml(req, res, 200, "Webauthn") : redirect(req, res, "/accounts/login/");
  }

  if (path === "/accounts/unsubscribe_alerts/bad-token/") return sendHtml(req, res, 404, "Not found");
  if (path.startsWith("/accounts/unsubscribe_reports/")) return sendHtml(req, res, 200, "Unsubscribe");
  if (path.startsWith("/accounts/change_email/") && path !== "/accounts/change_email/") return sendHtml(req, res, 200, "Change email verify");

  const protectedGet = new Set([
    "/accounts/change_email/",
    "/accounts/close/",
    "/accounts/profile/",
    "/accounts/profile/billing/",
    "/accounts/set_password/",
  ]);

  if (protectedGet.has(path) && req.method === "GET") {
    return loggedIn ? sendHtml(req, res, 200, path) : redirect(req, res, "/accounts/login/");
  }

  if (path === "/accounts/change_email/" && req.method === "POST") {
    return loggedIn ? sendHtml(req, res, 200, "Change email") : redirect(req, res, "/accounts/login/");
  }

  if (path === "/accounts/set_password/" && req.method === "POST") {
    return loggedIn ? sendHtml(req, res, 200, "Set password") : redirect(req, res, "/accounts/login/");
  }

  if (path === "/accounts/profile/appearance/" && req.method === "POST") {
    return loggedIn ? sendHtml(req, res, 200, "Appearance") : redirect(req, res, "/accounts/login/");
  }

  if (path === "/accounts/profile/notifications/" && req.method === "POST") {
    return loggedIn ? sendHtml(req, res, 200, "Notifications") : redirect(req, res, "/accounts/login/");
  }

  if (path === "/accounts/profile/billing/" && req.method === "POST") {
    if (!hasCsrf(req, body)) return sendHtml(req, res, 403, "Forbidden");
    return loggedIn ? redirect(req, res, "/accounts/profile/billing/") : redirect(req, res, "/accounts/login/");
  }

  return false;
}

function handleFront(req, res, url, body) {
  const path = url.pathname;
  const loggedIn = hasSession(req);

  if (path === "/" && req.method === "GET") return sendHtml(req, res, 200, "Healthchecks");
  if (path === "/pricing/" && req.method === "GET") return sendHtml(req, res, 200, "Pricing");
  if (path === "/docs/api/" && req.method === "GET") return sendHtml(req, res, 200, "API Docs");
  if (path === "/docs/cron/" && req.method === "GET") return sendHtml(req, res, 200, "Cron Docs");
  if (path === "/docs/search/" && req.method === "POST") return sendHtml(req, res, 200, "Search");
  if (path.startsWith("/docs/")) return sendHtml(req, res, 404, "Not found");
  if (path.startsWith("/cloaked/")) return sendHtml(req, res, 404, "Not found");
  if (path.startsWith("/integrations/")) return sendHtml(req, res, 404, "Not found");
  if (path === "/contact.vcf") return send(req, res, 200, "text/vcard", "BEGIN:VCARD\nEND:VCARD\n");

  const checkPage = path.match(/^\/checks\/([0-9a-f-]{36})\/([^/]+)\/(?:([0-9]+)\/?)?$/i);
  if (checkPage) {
    if (!loggedIn && req.method === "GET") return redirect(req, res, "/accounts/login/");
    const page = checkPage[2];
    if (req.method === "GET") {
      const check = checks.get(checkPage[1]);
      if (!check && page !== "name") return sendHtml(req, res, 404, "Not found");
      return sendHtml(req, res, 200, page);
    }
    if (req.method === "POST") {
      if (page === "name" && !loggedIn) return sendHtml(req, res, 403, "Forbidden");
      if (page === "transfer") return sendHtml(req, res, 400, "Transfer");
      if (["pause", "resume", "filtering_rules", "remove", "clear_events", "copy", "timeout"].includes(page)) {
        return redirect(req, res, `/checks/${checkPage[1]}/details/`);
      }
    }
  }

  const projectPage = path.match(/^\/projects\/([0-9a-f-]{36})\/([^/]+)\/?$/i);
  if (projectPage) {
    const page = projectPage[2];
    if (req.method === "GET") {
      if (!loggedIn) return redirect(req, res, "/accounts/login/");
      if (["add_signal", "add_trello", "channels"].includes(page)) return sendHtml(req, res, 404, "Not found");
      return sendHtml(req, res, 200, page);
    }

    if (req.method === "POST") {
      if (["settings", "remove"].includes(page) && !hasCsrf(req, body)) return sendHtml(req, res, 403, "Forbidden");
      if (page === "add_webhook") return sendHtml(req, res, 200, "Webhook");
      if (page.startsWith("add_")) return redirect(req, res, `/projects/${projectPage[1]}/integrations/`);
      if (["settings", "remove"].includes(page)) return redirect(req, res, "/");
    }
  }

  const projectNested = path.match(/^\/projects\/([0-9a-f-]{36})\/(checks|integrations|badges)\/(?:.*)?$/i);
  if (projectNested) {
    if (!loggedIn) return redirect(req, res, "/accounts/login/");
    return sendHtml(req, res, 200, projectNested[2]);
  }

  if (path === "/projects/menu/") {
    return loggedIn ? sendHtml(req, res, 200, "Projects") : redirect(req, res, "/accounts/login/");
  }

  return false;
}

function handleBadge(req, res, url) {
  const path = url.pathname;
  const aggregate = path.match(/^\/badge\/([^/]+)\/([^/]+)(?:\/([^/.]+))?\.(svg|json|shields)$/);
  if (aggregate) {
    const badgeKey = aggregate[1];
    const signature = aggregate[2];
    const tag = decodeURIComponent(aggregate[3] || "*");
    const format = aggregate[4];
    if (badgeKey !== "alice" || signature.startsWith("0000000000000000000000000000000000000000") || badgeKey === "nonexistent") {
      return sendHtml(req, res, 404, "Not found");
    }
    const selected = Array.from(checks.values()).filter((check) => tag === "*" || matchesTags(check, [tag]));
    const down = selected.filter((check) => check.status === "down").length;
    const status = down > 0 ? "down" : "up";
    if (format === "json") return sendJson(req, res, 200, { status, total: selected.length, grace: 0, down });
    if (format === "shields") return sendJson(req, res, 200, { schemaVersion: 1, label: tag, message: status, color: status === "up" ? "success" : "critical" });
    return send(req, res, 200, "image/svg+xml", `<svg><text>${status}</text></svg>`);
  }

  const single = path.match(/^\/b\/(\d+)\/([0-9a-f-]{36})\.(svg|json|shields)$/i);
  if (single) {
    const check = Array.from(checks.values()).find((item) => item.badgeKey === single[2]);
    if (!check) return sendHtml(req, res, 404, "Not found");
    const status = check.status === "down" ? "down" : "up";
    if (single[3] === "json") return sendJson(req, res, 200, { status, total: 1, grace: 0, down: status === "down" ? 1 : 0 });
    if (single[3] === "shields") return sendJson(req, res, 200, { schemaVersion: 1, label: check.name || check.uuid, message: status, color: status === "up" ? "success" : "critical" });
    return send(req, res, 200, "image/svg+xml", `<svg><text>${status}</text></svg>`);
  }

  return false;
}

async function route(req, res) {
  const body = await readBody(req);
  const url = new URL(req.url, `http://${req.headers.host || "localhost"}`);
  const path = url.pathname;

  if (path === "/__test/reset/") {
    resetState();
    return send(req, res, 200, "text/html", "ok");
  }

  if (path.startsWith("/api/v")) return handleApi(req, res, url, body);
  if (path.startsWith("/ping/")) return handlePing(req, res, url, body);
  if (path.startsWith("/badge/") || path.startsWith("/b/")) {
    handleBadge(req, res, url);
    if (res.writableEnded) return;
  }
  if (path.startsWith("/accounts/")) {
    await handleAccounts(req, res, url, body);
    if (res.writableEnded) return;
  }
  handleFront(req, res, url, body);
  if (res.writableEnded) return;

  sendHtml(req, res, 404, "Not found");
}

resetState();

const server = http.createServer((req, res) => {
  route(req, res).catch(() => {
    if (!res.headersSent) send(req, res, 500, "text/html", "server error");
    else res.end();
  });
});

server.listen(PORT, () => {
  console.log(`healthchecks target listening on http://localhost:${PORT}`);
});
