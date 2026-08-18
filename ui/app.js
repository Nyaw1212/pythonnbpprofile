const $ = (id) => document.getElementById(id);
const state = { timer: null };

function fullName(person) {
  const middle = person.middle_name ? ` ${person.middle_name}` : '';
  const suffix = person.suffix ? ` ${person.suffix}` : '';
  return `${person.first_name || ''}${middle} ${person.last_name || ''}${suffix}`.replace(/\s+/g, ' ').trim();
}

function option(value) {
  const node = document.createElement('option');
  node.value = value;
  node.textContent = value;
  return node;
}

function cell(value, className = '') {
  const td = document.createElement('td');
  td.textContent = value || '—';
  if (className) td.className = className;
  return td;
}

async function loadFilters() {
  const filters = await pywebview.api.get_filters();
  filters.camp.forEach((value) => $('campFilter').appendChild(option(value)));
  filters.office.forEach((value) => $('officeFilter').appendChild(option(value)));
  filters.rank.forEach((value) => $('rankFilter').appendChild(option(value)));
}

async function loadStats() {
  const stats = await pywebview.api.get_stats();
  $('totalPersonnel').textContent = Number(stats.total || 0).toLocaleString();
}

async function runSearch() {
  const results = await pywebview.api.search_personnel(
    $('searchInput').value,
    $('campFilter').value,
    $('officeFilter').value,
    $('rankFilter').value,
    100
  );

  $('resultCount').textContent = results.length === 100
    ? 'Showing first 100 matches'
    : `${results.length} match${results.length === 1 ? '' : 'es'}`;

  const tbody = $('results');
  const emptyState = $('emptyState');
  tbody.innerHTML = '';

  if (!results.length) {
    emptyState.classList.remove('hidden');
    return;
  }

  emptyState.classList.add('hidden');

  results.forEach((person) => {
    const row = document.createElement('tr');
    row.className = 'person-row';
    row.tabIndex = 0;
    row.setAttribute('role', 'button');
    row.setAttribute('aria-label', `Open profile for ${fullName(person)}`);

    row.appendChild(cell(String(person.badge_number || ''), 'badge-cell'));
    row.appendChild(cell(person.rank, 'rank-cell'));
    row.appendChild(cell(fullName(person), 'name-cell'));
    row.appendChild(cell(person.camp));
    row.appendChild(cell(person.office));
    row.appendChild(cell(person.classification));
    row.appendChild(cell(person.personnel_type));

    const open = () => openProfile(person.badge_number);
    row.addEventListener('click', open);
    row.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        open();
      }
    });

    tbody.appendChild(row);
  });
}

async function openProfile(badgeNumber) {
  const person = await pywebview.api.get_profile(String(badgeNumber));
  if (!person) return;

  const initials = `${(person.first_name || '?')[0]}${(person.last_name || '?')[0]}`.toUpperCase();
  $('profileInitials').textContent = initials;
  $('profileBadge').textContent = `BADGE ${person.badge_number}`;
  $('profileName').textContent = fullName(person);
  $('profileRank').textContent = person.rank || 'No rank recorded';

  const details = [
    ['Camp', person.camp],
    ['Office', person.office],
    ['Gender', person.gender],
    ['Classification', person.classification],
    ['Type', person.personnel_type],
    ['Record ID', person.record_id],
  ];

  $('profileDetails').innerHTML = details
    .filter(([, value]) => value)
    .map(([label, value]) => `<div class="detail"><small>${label}</small><strong>${value}</strong></div>`)
    .join('');

  $('profileModal').classList.remove('hidden');
  $('profileModal').setAttribute('aria-hidden', 'false');
}

function closeProfile() {
  $('profileModal').classList.add('hidden');
  $('profileModal').setAttribute('aria-hidden', 'true');
}

function scheduleSearch() {
  clearTimeout(state.timer);
  state.timer = setTimeout(runSearch, 140);
}

window.addEventListener('pywebviewready', async () => {
  await Promise.all([loadFilters(), loadStats()]);
  await runSearch();

  $('searchInput').addEventListener('input', scheduleSearch);
  ['campFilter', 'officeFilter', 'rankFilter'].forEach((id) => $(id).addEventListener('change', runSearch));
  $('clearButton').addEventListener('click', () => {
    $('searchInput').value = '';
    $('campFilter').value = '';
    $('officeFilter').value = '';
    $('rankFilter').value = '';
    runSearch();
  });
  document.querySelectorAll('[data-close-modal]').forEach((node) => node.addEventListener('click', closeProfile));
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeProfile();
  });
});
