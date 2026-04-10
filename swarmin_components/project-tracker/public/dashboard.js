(function () {
  const state = {
    tab: 'all',
    q: '',
  };

  function formatDate(value) {
    if (!value) return 'N/A';
    return new Date(value).toLocaleString();
  }

  function formatBadge(status) {
    return String(status || 'neutral').toLowerCase().replace(/\s+/g, '-');
  }

  async function api(path, options = {}) {
    const response = await fetch(path, {
      headers: { 'content-type': 'application/json' },
      ...options,
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || 'Request failed');
    }
    return response.json();
  }

  function statCard(label, value) {
    return `
      <article class="stat-card">
        <div class="stat-label">${label}</div>
        <div class="stat-value">${value ?? 'N/A'}</div>
      </article>
    `;
  }

  function projectCard(project) {
    return `
      <article class="project-card">
        <header>
          <div>
            <h4>${project.name}</h4>
            <p class="helper-text">${project.id}</p>
          </div>
          <span class="badge ${formatBadge(project.derivedStatus)}">${project.derivedStatus}</span>
        </header>
        <div class="project-meta-grid">
          <span>Stage: <strong>${project.currentStage}</strong></span>
          <span>Updated: <strong>${formatDate(project.lastActivityAt)}</strong></span>
          <span>Artifacts: <strong>${project.totalArtifacts}</strong></span>
          <span>Decisions: <strong>${project.totalDecisions}</strong></span>
          <span>Open problems: <strong>${project.openProblems}</strong></span>
          <span>Avg duration: <strong>${project.avgDurationDays ?? 'N/A'} days</strong></span>
        </div>
        <p class="helper-text">${project.prompt || 'No prompt captured for this project yet.'}</p>
        <div class="panel-header" style="margin-top: 14px; margin-bottom: 0;">
          <span class="helper-text">Created ${formatDate(project.createdAt)}</span>
          <a class="project-link" href="/project.html?id=${encodeURIComponent(project.id)}">Open project</a>
        </div>
      </article>
    `;
  }

  function activityCard(event) {
    return `
      <article class="activity-item ${event.entryType}">
        <header>
          <div>
            <strong>${event.title}</strong>
            <p class="helper-text">${event.projectName} · ${event.phase}</p>
          </div>
          <span class="badge ${formatBadge(event.entryType === 'problem' ? 'warn' : event.entryType)}">${event.entryType}</span>
        </header>
        <p>${event.detail || 'No additional detail provided.'}</p>
        <div class="panel-header" style="margin-top: 12px; margin-bottom: 0;">
          <span class="helper-text">${formatDate(event.createdAt)}</span>
          <a class="project-link" href="/project.html?id=${encodeURIComponent(event.projectId)}">View project</a>
        </div>
      </article>
    `;
  }

  async function loadDashboard() {
    const params = new URLSearchParams();
    params.set('tab', state.tab);
    if (state.q) params.set('q', state.q);

    const payload = await api(`/api/dashboard?${params.toString()}`);
    document.getElementById('stats-grid').innerHTML = [
      statCard('Total projects', payload.stats.totalProjects),
      statCard('In progress', payload.stats.inProgress),
      statCard('Completed', payload.stats.completed),
      statCard('Stalled', payload.stats.stalled),
      statCard('Avg duration', payload.stats.avgProjectDurationDays == null ? 'N/A' : `${payload.stats.avgProjectDurationDays}d`),
      statCard('Artifacts', payload.stats.totalArtifacts),
      statCard('Decisions', payload.stats.totalDecisions),
      statCard('Open problems', payload.stats.openProblems),
    ].join('');

    document.getElementById('current-projects').innerHTML = payload.currentProjects.length
      ? payload.currentProjects.map(projectCard).join('')
      : '<div class="empty-state">No current projects match the selected filter.</div>';

    document.getElementById('historical-projects').innerHTML = payload.historicalProjects.length
      ? payload.historicalProjects.map(projectCard).join('')
      : '<div class="empty-state">No historical projects match the selected filter.</div>';

    document.getElementById('recent-activity').innerHTML = payload.recentEvents.length
      ? payload.recentEvents.map(activityCard).join('')
      : '<div class="empty-state">No activity recorded yet.</div>';

    document.getElementById('current-count').textContent = `${payload.currentProjects.length} shown`;
    document.getElementById('historical-count').textContent = `${payload.historicalProjects.length} shown`;
    document.getElementById('stats-updated').textContent = `Updated ${formatDate(new Date().toISOString())}`;
  }

  function initTabs() {
    document.getElementById('project-tabs').addEventListener('click', async (event) => {
      const button = event.target.closest('[data-tab]');
      if (!button) return;
      state.tab = button.dataset.tab;
      document.querySelectorAll('.tab').forEach((tab) => tab.classList.toggle('active', tab === button));
      await loadDashboard();
    });
  }

  function initSearch() {
    const search = document.getElementById('project-search');
    search.addEventListener('input', async () => {
      state.q = search.value.trim();
      await loadDashboard();
    });
  }

  function initCreateForm() {
    const form = document.getElementById('create-project-form');
    const message = document.getElementById('create-project-message');

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      message.textContent = '';

      const name = document.getElementById('project-name').value.trim();
      const prompt = document.getElementById('project-prompt').value.trim();
      if (!name) return;

      try {
        const payload = await api('/api/projects', {
          method: 'POST',
          body: JSON.stringify({ name, prompt }),
        });
        form.reset();
        message.textContent = `Created ${payload.project.name}.`;
        await loadDashboard();
      } catch (error) {
        message.textContent = `Failed to create project: ${error.message}`;
      }
    });
  }

  async function init() {
    initTabs();
    initSearch();
    initCreateForm();
    await loadDashboard();
  }

  init().catch((error) => {
    document.getElementById('recent-activity').innerHTML = `<div class="empty-state">Unable to load dashboard: ${error.message}</div>`;
  });
})();
