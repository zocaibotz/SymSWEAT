const http = require('http');
const { Readable, Writable } = require('stream');
const { createApp } = require('../src/app');

class FakeSocket extends Writable {
  constructor() {
    super();
    this.output = '';
    this.remoteAddress = '127.0.0.1';
  }

  _write(chunk, _encoding, callback) {
    this.output += chunk.toString();
    callback();
  }

  cork() {}
  uncork() {}
  destroy() {}
  on() { return this; }
  once() { return this; }
  emit() { return false; }
  removeListener() { return this; }
}

function parseResponse(raw) {
  const [headerBlock, body = ''] = raw.split('\r\n\r\n');
  const headerLines = headerBlock.split('\r\n').slice(1);
  const headers = {};
  for (const line of headerLines) {
    const [name, ...rest] = line.split(':');
    headers[name.toLowerCase()] = rest.join(':').trim();
  }
  let parsedBody = body;
  if ((headers['content-type'] || '').includes('application/json')) {
    parsedBody = JSON.parse(body || '{}');
  }
  return { headers, body: parsedBody };
}

async function apiRequest(app, { method = 'GET', path = '/', body }) {
  const payload = body ? JSON.stringify(body) : null;
  const req = Readable.from(payload ? [payload] : []);
  req.method = method;
  req.url = path;
  req.headers = payload ? {
    'content-type': 'application/json',
    'content-length': Buffer.byteLength(payload),
  } : {};
  req.httpVersion = '1.1';
  req.httpVersionMajor = 1;
  req.httpVersionMinor = 1;

  const socket = new FakeSocket();
  req.socket = socket;
  req.connection = socket;

  const res = new http.ServerResponse(req);
  res.assignSocket(socket);

  return await new Promise((resolve, reject) => {
    res.on('finish', () => {
      resolve({
        status: res.statusCode,
        ...parseResponse(socket.output),
      });
    });
    app.handle(req, res, reject);
  });
}

describe('ZOC-91 Decisions & Problems API', () => {
  let app;
  const originalNodeEnv = process.env.NODE_ENV;

  beforeEach(() => {
    process.env.NODE_ENV = 'test';
    app = createApp();
  });

  afterAll(() => {
    process.env.NODE_ENV = originalNodeEnv;
  });

  test('POST /api/projects/:id/decisions creates decision with required reasoning fields', async () => {
    const res = await apiRequest(app, {
      method: 'POST',
      path: '/api/projects/p1/decisions',
      body: {
        phase: 'design',
        context: 'Need cache strategy',
        reasoning: 'Read-heavy access pattern',
        outcome: 'Adopt Redis LRU',
      },
    });

    expect(res.status).toBe(201);

    expect(res.body.decision).toMatchObject({
      projectId: 'p1',
      phase: 'design',
      context: 'Need cache strategy',
      reasoning: 'Read-heavy access pattern',
      outcome: 'Adopt Redis LRU',
      entryType: 'decision',
    });
  });

  test('POST /api/projects/:id/problems creates problem and links attempted resolutions', async () => {
    const res = await apiRequest(app, {
      method: 'POST',
      path: '/api/projects/p1/problems',
      body: {
        phase: 'build',
        title: 'Intermittent timeout',
        description: 'API times out under load',
        attemptedResolutions: ['increase timeout', 'reduce payload size'],
      },
    });

    expect(res.status).toBe(201);

    expect(res.body.problem).toMatchObject({
      projectId: 'p1',
      phase: 'build',
      title: 'Intermittent timeout',
      description: 'API times out under load',
      attemptedResolutions: ['increase timeout', 'reduce payload size'],
      entryType: 'problem',
    });
    expect(res.body.problem.resolutionIds).toEqual([]);
  });

  test('POST /api/problems/:id/resolutions attaches resolution to problem', async () => {
    const problemRes = await apiRequest(app, {
      method: 'POST',
      path: '/api/projects/p1/problems',
      body: {
        phase: 'build',
        title: 'Queue backlog',
        description: 'Workers not draining quickly enough',
      },
    });

    expect(problemRes.status).toBe(201);

    const problemId = problemRes.body.problem.id;

    const resolutionRes = await apiRequest(app, {
      method: 'POST',
      path: `/api/problems/${problemId}/resolutions`,
      body: {
        phase: 'build',
        description: 'Scaled workers from 5 to 12',
        outcome: 'improved',
      },
    });

    expect(resolutionRes.status).toBe(201);

    expect(resolutionRes.body.resolution).toMatchObject({
      problemId,
      phase: 'build',
      description: 'Scaled workers from 5 to 12',
      outcome: 'improved',
      entryType: 'resolution',
    });

    const logsRes = await apiRequest(app, {
      path: '/api/projects/p1/debug-logs?type=resolution',
    });

    expect(logsRes.status).toBe(200);

    expect(logsRes.body.entries.some((e) => e.entryType === 'resolution' && e.problemId === problemId)).toBe(true);
  });

  test('GET /api/projects/:id/debug-logs supports level/type/phase/date/full-text filters', async () => {
    let res = await apiRequest(app, {
      method: 'POST',
      path: '/api/projects/p1/decisions',
      body: {
        phase: 'design',
        context: 'Need observability',
        reasoning: 'Cannot trace failures',
        outcome: 'Add structured logs',
      },
    });
    expect(res.status).toBe(201);

    res = await apiRequest(app, {
      method: 'POST',
      path: '/api/projects/p1/problems',
      body: {
        phase: 'build',
        title: 'Null pointer in parser',
        description: 'Crash when token list is empty',
      },
    });
    expect(res.status).toBe(201);

    const phaseRes = await apiRequest(app, {
      path: '/api/projects/p1/debug-logs?phase=design&type=decision&q=observability',
    });
    expect(phaseRes.status).toBe(200);

    expect(phaseRes.body.total).toBeGreaterThan(0);
    expect(phaseRes.body.entries.every((e) => e.phase === 'design')).toBe(true);
    expect(phaseRes.body.entries.every((e) => e.entryType === 'decision')).toBe(true);

    const levelRes = await apiRequest(app, {
      path: '/api/projects/p1/debug-logs?level=warn',
    });
    expect(levelRes.status).toBe(200);

    expect(levelRes.body.entries.length).toBeGreaterThan(0);
    expect(levelRes.body.entries.every((e) => e.level === 'warn')).toBe(true);

    const from = new Date(Date.now() - 60_000).toISOString();
    const to = new Date(Date.now() + 60_000).toISOString();
    const dateRes = await apiRequest(app, {
      path: `/api/projects/p1/debug-logs?startDate=${encodeURIComponent(from)}&endDate=${encodeURIComponent(to)}`,
    });
    expect(dateRes.status).toBe(200);

    expect(dateRes.body.total).toBeGreaterThan(0);
  });

  test('GET /api/dashboard returns portfolio stats, project buckets, and recent activity', async () => {
    const projectRes = await apiRequest(app, {
      method: 'POST',
      path: '/api/projects',
      body: { name: 'Tracker Modernization', prompt: 'Refresh the dashboard UX' },
    });
    expect(projectRes.status).toBe(201);

    const projectId = projectRes.body.project.id;

    let res = await apiRequest(app, {
      method: 'POST',
      path: `/api/projects/${projectId}/decisions`,
      body: {
        phase: 'design',
        context: 'Need a dashboard layout',
        reasoning: 'Operators need an at-a-glance portfolio view',
        outcome: 'Adopt cards plus activity feed',
      },
    });
    expect(res.status).toBe(201);

    res = await apiRequest(app, {
      method: 'POST',
      path: `/api/projects/${projectId}/artifacts`,
      body: {
        phase: 'design',
        name: 'Dashboard mock',
        url: 'https://example.com/mock',
        kind: 'figma',
      },
    });
    expect(res.status).toBe(201);

    const dashboardRes = await apiRequest(app, { path: '/api/dashboard' });
    expect(dashboardRes.status).toBe(200);

    expect(dashboardRes.body.stats).toMatchObject({
      totalProjects: 1,
      inProgress: 1,
      completed: 0,
      totalArtifacts: 1,
      totalDecisions: 1,
      openProblems: 0,
    });
    expect(dashboardRes.body.currentProjects).toHaveLength(1);
    expect(dashboardRes.body.historicalProjects).toHaveLength(0);
    expect(dashboardRes.body.recentEvents.some((event) => event.entryType === 'artifact')).toBe(true);
  });

  test('GET /api/projects/:id/overview returns derived project metrics, stages, and artifacts', async () => {
    const projectRes = await apiRequest(app, {
      method: 'POST',
      path: '/api/projects',
      body: { name: 'Release Train', prompt: 'Ship v2' },
    });
    expect(projectRes.status).toBe(201);

    const projectId = projectRes.body.project.id;

    let res = await apiRequest(app, {
      method: 'POST',
      path: `/api/projects/${projectId}/decisions`,
      body: {
        phase: 'build',
        context: 'Need rollout guardrails',
        reasoning: 'Mitigate user impact',
        outcome: 'Feature-flag the release',
      },
    });
    expect(res.status).toBe(201);

    res = await apiRequest(app, {
      method: 'POST',
      path: `/api/projects/${projectId}/problems`,
      body: {
        phase: 'test',
        title: 'Regression in checkout',
        description: 'Purchase flow fails for guest users',
      },
    });
    expect(res.status).toBe(201);

    res = await apiRequest(app, {
      method: 'POST',
      path: `/api/projects/${projectId}/artifacts`,
      body: {
        phase: 'test',
        name: 'Regression report',
        url: 'https://example.com/report',
      },
    });
    expect(res.status).toBe(201);

    const overviewRes = await apiRequest(app, { path: `/api/projects/${projectId}/overview` });
    expect(overviewRes.status).toBe(200);

    expect(overviewRes.body.project).toMatchObject({
      id: projectId,
      totalArtifacts: 1,
      totalDecisions: 1,
      openProblems: 1,
      derivedStatus: 'in-progress',
    });
    expect(overviewRes.body.stages.some((stage) => stage.phase === 'test' && stage.isCurrent)).toBe(true);
    expect(overviewRes.body.artifacts).toHaveLength(1);
    expect(Array.isArray(overviewRes.body.phaseDocumentation)).toBe(true);
    expect(overviewRes.body.recentEvents.length).toBeGreaterThan(0);
  });
});
