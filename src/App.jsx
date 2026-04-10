import React, { useEffect, useMemo, useState } from 'react';

const API_BASE = (globalThis && globalThis.__SWEAT_API_BASE__) || '';

const theme = {
  bg: '#0a1120',
  bgElevated: '#111b2d',
  bgPanel: '#16233b',
  border: '#31476a',
  text: '#e7eefb',
  textMuted: '#9fb2cf',
  accent: '#5ea3ff',
  success: '#26c281',
  warn: '#f3b544',
  danger: '#f06d6d',
  fontHeading: 'Space Grotesk, Inter, sans-serif',
  fontBody: 'Manrope, Arial, sans-serif',
  fontMono: 'JetBrains Mono, monospace',
};

const stageLabels = {
  requirement_master: 'Requirement Master',
  specify: 'Specify',
  plan: 'Plan',
  tasks: 'Tasks',
  architect: 'Architect',
  pixel: 'Pixel',
  frontman: 'Frontman',
  code_smith: 'Code Smith',
  review: 'Review',
  ci_deploy_automator: 'CI / Deploy / Automator',
};

function fmt(text) {
  return (text || '').toString();
}

function severityFromBlocker(blocker) {
  const kind = fmt(blocker?.kind).toLowerCase();
  if (kind.includes('failed') || kind.includes('validation_error') || kind.includes('blocked')) return 'high';
  if (kind.includes('retry') || kind.includes('run_status')) return 'medium';
  return 'low';
}

function severityColor(level) {
  if (level === 'high') return theme.danger;
  if (level === 'medium') return theme.warn;
  return theme.success;
}

function summarizeAlerts(summary, liveEvents) {
  // Threshold tuning (fast-shippable defaults)
  // - CRITICAL: sustained/high-confidence failure signals
  // - WATCH: early warning signals
  const THRESHOLDS = {
    criticalHighBlockers: 2,
    criticalRecentFailures: 3,
    watchMediumBlockers: 1,
    watchRecentFailures: 1,
  };

  const blockers = summary?.blockers || [];
  const high = blockers.filter((b) => severityFromBlocker(b) === 'high').length;
  const medium = blockers.filter((b) => severityFromBlocker(b) === 'medium').length;
  const recentFailures = (liveEvents || []).slice(-20).filter((e) => {
    const type = fmt(e?.event?.event_type).toLowerCase();
    return type.includes('error') || type.includes('fail');
  }).length;

  let health = 'stable';
  if (high >= THRESHOLDS.criticalHighBlockers || recentFailures >= THRESHOLDS.criticalRecentFailures) {
    health = 'critical';
  } else if (
    high > 0 ||
    medium >= THRESHOLDS.watchMediumBlockers ||
    recentFailures >= THRESHOLDS.watchRecentFailures
  ) {
    health = 'watch';
  }

  return {
    health,
    high,
    medium,
    recentFailures,
    thresholds: THRESHOLDS,
  };
}

async function api(path, opts = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body || res.statusText}`);
  }
  return res.json();
}

function Header({ onHome, activeProject }) {
  return (
    <header style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '14px 24px',
      borderBottom: `1px solid ${theme.border}`,
      background: 'linear-gradient(95deg, #101b30, #15253e 60%, #193458)',
      position: 'sticky',
      top: 0,
      zIndex: 3,
    }}>
      <button onClick={onHome} style={{
        color: theme.text,
        background: 'transparent',
        border: 0,
        cursor: 'pointer',
        fontFamily: theme.fontHeading,
        fontSize: 20,
        letterSpacing: 0.6,
      }}>SWEAT Command Center</button>
      <div style={{ color: theme.textMuted, fontSize: 13, fontFamily: theme.fontMono }}>
        {activeProject ? `Project: ${activeProject}` : 'Fleet Monitor'}
      </div>
    </header>
  );
}

function ProjectCard({ project, onOpen }) {
  const isDone = project.status === 'completed';
  const statusColor = isDone ? theme.success : theme.accent;
  const blockers = (project.blockers || []).length;
  const alert = summarizeAlerts(project, []);

  return (
    <button onClick={() => onOpen(project.project_id)} style={{
      textAlign: 'left',
      background: `linear-gradient(170deg, ${theme.bgPanel}, #1a2c49)`,
      border: `1px solid ${theme.border}`,
      borderRadius: 14,
      padding: 16,
      cursor: 'pointer',
      color: theme.text,
      width: '100%',
      boxShadow: '0 10px 25px rgba(0,0,0,0.22)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <strong style={{ fontFamily: theme.fontHeading, fontSize: 17 }}>{project.display_name}</strong>
        <span style={{ color: statusColor, fontSize: 12, fontFamily: theme.fontMono }}>{project.status}</span>
      </div>
      <div style={{ marginTop: 8, color: theme.textMuted, fontSize: 13 }}>
        Stage: {stageLabels[project.current_stage] || project.current_stage}
      </div>
      <div style={{ marginTop: 8, color: theme.textMuted, fontSize: 12 }}>
        Last update: {fmt(project.last_updated_utc) || 'n/a'}
      </div>
      <div style={{ marginTop: 10, display: 'flex', gap: 12, fontSize: 12, color: theme.textMuted, alignItems: 'center', flexWrap: 'wrap' }}>
        <span>Runs: {project.kpis?.runs_total || 0}</span>
        <span>Events: {project.kpis?.events_total || 0}</span>
        <span style={{ color: blockers ? theme.danger : theme.success }}>Blockers: {blockers}</span>
        <span style={{
          border: `1px solid ${severityColor(alert.health === 'critical' ? 'high' : (alert.health === 'watch' ? 'medium' : 'low'))}`,
          color: severityColor(alert.health === 'critical' ? 'high' : (alert.health === 'watch' ? 'medium' : 'low')),
          borderRadius: 999,
          padding: '2px 8px',
          fontFamily: theme.fontMono,
          fontSize: 11,
        }}>
          {alert.health.toUpperCase()}
        </span>
      </div>
    </button>
  );
}

function Dashboard({ data, onOpen }) {
  const inProgress = data.projects.filter((p) => p.status !== 'completed');
  const completed = data.projects.filter((p) => p.status === 'completed');

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 18 }}>
        <h2 style={{ margin: 0, fontFamily: theme.fontHeading, color: theme.text }}>Project Monitoring Dashboard</h2>
        <div style={{ color: theme.textMuted, marginTop: 6, fontSize: 14 }}>
          In-progress {data.in_progress_count} | Completed {data.completed_count} | Total {data.total_count}
        </div>
      </div>

      <h3 style={{ color: theme.text, fontFamily: theme.fontHeading }}>In Progress</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(290px, 1fr))', gap: 14, marginBottom: 24 }}>
        {inProgress.map((project) => <ProjectCard key={project.project_id} project={project} onOpen={onOpen} />)}
        {!inProgress.length && <div style={{ color: theme.textMuted }}>No in-progress projects.</div>}
      </div>

      <h3 style={{ color: theme.text, fontFamily: theme.fontHeading }}>Completed</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(290px, 1fr))', gap: 14 }}>
        {completed.map((project) => <ProjectCard key={project.project_id} project={project} onOpen={onOpen} />)}
        {!completed.length && <div style={{ color: theme.textMuted }}>No completed projects.</div>}
      </div>
    </div>
  );
}

function Pipeline({ steps }) {
  return (
    <div style={{
      border: `1px solid ${theme.border}`,
      borderRadius: 14,
      padding: 12,
      background: theme.bgElevated,
      overflowX: 'auto',
      marginBottom: 14,
    }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(10, minmax(110px, 1fr))', gap: 10, minWidth: 1150 }}>
        {steps.map((step) => {
          const color = step.status === 'completed' ? theme.success : (step.status === 'active' ? theme.accent : theme.textMuted);
          return (
            <div key={step.stage} style={{
              border: `1px solid ${color}`,
              borderRadius: 10,
              padding: 8,
              background: step.status === 'active' ? '#20385f' : '#122038',
            }}>
              <div style={{ fontSize: 11, color, fontFamily: theme.fontMono }}>{step.status.toUpperCase()}</div>
              <div style={{ marginTop: 4, fontSize: 13, color: theme.text }}>{stageLabels[step.stage] || step.stage}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function InterviewPanel({ interview, projectId, onAnswered }) {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const pending = interview?.pending_questions || [];

  useEffect(() => {
    if (!question && pending[0]) {
      setQuestion(pending[0]);
    }
  }, [pending, question]);

  async function submit() {
    if (!question || !answer.trim()) return;
    setSubmitting(true);
    try {
      await api(`/api/monitoring/projects/${projectId}/interview/answer`, {
        method: 'POST',
        body: JSON.stringify({ question, answer, author: 'operator_ui' }),
      });
      setAnswer('');
      onAnswered();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section style={{ border: `1px solid ${theme.border}`, borderRadius: 12, padding: 12, background: theme.bgElevated }}>
      <h4 style={{ margin: '0 0 8px 0', color: theme.text, fontFamily: theme.fontHeading }}>Req Master Interview</h4>
      <div style={{ fontSize: 12, color: theme.textMuted, marginBottom: 8 }}>
        Status: {interview?.status || 'unknown'} | Pending: {pending.length} | Answered: {interview?.answered_count || 0}
      </div>
      {pending.length > 0 ? (
        <>
          <select value={question} onChange={(e) => setQuestion(e.target.value)} style={{ width: '100%', marginBottom: 8, background: theme.bgPanel, color: theme.text, border: `1px solid ${theme.border}`, borderRadius: 8, padding: 8 }}>
            {pending.map((q) => <option key={q} value={q}>{q}</option>)}
          </select>
          <textarea value={answer} onChange={(e) => setAnswer(e.target.value)} rows={3} placeholder="Type your answer" style={{ width: '100%', marginBottom: 8, background: theme.bgPanel, color: theme.text, border: `1px solid ${theme.border}`, borderRadius: 8, padding: 8 }} />
          <button onClick={submit} disabled={submitting} style={{ background: theme.accent, color: '#fff', border: 0, padding: '8px 12px', borderRadius: 8, cursor: 'pointer' }}>
            {submitting ? 'Submitting...' : 'Submit Answer'}
          </button>
        </>
      ) : (
        <div style={{ color: theme.success, fontSize: 13 }}>No pending req_master interview questions.</div>
      )}
    </section>
  );
}

function ArtifactsPanel({ artifacts, projectId }) {
  const [selected, setSelected] = useState(null);
  const [preview, setPreview] = useState(null);
  const [err, setErr] = useState('');

  async function openArtifact(key) {
    setSelected(key);
    setErr('');
    try {
      const data = await api(`/api/monitoring/projects/${projectId}/artifacts/${encodeURIComponent(key)}`);
      setPreview(data);
    } catch (e) {
      setErr(e.message);
      setPreview(null);
    }
  }

  return (
    <section style={{ border: `1px solid ${theme.border}`, borderRadius: 12, padding: 12, background: theme.bgElevated }}>
      <h4 style={{ margin: '0 0 8px 0', color: theme.text, fontFamily: theme.fontHeading }}>Artifact Registry</h4>
      <div style={{ display: 'grid', gap: 8, maxHeight: 190, overflowY: 'auto', marginBottom: 10 }}>
        {artifacts.map((artifact) => (
          <button key={artifact.key} onClick={() => openArtifact(artifact.key)} style={{
            textAlign: 'left',
            border: `1px solid ${selected === artifact.key ? theme.accent : theme.border}`,
            background: theme.bgPanel,
            color: theme.text,
            borderRadius: 8,
            padding: 8,
            cursor: 'pointer',
          }}>
            <div style={{ fontSize: 13 }}>{artifact.key}</div>
            <div style={{ fontSize: 11, color: theme.textMuted }}>{artifact.path}</div>
          </button>
        ))}
        {!artifacts.length && <div style={{ color: theme.textMuted }}>No artifacts registered.</div>}
      </div>
      {err && <div style={{ color: theme.danger, fontSize: 12 }}>{err}</div>}
      {preview?.artifact && (
        <div style={{ border: `1px solid ${theme.border}`, borderRadius: 8, background: '#0f1a2e', padding: 8 }}>
          <div style={{ color: theme.textMuted, fontSize: 12, marginBottom: 6 }}>{preview.resolved_path || preview.artifact.path}</div>
          <pre style={{ margin: 0, whiteSpace: 'pre-wrap', color: theme.text, fontSize: 11, maxHeight: 170, overflowY: 'auto' }}>
            {preview.preview || '[No preview available]'}
          </pre>
        </div>
      )}
    </section>
  );
}

function Timeline({ events }) {
  return (
    <section style={{ border: `1px solid ${theme.border}`, borderRadius: 12, padding: 12, background: theme.bgElevated }}>
      <h4 style={{ margin: '0 0 8px 0', color: theme.text, fontFamily: theme.fontHeading }}>Timeline / History</h4>
      <div style={{ maxHeight: 320, overflowY: 'auto', display: 'grid', gap: 8 }}>
        {events.slice().reverse().map((event) => (
          <div key={event.event_id} style={{ border: `1px solid ${theme.border}`, borderRadius: 8, padding: 8, background: '#13213a' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: theme.textMuted }}>
              <span>{event.ts_utc}</span>
              <span>{event.run_id}</span>
            </div>
            <div style={{ marginTop: 4, fontSize: 12, color: theme.text }}>
              {event.node} :: {event.event_type}
            </div>
            <div style={{ marginTop: 4, fontSize: 12, color: theme.textMuted }}>{fmt(event.summary)}</div>
          </div>
        ))}
        {!events.length && <div style={{ color: theme.textMuted }}>No timeline entries.</div>}
      </div>
    </section>
  );
}

function RightRail({ summary, stageDetails, liveEvents }) {
  const kpis = summary.kpis || {};
  const blockers = summary.blockers || [];
  const alerts = summarizeAlerts(summary, liveEvents);
  const streamFresh = (liveEvents || []).length > 0;

  return (
    <div style={{ display: 'grid', gap: 12 }}>
      <section style={{ border: `1px solid ${theme.border}`, borderRadius: 12, padding: 12, background: theme.bgElevated }}>
        <h4 style={{ margin: '0 0 8px 0', color: theme.text, fontFamily: theme.fontHeading }}>Observability Health</h4>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <span style={{
            border: `1px solid ${severityColor(alerts.health === 'critical' ? 'high' : (alerts.health === 'watch' ? 'medium' : 'low'))}`,
            color: severityColor(alerts.health === 'critical' ? 'high' : (alerts.health === 'watch' ? 'medium' : 'low')),
            borderRadius: 999,
            padding: '2px 10px',
            fontFamily: theme.fontMono,
            fontSize: 11,
          }}>
            {alerts.health.toUpperCase()}
          </span>
          <span style={{ color: theme.textMuted, fontSize: 12 }}>High: {alerts.high}</span>
          <span style={{ color: theme.textMuted, fontSize: 12 }}>Medium: {alerts.medium}</span>
          <span style={{ color: theme.textMuted, fontSize: 12 }}>Recent failures: {alerts.recentFailures}</span>
          <span style={{ color: streamFresh ? theme.success : theme.warn, fontSize: 12 }}>
            Stream freshness: {streamFresh ? 'live' : 'idle'}
          </span>
        </div>
      </section>
      <section style={{ border: `1px solid ${theme.border}`, borderRadius: 12, padding: 12, background: theme.bgElevated }}>
        <h4 style={{ margin: '0 0 8px 0', color: theme.text, fontFamily: theme.fontHeading }}>KPIs</h4>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, fontSize: 12 }}>
          <div style={{ color: theme.textMuted }}>Runs Total</div><div style={{ color: theme.text }}>{kpis.runs_total || 0}</div>
          <div style={{ color: theme.textMuted }}>Runs Running</div><div style={{ color: theme.text }}>{kpis.runs_running || 0}</div>
          <div style={{ color: theme.textMuted }}>Runs Failed</div><div style={{ color: theme.danger }}>{kpis.runs_failed || 0}</div>
          <div style={{ color: theme.textMuted }}>Events Total</div><div style={{ color: theme.text }}>{kpis.events_total || 0}</div>
          <div style={{ color: theme.textMuted }}>Gates</div><div style={{ color: theme.text }}>{kpis.gates_passed || 0} / {kpis.gates_total || 0}</div>
          <div style={{ color: theme.textMuted }}>Stage Events</div><div style={{ color: theme.text }}>{stageDetails.event_count || 0}</div>
        </div>
      </section>

      <section style={{ border: `1px solid ${theme.border}`, borderRadius: 12, padding: 12, background: theme.bgElevated }}>
        <h4 style={{ margin: '0 0 8px 0', color: theme.text, fontFamily: theme.fontHeading }}>Alert Rules</h4>
        <div style={{ display: 'grid', gap: 6, fontSize: 12, color: theme.textMuted }}>
          <div>• CRITICAL when High blockers ≥ {alerts.thresholds.criticalHighBlockers} or recent failures ≥ {alerts.thresholds.criticalRecentFailures}</div>
          <div>• WATCH when any High blocker exists, Medium blockers ≥ {alerts.thresholds.watchMediumBlockers}, or recent failures ≥ {alerts.thresholds.watchRecentFailures}</div>
          <div>• STABLE when none of the above conditions are met</div>
        </div>
      </section>

      <section style={{ border: `1px solid ${theme.border}`, borderRadius: 12, padding: 12, background: theme.bgElevated }}>
        <h4 style={{ margin: '0 0 8px 0', color: theme.text, fontFamily: theme.fontHeading }}>Blockers / Failures</h4>
        <div style={{ display: 'grid', gap: 8, maxHeight: 170, overflowY: 'auto' }}>
          {blockers.map((b, idx) => {
            const sev = severityFromBlocker(b);
            const color = severityColor(sev);
            return (
              <div key={`${b.kind}-${idx}`} style={{ border: `1px solid ${color}`, borderRadius: 8, padding: 8, background: '#3c1f2a' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ color, fontSize: 12 }}>{b.kind}</div>
                  <span style={{ color, fontSize: 10, fontFamily: theme.fontMono }}>{sev.toUpperCase()}</span>
                </div>
                <div style={{ color: theme.textMuted, fontSize: 11 }}>{fmt(b.detail || b.status)} {b.ts_utc || b.ended_at_utc || ''}</div>
              </div>
            );
          })}
          {!blockers.length && <div style={{ color: theme.success, fontSize: 12 }}>No active blockers detected.</div>}
        </div>
      </section>

      <section style={{ border: `1px solid ${theme.border}`, borderRadius: 12, padding: 12, background: theme.bgElevated }}>
        <h4 style={{ margin: '0 0 8px 0', color: theme.text, fontFamily: theme.fontHeading }}>Live Event Stream</h4>
        <div style={{ maxHeight: 220, overflowY: 'auto', display: 'grid', gap: 6 }}>
          {liveEvents.slice().reverse().map((item, idx) => (
            <div key={`${item.event?.event_id || 'live'}-${idx}`} style={{ borderBottom: `1px solid ${theme.border}`, paddingBottom: 6 }}>
              <div style={{ color: theme.text, fontSize: 12 }}>{item.event?.node} / {item.event?.event_type}</div>
              <div style={{ color: theme.textMuted, fontSize: 11 }}>{item.event?.ts_utc}</div>
            </div>
          ))}
          {!liveEvents.length && <div style={{ color: theme.textMuted }}>Waiting for events...</div>}
        </div>
      </section>
    </div>
  );
}

function ProjectDetails({ data, onBack, onRefresh, liveEvents }) {
  const summary = data.summary;
  const stageDetails = data.stage_details;

  return (
    <div style={{ padding: 16 }}>
      <button onClick={onBack} style={{ marginBottom: 12, background: 'transparent', border: `1px solid ${theme.border}`, color: theme.text, borderRadius: 8, padding: '6px 10px', cursor: 'pointer' }}>Back to Dashboard</button>

      <div style={{ marginBottom: 10 }}>
        <h2 style={{ margin: 0, color: theme.text, fontFamily: theme.fontHeading }}>{summary.display_name}</h2>
        <div style={{ color: theme.textMuted, fontSize: 13, marginTop: 4 }}>
          Status: {summary.status} | Stage: {stageLabels[summary.current_stage] || summary.current_stage} | Run: {summary.latest_run_id || 'n/a'}
        </div>
      </div>

      <Pipeline steps={data.pipeline} />

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 2.2fr) minmax(280px, 1fr)', gap: 12 }}>
        <div style={{ display: 'grid', gap: 12 }}>
          <section style={{ border: `1px solid ${theme.border}`, borderRadius: 12, padding: 12, background: theme.bgElevated }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h4 style={{ margin: 0, color: theme.text, fontFamily: theme.fontHeading }}>Current Stage Deep Details</h4>
              <button onClick={onRefresh} style={{ background: theme.accent, color: '#fff', border: 0, borderRadius: 8, padding: '6px 10px', cursor: 'pointer' }}>Refresh</button>
            </div>
            <div style={{ marginTop: 10, color: theme.textMuted, fontSize: 13 }}>
              Stage Event Count: {stageDetails.event_count || 0}
            </div>
            <pre style={{ marginTop: 10, background: '#0f1a2e', border: `1px solid ${theme.border}`, borderRadius: 8, padding: 8, whiteSpace: 'pre-wrap', color: theme.text, fontSize: 11, maxHeight: 220, overflowY: 'auto' }}>
              {JSON.stringify(stageDetails.latest_event || {}, null, 2)}
            </pre>
          </section>

          <Timeline events={data.timeline || []} />

          <InterviewPanel interview={data.interview} projectId={summary.project_id} onAnswered={onRefresh} />
          <ArtifactsPanel artifacts={data.artifacts || []} projectId={summary.project_id} />
        </div>

        <RightRail summary={summary} stageDetails={stageDetails} liveEvents={liveEvents} />
      </div>
    </div>
  );
}

export default function App() {
  const [dashboard, setDashboard] = useState({ projects: [], in_progress_count: 0, completed_count: 0, total_count: 0 });
  const [selectedProject, setSelectedProject] = useState('');
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [streamStatus, setStreamStatus] = useState('disconnected');
  const [liveEvents, setLiveEvents] = useState([]);

  async function loadDashboard() {
    const data = await api('/api/monitoring/projects');
    setDashboard(data);
  }

  async function loadDetails(projectId) {
    const data = await api(`/api/monitoring/projects/${projectId}`);
    setDetails(data);
  }

  async function refreshAll(projectId = selectedProject) {
    setError('');
    try {
      await loadDashboard();
      if (projectId) {
        await loadDetails(projectId);
      }
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => {
    let alive = true;
    setLoading(true);
    refreshAll().finally(() => {
      if (alive) setLoading(false);
    });

    const timer = setInterval(() => {
      refreshAll();
    }, 10000);

    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    const projectQ = selectedProject ? `?project_id=${encodeURIComponent(selectedProject)}` : '';
    const es = new EventSource(`${API_BASE}/api/monitoring/stream${projectQ}`);

    es.onopen = () => setStreamStatus('connected');
    es.onerror = () => setStreamStatus('error');
    es.addEventListener('heartbeat', () => {
      setStreamStatus('connected');
    });

    es.addEventListener('snapshot', (msg) => {
      try {
        const payload = JSON.parse(msg.data);
        if (!selectedProject && payload.projects) {
          setDashboard((prev) => ({ ...prev, projects: payload.projects }));
        }
      } catch {
        // ignore malformed snapshot
      }
    });

    es.addEventListener('run_event', (msg) => {
      try {
        const payload = JSON.parse(msg.data);
        setLiveEvents((prev) => [...prev.slice(-149), payload]);
      } catch {
        // ignore malformed event
      }
    });

    return () => {
      es.close();
      setStreamStatus('disconnected');
    };
  }, [selectedProject]);

  useEffect(() => {
    if (!selectedProject) return;
    refreshAll(selectedProject);
  }, [selectedProject]);

  const currentProjectName = useMemo(() => {
    if (!selectedProject) return '';
    const project = dashboard.projects.find((p) => p.project_id === selectedProject);
    return project?.display_name || selectedProject;
  }, [selectedProject, dashboard.projects]);

  return (
    <div style={{
      minHeight: '100vh',
      background: 'radial-gradient(circle at 15% 0%, #21365b 0, #0a1120 52%)',
      color: theme.text,
      fontFamily: theme.fontBody,
    }}>
      <Header onHome={() => setSelectedProject('')} activeProject={currentProjectName} />

      <div style={{ padding: '8px 24px', color: streamStatus === 'connected' ? theme.success : theme.warn, fontSize: 12, fontFamily: theme.fontMono }}>
        Live Stream: {streamStatus}
      </div>

      {error && (
        <div style={{ margin: '0 24px 12px', border: `1px solid ${theme.danger}`, color: theme.danger, borderRadius: 10, padding: 10 }}>
          API Error: {error}
        </div>
      )}

      {loading ? (
        <div style={{ padding: 24, color: theme.textMuted }}>Loading monitoring data...</div>
      ) : selectedProject && details ? (
        <ProjectDetails
          data={details}
          onBack={() => setSelectedProject('')}
          onRefresh={() => refreshAll(selectedProject)}
          liveEvents={liveEvents}
        />
      ) : (
        <Dashboard data={dashboard} onOpen={setSelectedProject} />
      )}
    </div>
  );
}
