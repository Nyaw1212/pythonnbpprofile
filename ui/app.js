const $ = (id) => document.getElementById(id);
const state = { timer: null, camp: '', office: '', rank: '', page: 1, pageSize: 25, totalPages: 1 };

function fullName(person) {
  const middle = person.middle_name ? ` ${person.middle_name}` : '';
  const suffix = person.suffix ? ` ${person.suffix}` : '';
  return `${person.first_name || ''}${middle} ${person.last_name || ''}${suffix}`.replace(/\s+/g, ' ').trim();
}

function cell(value, className = '') {
  const td = document.createElement('td'); td.textContent = value || '—'; if (className) td.className = className; return td;
}

function renderChipGroup(containerId, values, field) {
  const container = $(containerId); container.innerHTML = '';
  [''].concat(values).forEach((value) => {
    const button = document.createElement('button');
    button.type = 'button'; button.className = 'value-chip'; button.textContent = value || 'All';
    button.classList.toggle('active', state[field] === value);
    button.addEventListener('click', () => {
      state[field] = value;
      state.page = 1;
      container.querySelectorAll('.value-chip').forEach((chip) => chip.classList.remove('active'));
      button.classList.add('active');
      runSearch();
    });
    container.appendChild(button);
  });
}

async function loadFilters() {
  const filters = await pywebview.api.get_filters();
  renderChipGroup('campChips', filters.camp, 'camp');
  renderChipGroup('officeChips', filters.office, 'office');
  renderChipGroup('rankChips', filters.rank, 'rank');
}

async function loadStats() {
  const stats = await pywebview.api.get_stats();
  $('totalPersonnel').textContent = Number(stats.total || 0).toLocaleString();
}

function renderPageNumbers(current, totalPages) {
  const container = $('pageNumbers');
  container.innerHTML = '';

  const pages = new Set([1, totalPages, current - 1, current, current + 1]);
  const valid = [...pages].filter((page) => page >= 1 && page <= totalPages).sort((a, b) => a - b);
  let previous = null;

  valid.forEach((page) => {
    if (previous !== null && page - previous > 1) {
      const dots = document.createElement('span');
      dots.className = 'page-dots';
      dots.textContent = '…';
      container.appendChild(dots);
    }

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'page-number';
    button.textContent = page;
    button.classList.toggle('active', page === current);
    button.addEventListener('click', () => {
      if (page === state.page) return;
      state.page = page;
      runSearch();
    });
    container.appendChild(button);
    previous = page;
  });
}

function updatePagination(data) {
  state.page = data.page;
  state.totalPages = data.total_pages;

  $('pageSummary').textContent = data.total
    ? `Showing ${data.start}–${data.end} of ${Number(data.total).toLocaleString()} results`
    : 'Showing 0 results';

  $('resultCount').textContent = `${Number(data.total || 0).toLocaleString()} match${data.total === 1 ? '' : 'es'}`;
  $('prevPage').disabled = data.page <= 1;
  $('nextPage').disabled = data.page >= data.total_pages || data.total === 0;
  renderPageNumbers(data.page, data.total_pages);
}

async function runSearch() {
  const data = await pywebview.api.search_personnel_paged(
    $('searchInput').value,
    state.camp,
    state.office,
    state.rank,
    state.page,
    state.pageSize
  );

  updatePagination(data);
  const tbody = $('results');
  const emptyState = $('emptyState');
  tbody.innerHTML = '';

  if (!data.rows.length) {
    emptyState.classList.remove('hidden');
    return;
  }
  emptyState.classList.add('hidden');

  data.rows.forEach((person) => {
    const row = document.createElement('tr');
    row.className = 'person-row';
    row.tabIndex = 0;
    row.setAttribute('role', 'button');
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
      if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); open(); }
    });
    tbody.appendChild(row);
  });
}

async function openProfile(badgeNumber) {
  const person = await pywebview.api.get_profile(String(badgeNumber)); if (!person) return;
  $('profileInitials').textContent = `${(person.first_name || '?')[0]}${(person.last_name || '?')[0]}`.toUpperCase();
  $('profileBadge').textContent = `BADGE ${person.badge_number}`;
  $('profileName').textContent = fullName(person);
  $('profileRank').textContent = person.rank || 'No rank recorded';
  const details = [['Camp', person.camp], ['Office', person.office], ['Gender', person.gender], ['Classification', person.classification], ['Type', person.personnel_type], ['Record ID', person.record_id]];
  $('profileDetails').innerHTML = details.filter(([, value]) => value).map(([label, value]) => `<div class="detail"><small>${label}</small><strong>${value}</strong></div>`).join('');
  $('profileModal').classList.remove('hidden'); $('profileModal').setAttribute('aria-hidden', 'false');
}

function closeProfile() { $('profileModal').classList.add('hidden'); $('profileModal').setAttribute('aria-hidden', 'true'); }
function scheduleSearch() { clearTimeout(state.timer); state.page = 1; state.timer = setTimeout(runSearch, 140); }

window.addEventListener('pywebviewready', async () => {
  await Promise.all([loadFilters(), loadStats()]);
  await runSearch();

  $('searchInput').addEventListener('input', scheduleSearch);
  $('pageSize').addEventListener('change', () => {
    state.pageSize = Number($('pageSize').value);
    state.page = 1;
    runSearch();
  });
  $('prevPage').addEventListener('click', () => {
    if (state.page > 1) { state.page -= 1; runSearch(); }
  });
  $('nextPage').addEventListener('click', () => {
    if (state.page < state.totalPages) { state.page += 1; runSearch(); }
  });
  $('clearButton').addEventListener('click', async () => {
    state.camp = ''; state.office = ''; state.rank = ''; state.page = 1;
    await loadFilters();
    runSearch();
  });
  document.querySelectorAll('[data-close-modal]').forEach((node) => node.addEventListener('click', closeProfile));
  document.addEventListener('keydown', (event) => { if (event.key === 'Escape') closeProfile(); });
});
