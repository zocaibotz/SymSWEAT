const { test, expect } = require('@playwright/test');

async function seedProject(request, { name, prompt }) {
  const createProjectRes = await request.post('/api/projects', {
    data: { name, prompt },
  });
  expect(createProjectRes.ok()).toBeTruthy();
  const createProject = await createProjectRes.json();
  const projectId = createProject.project.id;

  const decisionRes = await request.post(`/api/projects/${projectId}/decisions`, {
    data: {
      phase: 'design',
      context: 'Need resilient architecture',
      reasoning: 'Reduce production incidents',
      outcome: 'Adopt canary rollout and async workers',
    },
  });
  expect(decisionRes.ok()).toBeTruthy();

  const problemRes = await request.post(`/api/projects/${projectId}/problems`, {
    data: {
      phase: 'test',
      title: 'Intermittent timeout',
      description: 'P95 latency spikes above SLA under load',
    },
  });
  expect(problemRes.ok()).toBeTruthy();

  const artifactRes = await request.post(`/api/projects/${projectId}/artifacts`, {
    data: {
      phase: 'test',
      name: 'Load test report',
      url: 'https://example.com/load-test-report',
      kind: 'report',
    },
  });
  expect(artifactRes.ok()).toBeTruthy();

  return { projectId, name };
}

test.describe('SWARMINSYM dashboard E2E', () => {
  test('dashboard shows portfolio stats and project cards', async ({ page, request }) => {
    const suffix = Date.now();
    await seedProject(request, {
      name: `E2E Current Project ${suffix}`,
      prompt: 'Validate dashboard counters and project list rendering',
    });

    await page.goto('/');

    await expect(page.getByRole('heading', { name: 'Project Intelligence Dashboard' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Portfolio Snapshot' })).toBeVisible();

    // Ensure key stat cards are rendered.
    await expect(page.locator('#stats-grid').getByText('Total projects', { exact: true })).toBeVisible();
    await expect(page.locator('#stats-grid').getByText('In progress', { exact: true })).toBeVisible();
    await expect(page.locator('#stats-grid').getByText('Open problems', { exact: true })).toBeVisible();

    // Ensure projects section has the seeded project.
    await expect(page.getByRole('heading', { name: `E2E Current Project ${suffix}` })).toBeVisible();

    // Activity feed should contain at least one event type badge.
    await expect(page.locator('.activity-item').first()).toBeVisible();
  });

  test('project details page supports stage selection and artifact links', async ({ page, request }) => {
    const suffix = Date.now();
    const { projectId, name } = await seedProject(request, {
      name: `E2E Detail Project ${suffix}`,
      prompt: 'Validate stage interactions and artifact reachability',
    });

    await page.goto(`/project.html?id=${projectId}`);

    await expect(page.getByRole('heading', { name })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Stage Progression' })).toBeVisible();

    // Click the TEST stage and verify detail panel refreshes.
    await page.locator('.stage-button', { hasText: 'TEST' }).first().click();
    await expect(page.getByRole('heading', { name: /TEST stage/i })).toBeVisible();
    await expect(page.locator('#stage-detail-body').getByRole('heading', { name: 'Intermittent timeout' })).toBeVisible();

    // Artifact should be reachable from stage details and artifacts panel.
    const stageArtifactLink = page.getByRole('link', { name: 'Open artifact' }).first();
    await expect(stageArtifactLink).toHaveAttribute('href', 'https://example.com/load-test-report');

    const artifactUrlLink = page.getByRole('link', { name: 'https://example.com/load-test-report' });
    await expect(artifactUrlLink).toBeVisible();
  });

  test('dashboard search filters projects and supports navigation to detail page', async ({ page, request }) => {
    const suffix = Date.now();
    const { projectId, name } = await seedProject(request, {
      name: `E2E Searchable ${suffix}`,
      prompt: 'Validate search and open project journey',
    });

    await page.goto('/');
    await page.locator('#project-search').fill(`Searchable ${suffix}`);

    await expect(page.getByRole('heading', { name })).toBeVisible();
    await page.getByRole('link', { name: 'Open project' }).first().click();

    await expect(page).toHaveURL((url) => url.pathname === '/project.html' && url.searchParams.get('id') === projectId);
    await expect(page.getByRole('heading', { name })).toBeVisible();
  });
});
