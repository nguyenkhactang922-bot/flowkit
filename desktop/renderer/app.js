'use strict';

const SECTION_LABELS = Object.freeze({
  authorityProvenance: 'Authority / provenance',
  profileResolution: 'Profile resolution',
  storyHierarchy: 'Story hierarchy',
  shotTrace: 'Shot trace',
  stateReference: 'State / reference',
  jobsQaRepair: 'Jobs / QA / repair',
  ambiguityRecovery: 'Ambiguity / recovery',
  evidenceStatus: 'Evidence status',
});

function setText(target, value) {
  target.textContent = String(value);
}

function renderItem(item) {
  const node = document.createElement('article');
  node.className = 'view-item';

  const heading = document.createElement('div');
  heading.className = 'view-item-heading';
  const label = document.createElement('strong');
  setText(label, item.label);
  const state = document.createElement('span');
  state.className = 'state';
  setText(state, item.state);
  heading.append(label, state);
  node.append(heading);

  const ref = document.createElement('div');
  ref.className = 'muted';
  setText(
    ref,
    item.canonicalRef
      ? `${item.canonicalRef.logicalId}@${item.canonicalRef.versionId}`
      : item.authority || 'presentation-only'
  );
  node.append(ref);

  if (item.provenanceRefs.length > 0) {
    const evidence = document.createElement('div');
    evidence.className = 'muted';
    setText(evidence, `evidence: ${item.provenanceRefs.join(', ')}`);
    node.append(evidence);
  }
  return node;
}

function renderModel(model) {
  const output = document.querySelector('#studio-output');
  output.replaceChildren();

  const summary = document.createElement('section');
  summary.className = 'summary';
  const title = document.createElement('h2');
  setText(title, model.project.label);
  const meta = document.createElement('p');
  meta.className = 'muted';
  const profile = model.project.activeProfileRef
    ? `${model.project.activeProfileRef.logicalId}@${model.project.activeProfileRef.versionId}`
    : 'none';
  setText(
    meta,
    `${model.sourceKind} · view-model v${model.readModelVersion} · ${model.project.workflowState} · profile ${profile}`
  );
  summary.append(title, meta);
  output.append(summary);

  const grid = document.createElement('div');
  grid.className = 'section-grid';
  for (const [key, label] of Object.entries(SECTION_LABELS)) {
    const section = model.sections[key];
    const card = document.createElement('section');
    card.className = 'section-card';
    const header = document.createElement('div');
    header.className = 'section-header';
    const heading = document.createElement('h3');
    setText(heading, label);
    const status = document.createElement('span');
    status.className = 'state';
    setText(status, section.status);
    header.append(heading, status);
    card.append(header);

    if (section.items.length === 0) {
      const empty = document.createElement('p');
      empty.className = 'muted';
      setText(empty, 'No view items.');
      card.append(empty);
    } else {
      for (const item of section.items.slice(0, 8)) {
        card.append(renderItem(item));
      }
    }
    grid.append(card);
  }
  output.append(grid);
}

async function refreshBridgeStatus() {
  const badge = document.querySelector('#bridge-status');
  try {
    const response = await window.flowkitHost.productionUtility.getBridgeStatus();
    setText(badge, response.ok ? 'Utility READY' : 'Utility unavailable');
    badge.dataset.state = response.ok ? 'ready' : 'blocked';
  } catch (_error) {
    setText(badge, 'Utility unavailable');
    badge.dataset.state = 'blocked';
  }
}

async function loadStudioModel(projectId) {
  const status = document.querySelector('#read-model-status');
  const output = document.querySelector('#studio-output');
  setText(status, 'Loading typed Studio application view…');
  output.replaceChildren();
  try {
    const response = await window.flowkitHost.studio.getApplicationReadModel(projectId);
    if (!response.ok || !response.data) {
      const code = response.error && response.error.code
        ? response.error.code
        : 'APPLICATION_READ_MODEL_UNAVAILABLE';
      throw new Error(code);
    }
    renderModel(response.data);
    setText(status, 'Canonical application read model loaded.');
    status.dataset.state = 'ready';
  } catch (error) {
    const code = error instanceof Error ? error.message : 'APPLICATION_READ_MODEL_UNAVAILABLE';
    setText(
      status,
      `Canonical application read model unavailable (${code}). No fake or legacy snapshot was promoted to Studio authority.`
    );
    status.dataset.state = 'blocked';
  }
}

window.addEventListener('DOMContentLoaded', () => {
  void refreshBridgeStatus();
  const form = document.querySelector('#project-form');
  const input = document.querySelector('#project-id');
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const projectId = input.value.trim();
    if (!projectId) {
      setText(document.querySelector('#read-model-status'), 'Project ID is required.');
      return;
    }
    void loadStudioModel(projectId);
  });
});
