const crypto = require('crypto');
const express = require('express');
const fs = require('fs');
const path = require('path');

let DatabaseSync;
try {
  ({ DatabaseSync } = require('node:sqlite'));
} catch {
  DatabaseSync = null;
}

const STAGE_ORDER = [
  'prompt',
  'prd',
  'design',
  'architecture',
  'sdd',
  'tdd',
  'build',
  'test',
  'deploy',
  'completed',
];

const STALLED_THRESHOLD_DAYS = Number(process.env.STALLED_THRESHOLD_DAYS || 7);
const WORKSPACE_ROOT = process.env.WORKSPACE_ROOT || path.resolve(process.cwd(), '..', '..');
const SWARM_DOCS_ROOT = process.env.SWARM_DOCS_ROOT || path.join(WORKSPACE_ROOT, 'projects', 'symphony');
const GITHUB_REPO = process.env.GITHUB_REPO || 'zocaibotz/swarminsym';
const GITHUB_BRANCH = process.env.GITHUB_BRANCH || 'master';
const TRACKER_DOCS_ROOT = process.env.TRACKER_DOCS_ROOT || path.join(process.cwd(), 'docs');
const LINEAR_TEAM_SLUG = process.env.LINEAR_TEAM_SLUG || '';

const STAGE_DOC_CANDIDATES = {
  prompt: ['PROMPT.md', 'prompt.md', 'swarm_prompt.txt', 'README.md'],
  prd: ['PRD.md', 'prd.md'],
  design: ['DESIGN.md', 'design.md', 'SYSTEM_DESIGN.md'],
  architecture: ['ARCHITECTURE.md', 'architecture.md', 'SYSTEM_DESIGN.md', 'API_CONTRACTS.md'],
  sdd: ['SDD.md', 'sdd.md'],
  tdd: ['TDD.md', 'tdd.md'],
  build: ['BUILD.md', 'build.md', 'IMPLEMENTATION.md', 'repo/README.md'],
  test: ['TEST.md', 'test.md', 'TEST_PLAN.md', 'tests/README.md'],
  deploy: ['DEPLOY.md', 'deploy.md', 'RELEASE.md'],
  completed: ['SUMMARY.md', 'REPORT.md', 'README.md'],
};

function nowIso() {
  return new Date().toISOString();
}

function textMatches(entry, q) {
  if (!q) return true;
  const haystack = JSON.stringify(entry).toLowerCase();
  return haystack.includes(String(q).toLowerCase());
}

function inDateRange(entry, startDate, endDate) {
  const ts = new Date(entry.createdAt).getTime();
  if (Number.isNaN(ts)) return false;
  if (startDate) {
    const start = new Date(startDate).getTime();
    if (Number.isNaN(start) || ts < start) return false;
  }
  if (endDate) {
    const end = new Date(endDate).getTime();
    if (Number.isNaN(end) || ts > end) return false;
  }
  return true;
}

function phaseRank(phase) {
  const rank = STAGE_ORDER.indexOf(String(phase || '').toLowerCase());
  return rank === -1 ? STAGE_ORDER.length : rank;
}

function isCompletedProject(project, events) {
  if (project.status === 'completed') return true;
  return events.some((event) => ['deploy', 'completed'].includes(String(event.phase || '').toLowerCase()));
}

function normalizeProject(row) {
  return {
    id: row.id,
    name: row.name,
    prompt: row.prompt || '',
    status: row.status || 'active',
    createdAt: row.createdAt,
    updatedAt: row.updatedAt,
  };
}

function normalizeEvent(event, projectLookup) {
  const project = projectLookup.get(event.projectId);
  const title = event.entryType === 'decision'
    ? event.context
    : event.entryType === 'problem'
      ? event.title
      : event.entryType === 'resolution'
        ? event.description
        : event.name;

  const detail = event.entryType === 'decision'
    ? event.outcome
    : event.entryType === 'problem'
      ? event.description
      : event.entryType === 'resolution'
        ? event.outcome
        : event.url;

  return {
    id: event.id,
    projectId: event.projectId,
    projectName: project ? project.name : event.projectId,
    phase: event.phase || 'unspecified',
    entryType: event.entryType,
    level: event.level || 'info',
    title,
    detail,
    createdAt: event.createdAt,
    updatedAt: event.updatedAt,
    url: event.url || null,
    kind: event.kind || null,
    problemId: event.problemId || null,
  };
}

function extractIssueKeys(project, events = []) {
  const candidates = [
    project.id,
    project.name,
    project.prompt,
    ...events.flatMap((event) => [event.context, event.title, event.description, event.outcome]),
  ].filter(Boolean);

  const keys = new Set();
  for (const candidate of candidates) {
    const matches = String(candidate).match(/\b([A-Z]{2,10}-\d+)\b/gi) || [];
    for (const match of matches) keys.add(match.toUpperCase());
  }
  return [...keys];
}

function extractProjectKey(project, events = []) {
  const [first] = extractIssueKeys(project, events).filter((key) => key.startsWith('ZOC-'));
  return first || null;
}

function buildLinearIssueLinks(project, events = []) {
  const keys = extractIssueKeys(project, events);
  return keys.map((key) => ({
    id: `linear:${key}`,
    key,
    phase: 'all',
    name: `Linear issue · ${key}`,
    kind: 'linear-issue',
    url: LINEAR_TEAM_SLUG
      ? `https://linear.app/${LINEAR_TEAM_SLUG}/issue/${key}`
      : `https://linear.app/search?query=${encodeURIComponent(key)}`,
  }));
}

function toGithubBlobUrl(relativePath) {
  const normalized = String(relativePath || '').replace(/^\/+/, '').split(path.sep).join('/');
  return `https://github.com/${GITHUB_REPO}/blob/${GITHUB_BRANCH}/${normalized}`;
}

function resolveProjectDocsDirectory(project, events = []) {
  const key = extractProjectKey(project, events);
  if (!key || !fs.existsSync(SWARM_DOCS_ROOT)) return null;

  const direct = path.join(SWARM_DOCS_ROOT, key);
  if (fs.existsSync(direct) && fs.statSync(direct).isDirectory()) return direct;

  const candidates = fs.readdirSync(SWARM_DOCS_ROOT, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .filter((name) => name.toUpperCase().startsWith(key));

  if (!candidates.length) return null;
  return path.join(SWARM_DOCS_ROOT, candidates.sort()[0]);
}

function buildPhaseDocumentationLinks(project, events = []) {
  const projectDir = resolveProjectDocsDirectory(project, events);
  const fallbackDir = fs.existsSync(TRACKER_DOCS_ROOT) ? TRACKER_DOCS_ROOT : null;

  const docs = [];
  for (const phase of STAGE_ORDER) {
    const candidates = STAGE_DOC_CANDIDATES[phase] || [];
    for (const candidate of candidates) {
      const scopedPath = projectDir ? path.join(projectDir, candidate) : null;
      const fallbackPath = fallbackDir ? path.join(fallbackDir, candidate) : null;
      const filePath = scopedPath && fs.existsSync(scopedPath) ? scopedPath : (fallbackPath && fs.existsSync(fallbackPath) ? fallbackPath : null);
      if (filePath && fs.statSync(filePath).isFile()) {
        const relativePath = path.relative(WORKSPACE_ROOT, filePath);
        docs.push({
          id: `${phase}:${candidate}`,
          phase,
          name: `${phase.toUpperCase()} doc · ${path.basename(candidate)}`,
          kind: projectDir && filePath.startsWith(projectDir) ? 'phase-doc' : 'phase-template',
          url: toGithubBlobUrl(relativePath),
          localPath: relativePath,
        });
        break;
      }
    }
  }
  return docs;
}

function buildStageDetails(project, events, artifacts) {
  const stageMap = new Map();

  for (const stage of STAGE_ORDER) {
    stageMap.set(stage, {
      id: stage,
      name: stage.toUpperCase(),
      phase: stage,
      isCurrent: false,
      status: 'upcoming',
      startedAt: null,
      updatedAt: null,
      decisions: [],
      problems: [],
      resolutions: [],
      artifacts: [],
      documents: [],
      linearIssues: [],
      totalEvents: 0,
      openProblems: 0,
    });
  }

  for (const event of events) {
    const key = stageMap.has(String(event.phase).toLowerCase()) ? String(event.phase).toLowerCase() : 'build';
    const stage = stageMap.get(key);
    stage.totalEvents += 1;
    stage.startedAt = stage.startedAt || event.createdAt;
    stage.updatedAt = event.updatedAt || event.createdAt;
    if (event.entryType === 'decision') stage.decisions.push(event);
    if (event.entryType === 'problem') {
      stage.problems.push(event);
      if (event.status !== 'resolved' && event.status !== 'closed') stage.openProblems += 1;
    }
    if (event.entryType === 'resolution') stage.resolutions.push(event);
  }

  for (const artifact of artifacts) {
    const key = stageMap.has(String(artifact.phase).toLowerCase()) ? String(artifact.phase).toLowerCase() : 'build';
    const stage = stageMap.get(key);
    stage.artifacts.push(artifact);
    stage.startedAt = stage.startedAt || artifact.createdAt;
    stage.updatedAt = artifact.updatedAt || artifact.createdAt;
  }

  const documentationLinks = buildPhaseDocumentationLinks(project, events);
  for (const doc of documentationLinks) {
    const key = stageMap.has(String(doc.phase).toLowerCase()) ? String(doc.phase).toLowerCase() : 'build';
    const stage = stageMap.get(key);
    stage.documents.push(doc);
    if (!stage.updatedAt) stage.updatedAt = project.updatedAt;
  }

  const linearIssueLinks = buildLinearIssueLinks(project, events);
  if (linearIssueLinks.length) {
    for (const stage of stageMap.values()) {
      stage.linearIssues = linearIssueLinks;
    }
  }

  const stages = [...stageMap.values()].sort((a, b) => phaseRank(a.phase) - phaseRank(b.phase));
  const completed = isCompletedProject(project, events);
  const activeStages = stages.filter((stage) => stage.totalEvents > 0 || stage.artifacts.length > 0 || (stage.documents || []).some((doc) => doc.kind === 'phase-doc'));
  const currentPhase = activeStages.length > 0 ? activeStages[activeStages.length - 1].phase : STAGE_ORDER[0];

  let reachedCurrent = false;
  for (const stage of stages) {
    if (stage.phase === currentPhase) {
      stage.isCurrent = !completed;
      stage.status = completed ? 'completed' : 'current';
      reachedCurrent = true;
      continue;
    }
    if (!reachedCurrent && (stage.totalEvents > 0 || stage.artifacts.length > 0 || (stage.documents || []).some((doc) => doc.kind === 'phase-doc'))) {
      stage.status = 'completed';
      continue;
    }
    stage.status = completed ? 'completed' : 'upcoming';
  }

  return stages;
}

function buildProjectMetrics(project, events, artifacts) {
  const completed = isCompletedProject(project, events);
  const durationMs = new Date(project.updatedAt).getTime() - new Date(project.createdAt).getTime();
  const openProblems = events.filter((event) => event.entryType === 'problem' && event.status !== 'resolved' && event.status !== 'closed').length;
  const decisionCount = events.filter((event) => event.entryType === 'decision').length;
  const currentStage = events.length > 0
    ? [...events].sort((a, b) => phaseRank(a.phase) - phaseRank(b.phase))[events.length - 1].phase
    : 'prompt';
  const stalledThreshold = Date.now() - (STALLED_THRESHOLD_DAYS * 24 * 60 * 60 * 1000);
  const stalled = !completed && project.status !== 'completed' && new Date(project.updatedAt).getTime() < stalledThreshold;

  return {
    ...normalizeProject(project),
    derivedStatus: completed ? 'completed' : stalled ? 'stalled' : 'in-progress',
    currentStage,
    totalEvents: events.length,
    totalArtifacts: artifacts.length,
    totalDecisions: decisionCount,
    openProblems,
    avgDurationDays: Number.isFinite(durationMs) ? Number((durationMs / (24 * 60 * 60 * 1000)).toFixed(1)) : null,
    lastActivityAt: project.updatedAt,
    isHistorical: completed,
    isStalled: stalled,
  };
}

function buildDashboardPayload(store, filters = {}) {
  const projects = store.listProjects();
  const projectLookup = new Map(projects.map((project) => [project.id, project]));
  const metrics = projects.map((project) => {
    const events = store.getProjectEvents(project.id);
    const artifacts = store.listArtifacts(project.id);
    return buildProjectMetrics(project, events, artifacts);
  });

  const q = String(filters.q || '').trim().toLowerCase();
  const tab = String(filters.tab || 'all');
  let filtered = metrics.filter((project) => {
    if (!q) return true;
    return JSON.stringify(project).toLowerCase().includes(q);
  });

  if (tab === 'current') filtered = filtered.filter((project) => !project.isHistorical);
  if (tab === 'historical') filtered = filtered.filter((project) => project.isHistorical);
  if (tab === 'stalled') filtered = filtered.filter((project) => project.isStalled);

  const events = store.listRecentEvents(Number(filters.limit || 12)).map((event) => normalizeEvent(event, projectLookup));
  const activeProjects = filtered.filter((project) => !project.isHistorical);
  const historicalProjects = filtered.filter((project) => project.isHistorical);
  const avgDurationDays = metrics.length
    ? Number((metrics.reduce((sum, project) => sum + (project.avgDurationDays || 0), 0) / metrics.length).toFixed(1))
    : null;

  return {
    stats: {
      totalProjects: metrics.length,
      inProgress: metrics.filter((project) => project.derivedStatus === 'in-progress').length,
      completed: metrics.filter((project) => project.derivedStatus === 'completed').length,
      stalled: metrics.filter((project) => project.derivedStatus === 'stalled').length,
      avgProjectDurationDays: avgDurationDays,
      totalArtifacts: metrics.reduce((sum, project) => sum + project.totalArtifacts, 0),
      totalDecisions: metrics.reduce((sum, project) => sum + project.totalDecisions, 0),
      openProblems: metrics.reduce((sum, project) => sum + project.openProblems, 0),
    },
    projects: filtered,
    currentProjects: activeProjects,
    historicalProjects: historicalProjects,
    recentEvents: events,
  };
}

class MemoryStore {
  constructor() {
    this.projects = new Map();
    this.decisions = [];
    this.problems = [];
    this.resolutions = [];
    this.artifacts = [];
  }

  ensureProject(projectId, name = null, prompt = '') {
    if (!this.projects.has(projectId)) {
      const t = nowIso();
      this.projects.set(projectId, {
        id: projectId,
        name: name || projectId,
        prompt,
        status: 'active',
        createdAt: t,
        updatedAt: t,
      });
    }
    return this.projects.get(projectId);
  }

  createProject({ name, prompt = '' }) {
    const t = nowIso();
    const project = {
      id: crypto.randomUUID(),
      name,
      prompt,
      status: 'active',
      createdAt: t,
      updatedAt: t,
    };
    this.projects.set(project.id, project);
    return project;
  }

  getProject(projectId) {
    return this.projects.get(projectId) || null;
  }

  listProjects() {
    return [...this.projects.values()].sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
  }

  createDecision(data) {
    this.ensureProject(data.projectId);
    const t = nowIso();
    const decision = { ...data, id: crypto.randomUUID(), createdAt: t, updatedAt: t, entryType: 'decision', level: 'info' };
    this.decisions.push(decision);
    this.projects.get(data.projectId).updatedAt = t;
    return decision;
  }

  createProblem(data) {
    this.ensureProject(data.projectId);
    const t = nowIso();
    const problem = {
      ...data,
      id: crypto.randomUUID(),
      attemptedResolutions: data.attemptedResolutions || [],
      resolutionIds: data.resolutionIds || [],
      status: data.status || 'open',
      summary: data.summary || data.title,
      resolution: data.resolution || null,
      entryType: 'problem',
      level: 'warn',
      createdAt: t,
      updatedAt: t,
    };
    this.problems.push(problem);
    this.projects.get(data.projectId).updatedAt = t;
    return problem;
  }

  updateProblem(problemId, patch) {
    const problem = this.problems.find((item) => item.id === problemId);
    if (!problem) return null;
    if (patch.status) problem.status = patch.status;
    if (patch.resolution) {
      problem.resolution = patch.resolution;
      problem.attemptedResolutions = problem.attemptedResolutions || [];
      problem.attemptedResolutions.push(patch.resolution);
    }
    problem.updatedAt = nowIso();
    const project = this.projects.get(problem.projectId);
    if (project) project.updatedAt = problem.updatedAt;
    return problem;
  }

  getProblem(problemId) {
    return this.problems.find((item) => item.id === problemId) || null;
  }

  createResolution(data) {
    const problem = this.getProblem(data.problemId);
    if (!problem) return null;
    this.ensureProject(problem.projectId);
    const t = nowIso();
    const resolution = {
      ...data,
      id: crypto.randomUUID(),
      projectId: problem.projectId,
      entryType: 'resolution',
      level: 'info',
      createdAt: t,
      updatedAt: t,
    };
    this.resolutions.push(resolution);
    problem.resolutionIds = problem.resolutionIds || [];
    problem.resolutionIds.push(resolution.id);
    problem.attemptedResolutions = problem.attemptedResolutions || [];
    problem.attemptedResolutions.push(data.description);
    problem.resolution = data.description;
    problem.updatedAt = t;
    this.projects.get(problem.projectId).updatedAt = t;
    return { resolution, problem };
  }

  createArtifact(data) {
    this.ensureProject(data.projectId);
    const t = nowIso();
    const artifact = {
      ...data,
      id: crypto.randomUUID(),
      entryType: 'artifact',
      level: 'info',
      createdAt: t,
      updatedAt: t,
    };
    this.artifacts.push(artifact);
    this.projects.get(data.projectId).updatedAt = t;
    return artifact;
  }

  listArtifacts(projectId) {
    return this.artifacts
      .filter((artifact) => artifact.projectId === projectId)
      .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
  }

  getProjectEvents(projectId) {
    return [
      ...this.decisions.filter((decision) => decision.projectId === projectId),
      ...this.problems.filter((problem) => problem.projectId === projectId),
      ...this.resolutions.filter((resolution) => resolution.projectId === projectId),
    ].sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt));
  }

  listRecentEvents(limit = 12) {
    return [
      ...this.decisions,
      ...this.problems,
      ...this.resolutions,
      ...this.artifacts,
    ].sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)).slice(0, limit);
  }
}

class SqliteStore {
  constructor(dbPath) {
    const abs = path.resolve(dbPath);
    fs.mkdirSync(path.dirname(abs), { recursive: true });
    this.db = new DatabaseSync(abs);
    this.db.exec(`
      PRAGMA journal_mode=WAL;
      CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        prompt TEXT DEFAULT '',
        status TEXT DEFAULT 'active',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
      );
      CREATE TABLE IF NOT EXISTS decisions (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        phase TEXT NOT NULL,
        context TEXT NOT NULL,
        reasoning TEXT NOT NULL,
        outcome TEXT NOT NULL,
        title TEXT,
        rationale TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
      );
      CREATE TABLE IF NOT EXISTS problems (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        phase TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        severity TEXT,
        status TEXT DEFAULT 'open',
        attempted_resolutions TEXT DEFAULT '[]',
        resolution_ids TEXT DEFAULT '[]',
        resolution TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
      );
      CREATE TABLE IF NOT EXISTS resolutions (
        id TEXT PRIMARY KEY,
        problem_id TEXT NOT NULL,
        project_id TEXT NOT NULL,
        phase TEXT NOT NULL,
        description TEXT NOT NULL,
        outcome TEXT DEFAULT 'attempted',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
      );
      CREATE TABLE IF NOT EXISTS artifacts (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        phase TEXT NOT NULL,
        name TEXT NOT NULL,
        url TEXT NOT NULL,
        kind TEXT DEFAULT 'link',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
      );
    `);
  }

  ensureProject(projectId, name = null, prompt = '') {
    const row = this.db.prepare('SELECT * FROM projects WHERE id = ?').get(projectId);
    if (row) return this._projectRow(row);
    const t = nowIso();
    this.db.prepare('INSERT INTO projects (id, name, prompt, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)')
      .run(projectId, name || projectId, prompt || '', 'active', t, t);
    return this._projectRow(this.db.prepare('SELECT * FROM projects WHERE id = ?').get(projectId));
  }

  createProject({ name, prompt = '' }) {
    const id = crypto.randomUUID();
    const t = nowIso();
    this.db.prepare('INSERT INTO projects (id, name, prompt, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)')
      .run(id, name, prompt, 'active', t, t);
    return this._projectRow(this.db.prepare('SELECT * FROM projects WHERE id = ?').get(id));
  }

  getProject(projectId) {
    const row = this.db.prepare('SELECT * FROM projects WHERE id = ?').get(projectId);
    return row ? this._projectRow(row) : null;
  }

  listProjects() {
    return this.db.prepare('SELECT * FROM projects ORDER BY updated_at DESC').all().map((row) => this._projectRow(row));
  }

  createDecision(data) {
    this.ensureProject(data.projectId);
    const id = crypto.randomUUID();
    const t = nowIso();
    this.db.prepare(`INSERT INTO decisions
      (id, project_id, phase, context, reasoning, outcome, title, rationale, created_at, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
      .run(id, data.projectId, data.phase, data.context, data.reasoning, data.outcome, data.title || null, data.rationale || null, t, t);
    this.db.prepare('UPDATE projects SET updated_at = ? WHERE id = ?').run(t, data.projectId);
    return this._decisionRow(this.db.prepare('SELECT * FROM decisions WHERE id = ?').get(id));
  }

  createProblem(data) {
    this.ensureProject(data.projectId);
    const id = crypto.randomUUID();
    const t = nowIso();
    this.db.prepare(`INSERT INTO problems
      (id, project_id, phase, title, description, severity, status, attempted_resolutions, resolution_ids, resolution, created_at, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
      .run(
        id,
        data.projectId,
        data.phase,
        data.title,
        data.description,
        data.severity || null,
        data.status || 'open',
        JSON.stringify(data.attemptedResolutions || []),
        JSON.stringify(data.resolutionIds || []),
        data.resolution || null,
        t,
        t,
      );
    this.db.prepare('UPDATE projects SET updated_at = ? WHERE id = ?').run(t, data.projectId);
    return this._problemRow(this.db.prepare('SELECT * FROM problems WHERE id = ?').get(id));
  }

  updateProblem(problemId, patch) {
    const row = this.db.prepare('SELECT * FROM problems WHERE id = ?').get(problemId);
    if (!row) return null;
    const problem = this._problemRow(row);
    if (patch.status) problem.status = patch.status;
    if (patch.resolution) {
      problem.resolution = patch.resolution;
      problem.attemptedResolutions = problem.attemptedResolutions || [];
      problem.attemptedResolutions.push(patch.resolution);
    }
    problem.updatedAt = nowIso();
    this.db.prepare(`UPDATE problems SET status = ?, resolution = ?, attempted_resolutions = ?, updated_at = ? WHERE id = ?`)
      .run(problem.status, problem.resolution || null, JSON.stringify(problem.attemptedResolutions || []), problem.updatedAt, problem.id);
    this.db.prepare('UPDATE projects SET updated_at = ? WHERE id = ?').run(problem.updatedAt, problem.projectId);
    return problem;
  }

  getProblem(problemId) {
    const row = this.db.prepare('SELECT * FROM problems WHERE id = ?').get(problemId);
    return row ? this._problemRow(row) : null;
  }

  createResolution(data) {
    const problem = this.getProblem(data.problemId);
    if (!problem) return null;
    const id = crypto.randomUUID();
    const t = nowIso();
    this.db.prepare(`INSERT INTO resolutions
      (id, problem_id, project_id, phase, description, outcome, created_at, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)`)
      .run(id, problem.id, problem.projectId, data.phase, data.description, data.outcome || 'attempted', t, t);

    const updatedProblem = this.updateProblem(problem.id, { resolution: data.description });
    updatedProblem.resolutionIds = updatedProblem.resolutionIds || [];
    updatedProblem.resolutionIds.push(id);
    this.db.prepare('UPDATE problems SET resolution_ids = ?, updated_at = ? WHERE id = ?')
      .run(JSON.stringify(updatedProblem.resolutionIds), nowIso(), problem.id);

    const resolution = this._resolutionRow(this.db.prepare('SELECT * FROM resolutions WHERE id = ?').get(id));
    return { resolution, problem: this.getProblem(problem.id) };
  }

  createArtifact(data) {
    this.ensureProject(data.projectId);
    const id = crypto.randomUUID();
    const t = nowIso();
    this.db.prepare(`INSERT INTO artifacts
      (id, project_id, phase, name, url, kind, created_at, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)`)
      .run(id, data.projectId, data.phase, data.name, data.url, data.kind || 'link', t, t);
    this.db.prepare('UPDATE projects SET updated_at = ? WHERE id = ?').run(t, data.projectId);
    return this._artifactRow(this.db.prepare('SELECT * FROM artifacts WHERE id = ?').get(id));
  }

  listArtifacts(projectId) {
    return this.db.prepare('SELECT * FROM artifacts WHERE project_id = ? ORDER BY created_at DESC').all(projectId)
      .map((row) => this._artifactRow(row));
  }

  getProjectEvents(projectId) {
    const decisions = this.db.prepare('SELECT * FROM decisions WHERE project_id = ?').all(projectId).map((row) => this._decisionRow(row));
    const problems = this.db.prepare('SELECT * FROM problems WHERE project_id = ?').all(projectId).map((row) => this._problemRow(row));
    const resolutions = this.db.prepare('SELECT * FROM resolutions WHERE project_id = ?').all(projectId).map((row) => this._resolutionRow(row));
    return [...decisions, ...problems, ...resolutions].sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt));
  }

  listRecentEvents(limit = 12) {
    const decisions = this.db.prepare('SELECT * FROM decisions ORDER BY created_at DESC LIMIT ?').all(limit).map((row) => this._decisionRow(row));
    const problems = this.db.prepare('SELECT * FROM problems ORDER BY created_at DESC LIMIT ?').all(limit).map((row) => this._problemRow(row));
    const resolutions = this.db.prepare('SELECT * FROM resolutions ORDER BY created_at DESC LIMIT ?').all(limit).map((row) => this._resolutionRow(row));
    const artifacts = this.db.prepare('SELECT * FROM artifacts ORDER BY created_at DESC LIMIT ?').all(limit).map((row) => this._artifactRow(row));
    return [...decisions, ...problems, ...resolutions, ...artifacts]
      .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
      .slice(0, limit);
  }

  _projectRow(row) {
    return {
      id: row.id,
      name: row.name,
      prompt: row.prompt,
      status: row.status,
      createdAt: row.created_at,
      updatedAt: row.updated_at,
    };
  }

  _decisionRow(row) {
    return {
      id: row.id,
      projectId: row.project_id,
      phase: row.phase,
      context: row.context,
      reasoning: row.reasoning,
      outcome: row.outcome,
      title: row.title || row.context,
      rationale: row.rationale || row.reasoning,
      entryType: 'decision',
      level: 'info',
      createdAt: row.created_at,
      updatedAt: row.updated_at,
    };
  }

  _problemRow(row) {
    return {
      id: row.id,
      projectId: row.project_id,
      phase: row.phase,
      title: row.title,
      description: row.description,
      summary: row.title,
      severity: row.severity,
      status: row.status,
      attemptedResolutions: JSON.parse(row.attempted_resolutions || '[]'),
      resolutionIds: JSON.parse(row.resolution_ids || '[]'),
      resolution: row.resolution,
      entryType: 'problem',
      level: 'warn',
      createdAt: row.created_at,
      updatedAt: row.updated_at,
    };
  }

  _resolutionRow(row) {
    return {
      id: row.id,
      problemId: row.problem_id,
      projectId: row.project_id,
      phase: row.phase,
      description: row.description,
      outcome: row.outcome,
      entryType: 'resolution',
      level: 'info',
      createdAt: row.created_at,
      updatedAt: row.updated_at,
    };
  }

  _artifactRow(row) {
    return {
      id: row.id,
      projectId: row.project_id,
      phase: row.phase,
      name: row.name,
      url: row.url,
      kind: row.kind,
      entryType: 'artifact',
      level: 'info',
      createdAt: row.created_at,
      updatedAt: row.updated_at,
    };
  }
}

function createStore() {
  const dbPath = process.env.DB_PATH || path.join(process.cwd(), 'data', 'tracker.db');
  const wantSqlite = process.env.TRACKER_DB !== 'memory' && process.env.NODE_ENV !== 'test';
  if (wantSqlite && DatabaseSync) return new SqliteStore(dbPath);
  return new MemoryStore();
}

function buildProjectOverview(store, projectId) {
  const project = store.getProject(projectId);
  if (!project) return null;

  const events = store.getProjectEvents(projectId);
  const artifacts = store.listArtifacts(projectId);
  const metrics = buildProjectMetrics(project, events, artifacts);
  const stages = buildStageDetails(project, events, artifacts);
  const phaseDocumentation = stages.flatMap((stage) => stage.documents || []);
  const projectLookup = new Map([[projectId, project]]);
  const recentEvents = [...events, ...artifacts]
    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    .slice(0, 20)
    .map((event) => normalizeEvent(event, projectLookup));

  return {
    project: metrics,
    metadata: {
      createdAt: project.createdAt,
      updatedAt: project.updatedAt,
      prompt: project.prompt,
      status: metrics.derivedStatus,
    },
    stages,
    artifacts,
    phaseDocumentation,
    recentEvents,
  };
}

function createApp() {
  const app = express();
  const store = createStore();

  app.use(express.json());
  app.use(express.static(path.join(process.cwd(), 'public')));

  app.post('/api/projects', (req, res) => {
    const { name, prompt = '' } = req.body || {};
    if (!name || !String(name).trim()) {
      return res.status(400).json({ error: { code: 'VALIDATION_ERROR', message: 'name is required' } });
    }
    const project = store.createProject({ name: String(name).trim(), prompt: String(prompt || '') });
    return res.status(201).json({ project });
  });

  app.get('/api/projects', (_req, res) => {
    const projects = store.listProjects();
    return res.json({ total: projects.length, projects });
  });

  app.get('/api/dashboard', (req, res) => {
    return res.json(buildDashboardPayload(store, req.query));
  });

  app.get('/api/dashboard/stats', (_req, res) => {
    return res.json(buildDashboardPayload(store).stats);
  });

  app.get('/api/dashboard/projects', (req, res) => {
    const payload = buildDashboardPayload(store, req.query);
    return res.json({
      total: payload.projects.length,
      currentProjects: payload.currentProjects,
      historicalProjects: payload.historicalProjects,
      projects: payload.projects,
    });
  });

  app.get('/api/dashboard/recent-events', (req, res) => {
    return res.json({ recentEvents: buildDashboardPayload(store, req.query).recentEvents });
  });

  app.get('/api/projects/:id/overview', (req, res) => {
    const overview = buildProjectOverview(store, req.params.id);
    if (!overview) return res.status(404).json({ error: { code: 'NOT_FOUND' } });
    return res.json(overview);
  });

  app.get('/api/projects/:id/stages', (req, res) => {
    const overview = buildProjectOverview(store, req.params.id);
    if (!overview) return res.status(404).json({ error: { code: 'NOT_FOUND' } });
    return res.json({ projectId: req.params.id, stages: overview.stages });
  });

  app.get('/api/projects/:id/artifacts', (req, res) => {
    const project = store.getProject(req.params.id);
    if (!project) return res.status(404).json({ error: { code: 'NOT_FOUND' } });
    return res.json({ projectId: req.params.id, artifacts: store.listArtifacts(req.params.id) });
  });

  app.get('/api/projects/:id/recent-events', (req, res) => {
    const overview = buildProjectOverview(store, req.params.id);
    if (!overview) return res.status(404).json({ error: { code: 'NOT_FOUND' } });
    return res.json({ projectId: req.params.id, recentEvents: overview.recentEvents });
  });

  app.post('/api/projects/:id/artifacts', (req, res) => {
    const { phase, name, url, kind = 'link' } = req.body || {};
    if (![phase, name, url].every((value) => typeof value === 'string' && value.trim())) {
      return res.status(400).json({ error: 'phase, name, url are required' });
    }

    const artifact = store.createArtifact({
      projectId: req.params.id,
      phase: phase.trim(),
      name: name.trim(),
      url: url.trim(),
      kind: String(kind || 'link').trim(),
    });
    return res.status(201).json({ artifact });
  });

  app.post('/api/decisions', (req, res) => {
    const { projectId, title, rationale } = req.body || {};
    if (!projectId || !title || !rationale) {
      return res.status(400).json({ error: { code: 'VALIDATION_ERROR', message: 'projectId, title, rationale required' } });
    }

    const decision = store.createDecision({
      projectId,
      phase: 'unspecified',
      context: title,
      reasoning: rationale,
      outcome: title,
      title,
      rationale,
    });
    return res.status(201).json(decision);
  });

  app.post('/api/problems', (req, res) => {
    const { projectId, summary, severity } = req.body || {};
    if (!projectId || !summary || !severity) {
      return res.status(400).json({ error: { code: 'VALIDATION_ERROR', message: 'projectId, summary, severity required' } });
    }

    const problem = store.createProblem({
      projectId,
      phase: 'unspecified',
      title: summary,
      description: summary,
      summary,
      severity,
      status: 'open',
      attemptedResolutions: [],
      resolutionIds: [],
    });
    return res.status(201).json(problem);
  });

  app.patch('/api/problems/:id', (req, res) => {
    const problem = store.updateProblem(req.params.id, req.body || {});
    if (!problem) return res.status(404).json({ error: { code: 'NOT_FOUND' } });
    return res.status(200).json(problem);
  });

  app.get('/api/projects/:id/timeline', (req, res) => {
    const projectId = req.params.id;
    if (!store.getProject(projectId)) return res.json({ projectId, events: [] });
    const events = store.getProjectEvents(projectId).map((event) => {
      if (event.entryType === 'decision') return { ...event, type: 'decision' };
      if (event.entryType === 'problem') return { ...event, type: 'problem' };
      return { ...event, type: 'resolution' };
    });
    return res.json({ projectId, events });
  });

  app.post('/api/projects/:id/decisions', (req, res) => {
    const { phase, context, reasoning, outcome } = req.body || {};
    if (![phase, context, reasoning, outcome].every((value) => typeof value === 'string' && value.trim())) {
      return res.status(400).json({ error: 'phase, context, reasoning, outcome are required' });
    }

    const decision = store.createDecision({
      projectId: req.params.id,
      phase: phase.trim(),
      context: context.trim(),
      reasoning: reasoning.trim(),
      outcome: outcome.trim(),
    });
    return res.status(201).json({ decision });
  });

  app.post('/api/projects/:id/problems', (req, res) => {
    const { phase, title, description, attemptedResolutions } = req.body || {};
    if (![phase, title, description].every((value) => typeof value === 'string' && value.trim())) {
      return res.status(400).json({ error: 'phase, title, description are required' });
    }
    if (attemptedResolutions && !Array.isArray(attemptedResolutions)) {
      return res.status(400).json({ error: 'attemptedResolutions must be an array of strings' });
    }

    const problem = store.createProblem({
      projectId: req.params.id,
      phase: phase.trim(),
      title: title.trim(),
      description: description.trim(),
      attemptedResolutions: attemptedResolutions || [],
      resolutionIds: [],
    });
    return res.status(201).json({ problem });
  });

  app.post('/api/problems/:id/resolutions', (req, res) => {
    const { phase, description, outcome = 'attempted' } = req.body || {};
    if (![phase, description].every((value) => typeof value === 'string' && value.trim())) {
      return res.status(400).json({ error: 'phase and description are required' });
    }

    const payload = store.createResolution({
      problemId: req.params.id,
      phase: phase.trim(),
      description: description.trim(),
      outcome: String(outcome || 'attempted').trim(),
    });
    if (!payload) return res.status(404).json({ error: 'problem not found' });
    return res.status(201).json(payload);
  });

  app.get('/api/projects/:id/debug-logs', (req, res) => {
    const { q, phase, type, level, startDate, endDate } = req.query;
    const projectId = req.params.id;

    let entries = store.getProjectEvents(projectId);
    if (phase) entries = entries.filter((entry) => entry.phase === phase);
    if (type) entries = entries.filter((entry) => entry.entryType === type);
    if (level) entries = entries.filter((entry) => entry.level === level);
    if (startDate || endDate) entries = entries.filter((entry) => inDateRange(entry, startDate, endDate));
    if (q) entries = entries.filter((entry) => textMatches(entry, q));

    entries.sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt));
    return res.json({
      projectId,
      filters: { q, phase, type, level, startDate, endDate },
      total: entries.length,
      entries,
    });
  });

  return app;
}

module.exports = { createApp, STAGE_ORDER };
