const $ = (selector) => document.querySelector(selector);
const commandInput = $('#command-input');
const svgNamespace = 'http://www.w3.org/2000/svg';
let currentSuggestion = '';
let isSending = false;

const stateLabels = {
  sin_seleccion: 'Sin taladro seleccionado',
  seleccionado: 'Taladro seleccionado',
  consultado: 'Plan consultado',
  preparado: 'Preparación lista',
  confirmacion_pendiente: 'Confirmación requerida',
  movimiento_en_curso: 'Movimiento en curso',
  posicionado: 'En posición',
  carga_en_curso: 'Carga en curso',
  cargado: 'Carga simulada completa',
  retraccion_en_curso: 'Retracción en curso',
  retraido: 'Retraído',
  cerrado: 'Taladro cerrado',
  fallo: 'Revisión requerida',
  resultado_desconocido: 'Resultado desconocido',
};

function setFeedback(message, tone = 'info') {
  const box = $('#feedback');
  box.classList.toggle('is-rejected', tone === 'rejected');
  box.classList.toggle('is-success', tone === 'success');
  $('#feedback-text').textContent = message;
  const icon = box.querySelector('.feedback-icon');
  icon.textContent = tone === 'rejected' ? '!' : tone === 'success' ? '✓' : 'i';
}

function runCommand(command) {
  const trimmed = String(command || '').trim();
  if (!trimmed || isSending) return;
  isSending = true;
  $('#send-button').disabled = true;
  $('#suggestion-button').disabled = true;
  fetch('/api/command', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ command: trimmed }),
  }).then(async (response) => {
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'No fue posible enviar la instrucción.');
    setFeedback(data.last_message.text, data.last_message.tone);
    commandInput.value = '';
    await refresh();
  }).catch((error) => {
    setFeedback(error.message || 'No se pudo conectar con la consola.', 'rejected');
  }).finally(() => {
    isSending = false;
    $('#send-button').disabled = false;
    $('#suggestion-button').disabled = false;
  });
}

function renderJourney(progress, state) {
  const list = $('#journey-steps');
  const items = [...list.children];
  const active = Number.isInteger(progress.current_step) ? progress.current_step : -1;
  const completed = progress.completed_steps || 0;
  items.forEach((item, index) => {
    item.classList.toggle('is-current', index === active && state !== 'cerrado');
    item.classList.toggle('is-complete', index < completed || state === 'cerrado');
  });
  $('#progress-label').textContent = `${state === 'cerrado' ? 8 : completed} de 8 etapas`;
}

function renderScene(holes, operation) {
  const layer = $('#scene-holes');
  layer.replaceChildren();
  const start = holes.length === 1 ? 730 : 320;
  const end = 730;
  const points = holes.map((hole, index) => ({
    hole,
    x: holes.length === 1 ? start : start + (end - start) * index / (holes.length - 1),
  }));
  const selectedId = operation.hole_id ? String(operation.hole_id) : '';
  const activePoint = points.find(({ hole }) => String(hole.id) === selectedId);
  const state = operation.state;
  const unitAtHole = ['movimiento_en_curso', 'posicionado', 'carga_en_curso', 'cargado', 'retraccion_en_curso', 'retraido', 'cerrado'].includes(state);
  const armExtended = ['movimiento_en_curso', 'posicionado', 'carga_en_curso', 'cargado', 'retraccion_en_curso'].includes(state);
  const truckX = unitAtHole && activePoint ? Math.max(18, Math.min(600, activePoint.x - 193)) : 18;
  $('.scene-truck').setAttribute('transform', `translate(${truckX} 38)`);

  const link = $('#active-link');
  if (armExtended && activePoint) {
    link.setAttribute('x1', String(truckX + 193));
    link.setAttribute('y1', '69');
    link.setAttribute('x2', String(activePoint.x));
    link.setAttribute('y2', '122');
    link.classList.add('is-visible');
  } else {
    link.classList.remove('is-visible');
  }

  const statusClass = { Activo: 'active', Completado: 'complete', Bloqueado: 'blocked', Pendiente: 'pending' };
  const shortStatus = { Activo: 'ACTIVO', Completado: 'LISTO', Bloqueado: 'BLOQUEADO', Pendiente: 'PENDIENTE' };
  points.forEach(({ hole, x }) => {
    const group = document.createElementNS(svgNamespace, 'g');
    group.setAttribute('class', `scene-hole is-${statusClass[hole.status] || 'pending'}${String(hole.id) === selectedId ? ' is-current' : ''}`);
    group.setAttribute('aria-label', `Taladro ${hole.id}: ${hole.status}`);

    const label = document.createElementNS(svgNamespace, 'text');
    label.setAttribute('class', 'scene-hole-id');
    label.setAttribute('x', String(x));
    label.setAttribute('y', '99');
    label.textContent = hole.id;

    const stem = document.createElementNS(svgNamespace, 'line');
    stem.setAttribute('class', 'scene-hole-stem');
    stem.setAttribute('x1', String(x));
    stem.setAttribute('y1', '136');
    stem.setAttribute('x2', String(x));
    stem.setAttribute('y2', '150');

    const halo = document.createElementNS(svgNamespace, 'circle');
    halo.setAttribute('class', 'scene-hole-halo');
    halo.setAttribute('cx', String(x));
    halo.setAttribute('cy', '126');
    halo.setAttribute('r', '17');

    const ring = document.createElementNS(svgNamespace, 'circle');
    ring.setAttribute('class', 'scene-hole-ring');
    ring.setAttribute('cx', String(x));
    ring.setAttribute('cy', '126');
    ring.setAttribute('r', '9');

    const dot = document.createElementNS(svgNamespace, 'circle');
    dot.setAttribute('class', 'scene-hole-dot');
    dot.setAttribute('cx', String(x));
    dot.setAttribute('cy', '126');
    dot.setAttribute('r', '3');

    const status = document.createElementNS(svgNamespace, 'text');
    status.setAttribute('class', 'scene-hole-status');
    status.setAttribute('x', String(x));
    status.setAttribute('y', '166');
    status.textContent = shortStatus[hole.status] || 'PENDIENTE';
    group.append(label, stem, halo, ring, dot, status);
    layer.append(group);
  });

  const caption = activePoint
    ? unitAtHole ? `Unidad en taladro ${activePoint.hole.id}` : `Unidad en base · taladro ${activePoint.hole.id} seleccionado`
    : 'Unidad en base';
  $('#scene-caption').textContent = caption;
}

function renderPlan(holes, completedCount, availableCount) {
  const list = $('#hole-list');
  list.replaceChildren();
  holes.forEach((hole) => {
    const tile = document.createElement('article');
    tile.className = 'hole-tile';
    if (hole.status === 'Activo') tile.classList.add('is-active');
    if (hole.blocked) tile.classList.add('is-blocked');
    const top = document.createElement('div');
    top.className = 'hole-tile-top';
    const id = document.createElement('strong');
    id.textContent = `Taladro ${hole.id}`;
    const status = document.createElement('span');
    status.className = 'hole-status';
    status.textContent = hole.status;
    top.append(id, status);
    const detail = document.createElement('p');
    detail.textContent = hole.blocked ? 'Bloqueado por el plan' : `${hole.product} · ${hole.planned_kg} kg · ${hole.delivery_method}`;
    tile.append(top, detail);
    if (hole.blocked && hole.status === 'Bloqueado') {
      const attempt = document.createElement('button');
      attempt.type = 'button';
      attempt.className = 'button button-secondary button-wide';
      attempt.textContent = 'Ver rechazo';
      attempt.setAttribute('aria-label', `Probar selección del taladro bloqueado ${hole.id}`);
      attempt.addEventListener('click', () => runCommand(`seleccionar taladro ${hole.id}`));
      tile.append(attempt);
    }
    list.append(tile);
  });
  $('#plan-progress').textContent = `${completedCount} de ${availableCount} completados`;
}

function renderHistory(events) {
  const list = $('#event-list');
  list.replaceChildren();
  const entries = [...events].reverse();
  $('#history-count').textContent = String(events.length);
  if (!entries.length) {
    const empty = document.createElement('li');
    empty.className = 'empty-event';
    empty.textContent = 'Las acciones del recorrido aparecerán aquí.';
    list.append(empty);
    return;
  }
  entries.forEach((event) => {
    const row = document.createElement('li');
    row.className = 'event-item';
    if (!event.accepted) row.classList.add('is-rejected');
    const time = document.createElement('span');
    time.className = 'event-time';
    time.textContent = event.time;
    const copy = document.createElement('div');
    copy.className = 'event-copy';
    const title = document.createElement('strong');
    title.textContent = event.title;
    const detail = document.createElement('span');
    detail.textContent = event.detail;
    copy.append(title, detail);
    row.append(time, copy);
    list.append(row);
  });
}

function render(data) {
  $('#plan-name').textContent = data.plan.name.replace(/\s+ficticia/i, '');
  $('.metric-hole').classList.toggle('is-empty', !data.operation.hole_id);
  $('#hole-id').textContent = data.operation.hole_id ? `#${data.operation.hole_id}` : '—';
  $('#hole-state').textContent = data.operation.hole_status;
  $('#product').textContent = data.operation.product || '—';
  $('#planned-kg').textContent = data.operation.planned_kg ? `${data.operation.planned_kg}` : '—';
  $('#delivery-method').textContent = data.operation.delivery_method || '—';
  $('#scenario-label').textContent = data.scenario.label;
  const zoneToggle = $('#zone-clear');
  zoneToggle.checked = data.scenario.zone_clear;
  zoneToggle.disabled = !data.scenario.zone_clear_available;
  $('#zone-label').textContent = !data.scenario.zone_clear_available
    ? 'Ocupada por escenario'
    : data.scenario.zone_clear ? 'Despejada' : 'Marca manual';

  const pill = $('#state-pill');
  pill.textContent = stateLabels[data.operation.state] || 'Estado actualizado';
  pill.classList.toggle('is-error', ['fallo', 'resultado_desconocido'].includes(data.operation.state));

  const suggestion = data.suggestion;
  currentSuggestion = suggestion.command || '';
  $('#suggestion-title').textContent = suggestion.title;
  const requiresZone = suggestion.command.startsWith('extender ') && !data.scenario.zone_clear;
  $('#suggestion-description').textContent = requiresZone
    ? `${suggestion.description} Marca la zona antes de solicitar el movimiento.`
    : suggestion.description;
  $('#suggestion-button').textContent = suggestion.button_label;
  $('#suggestion-button').disabled = !suggestion.command || isSending || requiresZone;
  $('#suggestion-button').setAttribute('aria-label', suggestion.command ? `${suggestion.button_label}: ${suggestion.command}` : suggestion.button_label);

  const confirmation = data.confirmation;
  $('#confirmation-panel').hidden = !confirmation;
  if (confirmation) {
    const action = confirmation.action.replaceAll('_', ' ');
    $('#confirmation-text').textContent = `Taladro ${confirmation.hole_id}: ¿confirmas ${action}?`;
  }

  const alertPanel = $('#alert-panel');
  alertPanel.hidden = !data.alert;
  alertPanel.textContent = data.alert ? `Revisión requerida: ${data.alert.message}` : '';

  const recovery = ['resultado_desconocido'].includes(data.operation.state);
  $('#recovery-panel').hidden = !recovery;
  renderJourney(data.progress, data.operation.state);
  renderScene(data.plan.holes, data.operation);
  renderPlan(data.plan.holes, data.plan.completed_count, data.plan.available_count);
  renderHistory(data.history);
  if (data.last_message.text) setFeedback(data.last_message.text, data.last_message.tone);
}

async function refresh() {
  try {
    const response = await fetch('/api/state', { cache: 'no-store' });
    if (!response.ok) throw new Error('No se pudo actualizar el estado.');
    render(await response.json());
  } catch (error) {
    setFeedback('Se perdió la conexión con la consola local. Comprueba que Faro siga abierto.', 'rejected');
  }
}

$('#suggestion-button').addEventListener('click', () => runCommand(currentSuggestion));
$('#send-button').addEventListener('click', () => runCommand(commandInput.value));
commandInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter') runCommand(commandInput.value);
});
$('#confirm-button').addEventListener('click', () => runCommand('confirmar'));
$('#cancel-button').addEventListener('click', () => runCommand('cancelar'));
$('#zone-clear').addEventListener('change', async (event) => {
  try {
    const response = await fetch('/api/zone-clear', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: event.currentTarget.checked }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'No se pudo actualizar el escenario.');
    setFeedback(data.last_message.text, data.last_message.tone);
    render(data);
  } catch (error) {
    setFeedback(error.message || 'No se pudo actualizar el escenario.', 'rejected');
  }
});
$('#recovery-button').addEventListener('click', async () => {
  try {
    const response = await fetch('/api/recover', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'No fue posible registrar la revisión.');
    setFeedback(data.last_message.text, data.last_message.tone);
    await refresh();
  } catch (error) {
    setFeedback(error.message || 'No se pudo registrar la revisión.', 'rejected');
  }
});

refresh();
window.setInterval(refresh, 700);
