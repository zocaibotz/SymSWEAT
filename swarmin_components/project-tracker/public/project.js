(function () {
  const params = new URLSearchParams(window.location.search);
  const projectId = params.get('id');
  let selectedStageId = null;
  let cachedStages = [];

  function formatDate(value) {
    if (!value) return 'N/A';
    return new Date(value).toLocaleString();
  }

  function formatBadge(status) {
    return String(status || 'neutral').toLowerCase().replace(/\s+/g, '-');
  }

  async function api(path) {
    const response = await fetch(path);
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || 'Request failed');
    }
    return response.json();
  }

  function renderList(items, mapper) {
    if (!items.length) return '<div class="empty-state">No records captured for this section.</div>';
    return `<div class="stack">${items.map(mapper).join('')}</div>`;
  }

  function renderEventCard(item, title, body) {
    return `
      <article class="event-card">
        <header>
          <div>
            <h4>${title}</h4>
            <p class="helper-text">${item.phase} · ${formatDate(item.createdAt)}</p>
          </div>
          <span class="badge ${formatBadge(item.entryType === 'problem' && item.status !== 'resolved' ? 'open' : item.entryType)}">
            ${item.entryType}
          </span>
        </header>
        <p>${body}</p>
      </article>
    `;
  }

  function renderTimeline() {
    const timeline = document.getElementById('stage-timeline');
    timeline.innerHTML = cachedStages.length
      ? cachedStages.map((stage) => `
          <button
            type="button"
            class="stage-button ${stage.status} ${selectedStageId === stage.id ? 'active' : ''}"
            data-stage-id="${stage.id}"
          >
            <div class="panel-header" style="margin-bottom: 8px;">
              <strong>${stage.name}</strong>
              <span class="badge ${formatBadge(stage.status)}">${stage.status}</span>
            </div>
            <p class="helper-text">${stage.isCurrent ? 'Current active stage' : `Updated ${formatDate(stage.updatedAt)}`}</p>
            <div class="stage-summary">
              <span>${stage.decisions.length} decisions</span>
              <span>${stage.problems.length} problems</span>
              <span>${stage.artifacts.length} artifacts</span>
              <span>${(stage.documents || []).length} docs</span>
              <span>${(stage.linearIssues || []).length} linear</span>
            </div>
          </button>
        `).join('')
      : '<div class="empty-state">No stage activity recorded yet.</div>';

    timeline.querySelectorAll('[data-stage-id]').forEach((button) => {
      button.addEventListener('click', () => {
        selectedStageId = button.dataset.stageId;
        renderTimeline();
        renderStageDetail();
      });
    });
  }

  function renderStageDetail() {
    const stage = cachedStages.find((item) => item.id === selectedStageId) || cachedStages[0];
    const title = document.getElementById('stage-detail-title');
    const meta = document.getElementById('stage-detail-meta');
    const body = document.getElementById('stage-detail-body');

    if (!stage) {
      title.textContent = 'Stage details';
      meta.textContent = '';
      body.innerHTML = '<div class="empty-state">No stage selected.</div>';
      return;
    }

    title.textContent = `${stage.name} stage`;
    meta.textContent = `${stage.status} · ${stage.totalEvents} events · ${stage.artifacts.length} artifacts · ${(stage.documents || []).length} docs · ${(stage.linearIssues || []).length} linear links · last updated ${formatDate(stage.updatedAt)}`;
    body.innerHTML = [
      renderList(stage.decisions, (item) => renderEventCard(item, item.context || item.title, item.outcome || item.reasoning)),
      renderList(stage.problems, (item) => renderEventCard(item, item.title, item.description)),
      renderList(stage.resolutions, (item) => renderEventCard(item, 'Resolution', item.description)),
      (stage.documents || []).length
        ? `<div class="stack">${stage.documents.map((doc) => `
            <article class="artifact-card">
              <header>
                <div>
                  <h4>${doc.name}</h4>
                  <p class="helper-text">${doc.phase} · ${doc.kind}</p>
                </div>
                <span class="badge neutral">doc</span>
              </header>
              <p><a class="artifact-link" href="${doc.url}" target="_blank" rel="noreferrer">Open markdown</a></p>
            </article>
          `).join('')}</div>`
        : '<div class="empty-state">No stage markdown docs found in GitHub mapping.</div>',
      (stage.linearIssues || []).length
        ? `<div class="stack">${stage.linearIssues.map((item) => `
            <article class="artifact-card">
              <header>
                <div>
                  <h4>${item.name}</h4>
                  <p class="helper-text">${item.key} · ${item.kind}</p>
                </div>
                <span class="badge neutral">linear</span>
              </header>
              <p><a class="artifact-link" href="${item.url}" target="_blank" rel="noreferrer">Open Linear issue</a></p>
            </article>
          `).join('')}</div>`
        : '<div class="empty-state">No Linear issue links detected for this project.</div>',
      stage.artifacts.length
        ? `<div class="stack">${stage.artifacts.map((artifact) => `
            <article class="artifact-card">
              <header>
                <div>
                  <h4>${artifact.name}</h4>
                  <p class="helper-text">${artifact.phase} · ${artifact.kind}</p>
                </div>
                <span class="badge neutral">artifact</span>
              </header>
              <p><a class="artifact-link" href="${artifact.url}" target="_blank" rel="noreferrer">Open artifact</a></p>
            </article>
          `).join('')}</div>`
        : '<div class="empty-state">No stage artifacts linked yet.</div>',
    ].join('');
  }

  function renderArtifacts(artifacts, docs = [], linearIssues = []) {
    const combined = [
      ...docs.map((doc) => ({ ...doc, __type: 'doc' })),
      ...linearIssues.map((item) => ({ ...item, __type: 'linear' })),
      ...artifacts.map((artifact) => ({ ...artifact, __type: 'artifact' })),
    ];

    document.getElementById('artifact-cards').innerHTML = combined.length
      ? combined.map((item) => `
          <article class="artifact-card">
            <header>
              <div>
                <h4>${item.name}</h4>
                <p class="helper-text">${item.phase} · ${item.kind}</p>
              </div>
              <span class="badge neutral">${item.__type}</span>
            </header>
            <p><a class="artifact-link" href="${item.url}" target="_blank" rel="noreferrer">${item.url}</a></p>
          </article>
        `).join('')
      : '<div class="empty-state">No artifacts or markdown docs have been attached to this project.</div>';
  }

  function renderActivity(events) {
    document.getElementById('project-activity').innerHTML = events.length
      ? events.map((event) => `
          <article class="activity-item ${event.entryType}">
            <header>
              <div>
                <strong>${event.title}</strong>
                <p class="helper-text">${event.phase} · ${formatDate(event.createdAt)}</p>
              </div>
              <span class="badge ${formatBadge(event.entryType === 'problem' ? 'warn' : event.entryType)}">${event.entryType}</span>
            </header>
            <p>${event.detail || 'No additional detail.'}</p>
          </article>
        `).join('')
      : '<div class="empty-state">No recent events for this project yet.</div>';
  }

  async function init() {
    if (!projectId) {
      document.getElementById('project-title').textContent = 'Project not found';
      document.getElementById('stage-detail-body').innerHTML = '<div class="empty-state">A project id is required in the query string.</div>';
      return;
    }

    const overview = await api(`/api/projects/${encodeURIComponent(projectId)}/overview`);
    cachedStages = overview.stages || [];
    selectedStageId = cachedStages.find((stage) => stage.isCurrent)?.id || cachedStages[0]?.id || null;

    document.title = `${overview.project.name} · SWARMINSYM Tracker`;
    document.getElementById('project-title').textContent = overview.project.name;
    document.getElementById('project-status-badge').textContent = overview.project.derivedStatus;
    document.getElementById('project-status-badge').className = `badge ${formatBadge(overview.project.derivedStatus)}`;
    document.getElementById('project-meta').innerHTML = [
      `<span>ID ${overview.project.id}</span>`,
      `<span>Current stage ${overview.project.currentStage}</span>`,
      `<span>Artifacts ${overview.project.totalArtifacts}</span>`,
      `<span>Decisions ${overview.project.totalDecisions}</span>`,
      `<span>Open problems ${overview.project.openProblems}</span>`,
      `<span>Updated ${formatDate(overview.project.updatedAt)}</span>`,
    ].join('');

    renderTimeline();
    renderStageDetail();
    const linearIssues = (overview.stages || []).flatMap((stage) => stage.linearIssues || []);
    const uniqueLinearIssues = [...new Map(linearIssues.map((item) => [item.id, item])).values()];
    renderArtifacts(overview.artifacts || [], overview.phaseDocumentation || [], uniqueLinearIssues);
    renderActivity(overview.recentEvents || []);
  }

  init().catch((error) => {
    document.getElementById('project-title').textContent = 'Unable to load project';
    document.getElementById('stage-detail-body').innerHTML = `<div class="empty-state">${error.message}</div>`;
  });
})();
