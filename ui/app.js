const $ = (id) => document.getElementById(id);
const state = { timer: null, camp: '', office: '', rank: '', page: 1, pageSize: 25, totalPages: 1, currentBadge: null };

function fullName(person) {
  const middle = person.middle_name ? ` ${person.middle_name}` : '';
  const suffix = person.suffix ? ` ${person.suffix}` : '';
  return `${person.first_name || ''}${middle} ${person.last_name || ''}${suffix}`.replace(/\s+/g, ' ').trim();
}
function display(value) { return value || '—'; }
function cell(value, className = '') { const td = document.createElement('td'); td.textContent = value || '—'; if (className) td.className = className; return td; }

function renderChipGroup(containerId, values, field) {
  const container = $(containerId); container.innerHTML = '';
  [''].concat(values).forEach((value) => {
    const button = document.createElement('button'); button.type = 'button'; button.className = 'value-chip'; button.textContent = value || 'All';
    button.classList.toggle('active', state[field] === value);
    button.addEventListener('click', () => { state[field] = value; state.page = 1; container.querySelectorAll('.value-chip').forEach((chip) => chip.classList.remove('active')); button.classList.add('active'); runSearch(); });
    container.appendChild(button);
  });
}
async function loadFilters() { const filters = await pywebview.api.get_filters(); renderChipGroup('campChips', filters.camp, 'camp'); renderChipGroup('officeChips', filters.office, 'office'); renderChipGroup('rankChips', filters.rank, 'rank'); }
async function loadStats() { const stats = await pywebview.api.get_stats(); $('totalPersonnel').textContent = Number(stats.total || 0).toLocaleString(); }

function renderPageNumbers(current, totalPages) {
  const container = $('pageNumbers'); container.innerHTML = '';
  const pages = new Set([1, totalPages, current - 1, current, current + 1]); const valid = [...pages].filter((page) => page >= 1 && page <= totalPages).sort((a,b) => a-b); let previous = null;
  valid.forEach((page) => { if (previous !== null && page - previous > 1) { const dots = document.createElement('span'); dots.className = 'page-dots'; dots.textContent = '…'; container.appendChild(dots); }
    const button = document.createElement('button'); button.type = 'button'; button.className = 'page-number'; button.textContent = page; button.classList.toggle('active', page === current); button.addEventListener('click', () => { if (page !== state.page) { state.page = page; runSearch(); } }); container.appendChild(button); previous = page; });
}
function updatePagination(data) {
  state.page = data.page; state.totalPages = data.total_pages;
  $('pageSummary').textContent = data.total ? `Showing ${data.start}–${data.end} of ${Number(data.total).toLocaleString()} results` : 'Showing 0 results';
  $('resultCount').textContent = `${Number(data.total || 0).toLocaleString()} match${data.total === 1 ? '' : 'es'}`;
  $('prevPage').disabled = data.page <= 1; $('nextPage').disabled = data.page >= data.total_pages || data.total === 0; renderPageNumbers(data.page, data.total_pages);
}

async function runSearch() {
  const data = await pywebview.api.search_personnel_paged($('searchInput').value, state.camp, state.office, state.rank, state.page, state.pageSize);
  updatePagination(data); const tbody = $('results'); const emptyState = $('emptyState'); tbody.innerHTML = '';
  if (!data.rows.length) { emptyState.classList.remove('hidden'); return; } emptyState.classList.add('hidden');
  data.rows.forEach((person) => { const row = document.createElement('tr'); row.className = 'person-row'; row.tabIndex = 0; row.setAttribute('role', 'button');
    row.appendChild(cell(String(person.badge_number || ''), 'badge-cell')); row.appendChild(cell(person.rank, 'rank-cell')); row.appendChild(cell(fullName(person), 'name-cell')); row.appendChild(cell(person.camp)); row.appendChild(cell(person.office)); row.appendChild(cell(person.classification)); row.appendChild(cell(person.personnel_type));
    const open = () => openProfile(person.badge_number); row.addEventListener('click', open); row.addEventListener('keydown', (event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); open(); } }); tbody.appendChild(row); });
}

function setProfilePhoto(person) {
  const initials = `${(person.first_name || '?')[0]}${(person.last_name || '?')[0]}`.toUpperCase();
  const image = $('profilePhoto');
  const initialsNode = $('profileInitials');
  initialsNode.textContent = initials;
  initialsNode.classList.remove('hidden');
  image.classList.add('hidden');
  image.removeAttribute('src');
  image.onload = null;
  image.onerror = null;

  const fileId = String(person.drive_file_id || '').trim();
  if (!fileId) return;

  const encoded = encodeURIComponent(fileId);
  const sources = [
    `https://drive.google.com/thumbnail?id=${encoded}&sz=w1000`,
    `https://drive.google.com/uc?export=view&id=${encoded}`,
    `https://lh3.googleusercontent.com/d/${encoded}=w1000`
  ];

  let sourceIndex = 0;
  const tryNextSource = () => {
    if (sourceIndex >= sources.length) {
      image.classList.add('hidden');
      initialsNode.classList.remove('hidden');
      return;
    }
    image.src = sources[sourceIndex++];
  };

  image.onload = () => {
    if (!image.naturalWidth || !image.naturalHeight) {
      tryNextSource();
      return;
    }
    image.classList.remove('hidden');
    initialsNode.classList.add('hidden');
  };
  image.onerror = tryNextSource;
  tryNextSource();
}

async function openProfile(badgeNumber) {
  const person = await pywebview.api.get_profile(String(badgeNumber)); if (!person) return;
  state.currentBadge = String(badgeNumber);
  setProfilePhoto(person);
  $('profileName').textContent = fullName(person).toUpperCase();
  $('profileRank').textContent = display(person.rank);
  $('profileBadgeValue').textContent = display(person.badge_number);
  $('profileRecordId').textContent = display(person.record_id);
  $('profileClassification').textContent = display(person.classification);
  $('profileType').textContent = display(person.personnel_type);
  $('profileGender').textContent = display(person.gender);
  $('profileCampSide').textContent = display(person.camp);
  $('profileOffice').textContent = display(person.office);
  $('profileCamp').textContent = display(person.camp);
  $('profileRankOffice').textContent = display(person.rank);
  $('profileGeneratedDate').textContent = new Date().toLocaleString();
  $('pdfStatus').textContent = '';
  $('profileModal').classList.remove('hidden'); $('profileModal').setAttribute('aria-hidden', 'false'); document.body.classList.add('modal-open');
}

async function saveCurrentProfilePdf() {
  if (!state.currentBadge) return;
  const button = $('savePdfButton');
  const status = $('pdfStatus');
  button.disabled = true;
  button.textContent = 'Saving…';
  status.textContent = '';
  try {
    const result = await pywebview.api.save_profile_pdf(state.currentBadge);
    if (result && result.ok) {
      status.textContent = 'PDF saved';
      status.className = 'pdf-status success';
    } else if (result && result.cancelled) {
      status.textContent = 'Save cancelled';
      status.className = 'pdf-status';
    } else {
      status.textContent = (result && result.message) || 'Could not save PDF';
      status.className = 'pdf-status error';
    }
  } catch (error) {
    status.textContent = 'Could not save PDF';
    status.className = 'pdf-status error';
  } finally {
    button.disabled = false;
    button.textContent = 'Save PDF';
  }
}

function printCurrentProfile() { if (!state.currentBadge) return; window.print(); }
function closeProfile() { $('profileModal').classList.add('hidden'); $('profileModal').setAttribute('aria-hidden', 'true'); document.body.classList.remove('modal-open'); state.currentBadge = null; }
function scheduleSearch() { clearTimeout(state.timer); state.page = 1; state.timer = setTimeout(runSearch, 140); }

window.addEventListener('pywebviewready', async () => {
  await Promise.all([loadFilters(), loadStats()]); await runSearch();
  $('searchInput').addEventListener('input', scheduleSearch);
  $('pageSize').addEventListener('change', () => { state.pageSize = Number($('pageSize').value); state.page = 1; runSearch(); });
  $('prevPage').addEventListener('click', () => { if (state.page > 1) { state.page -= 1; runSearch(); } });
  $('nextPage').addEventListener('click', () => { if (state.page < state.totalPages) { state.page += 1; runSearch(); } });
  $('clearButton').addEventListener('click', async () => { state.camp = ''; state.office = ''; state.rank = ''; state.page = 1; await loadFilters(); runSearch(); });
  $('savePdfButton').addEventListener('click', saveCurrentProfilePdf);
  $('printProfileButton').addEventListener('click', printCurrentProfile);
  document.querySelectorAll('[data-close-modal]').forEach((node) => node.addEventListener('click', closeProfile));
  document.addEventListener('keydown', (event) => { if (event.key === 'Escape') closeProfile(); });
});
