/* ═══════════════════════════════════════════════════════════════
   Bassi Clothing — AI Marketing Dashboard JS v2.0
   Gemini Pro + Apollo Integration
   ═══════════════════════════════════════════════════════════════ */

const API = '';  // Same origin

// ─── State ───
let allLeads = [];
let generatedEmails = [];
let lastGeneratedEmail = null;
let currentPage = 'dashboard';

// ─── Init ───
document.addEventListener('DOMContentLoaded', () => {
  loadDashboard();
  setupUploadDropzone();
});

// ═══════════════════════════════════════════════════════════════
//  NAVIGATION
// ═══════════════════════════════════════════════════════════════

function showPage(page) {
  currentPage = page;

  // Hide all page sections
  document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active'));

  // Show selected
  const el = document.getElementById(`page-${page}`);
  if (el) el.classList.add('active');

  // Update nav
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const navItem = document.querySelector(`.nav-item[data-page="${page}"]`);
  if (navItem) navItem.classList.add('active');

  // Load page data
  switch (page) {
    case 'dashboard': loadDashboard(); break;
    case 'apollo-search': /* static page */ break;
    case 'upload-emails': /* static page */ break;
    case 'leads': loadLeads(); break;
    case 'bin': loadBin(); break;
    case 'bulk-email': loadBulkEmail(); break;
    case 'email-gen': loadEmailGenOptions(); break;
    case 'campaigns': loadCampaigns(); break;
    case 'replies': loadReplies(); break;
    case 'pipeline': loadPipeline(); break;
    case 'scoring': loadScoring(); break;
    case 'catalog': loadCatalog(); break;
    case 'case-studies': loadCaseStudies(); break;
    case 'calendar': loadCalendar(); break;
  }
}

// ═══════════════════════════════════════════════════════════════
//  DASHBOARD
// ═══════════════════════════════════════════════════════════════

async function loadDashboard() {
  try {
    const res = await fetch(`${API}/api/leads/stats/pipeline`);
    const stats = await res.json();

    document.getElementById('stat-total-leads').textContent = stats.total_leads || 0;
    document.getElementById('stat-with-email').textContent = stats.with_email || 0;
    document.getElementById('stat-contacted').textContent = stats.by_stage?.contacted || 0;
    document.getElementById('stat-replied').textContent = stats.by_stage?.replied || 0;
    document.getElementById('stat-meetings').textContent = stats.by_stage?.meeting_booked || 0;
    document.getElementById('stat-in-bin').textContent = stats.in_bin || 0;

    // Update badges
    const badge = document.getElementById('leads-count-badge');
    if (badge) badge.textContent = stats.total_leads || 0;
    const binBadge = document.getElementById('bin-count-badge');
    if (binBadge) {
      const binCount = stats.in_bin || 0;
      binBadge.textContent = binCount;
      binBadge.style.display = binCount > 0 ? '' : 'none';
    }

    // Country breakdown
    const countryDiv = document.getElementById('country-breakdown');
    if (stats.by_country) {
      const countryFlags = {
        'United Kingdom': '🇬🇧', 'France': '🇫🇷', 'Germany': '🇩🇪',
        'Netherlands': '🇳🇱', 'Sweden': '🇸🇪', 'Denmark': '🇩🇰',
        'Italy': '🇮🇹', 'Spain': '🇪🇸', 'Belgium': '🇧🇪', 'Ireland': '🇮🇪',
      };
      const total = stats.total_leads || 1;
      countryDiv.innerHTML = Object.entries(stats.by_country)
        .filter(([_, count]) => count > 0)
        .map(([country, count]) => {
          const pct = Math.round(count / total * 100);
          const flag = countryFlags[country] || '🌍';
          return `
            <div style="margin-bottom:12px;">
              <div class="flex-between mb-1">
                <span style="font-size:0.85rem;">${flag} ${country}</span>
                <span style="font-size:0.8rem;color:var(--text-muted);">${count} (${pct}%)</span>
              </div>
              <div class="score-bar">
                <div class="score-bar-fill" style="width:${pct}%;background:var(--gradient-primary);"></div>
              </div>
            </div>`;
        }).join('');
    }

    // Industry breakdown
    const industryDiv = document.getElementById('industry-breakdown');
    if (stats.by_industry) {
      const total = stats.total_leads || 1;
      industryDiv.innerHTML = Object.entries(stats.by_industry)
        .filter(([_, count]) => count > 0)
        .slice(0, 8)
        .map(([industry, count]) => {
          const pct = Math.round(count / total * 100);
          return `
            <div style="margin-bottom:12px;">
              <div class="flex-between mb-1">
                <span style="font-size:0.85rem;">🏭 ${industry || 'Unknown'}</span>
                <span style="font-size:0.8rem;color:var(--text-muted);">${count} (${pct}%)</span>
              </div>
              <div class="score-bar">
                <div class="score-bar-fill" style="width:${pct}%;background:var(--gradient-blue);"></div>
              </div>
            </div>`;
        }).join('');
    }

  } catch (e) {
    console.error('Dashboard load error:', e);
  }
}

// ═══════════════════════════════════════════════════════════════
//  APOLLO SEARCH
// ═══════════════════════════════════════════════════════════════

async function triggerApolloSearch() {
  const btn = document.getElementById('btn-apollo-search');
  btn.disabled = true;
  btn.innerHTML = '<span class="loading-spinner"></span> Searching Apollo...';

  showToast('🔍 Searching Apollo with your ICP filters...', 'info');

  try {
    const res = await fetch(`${API}/api/apollo/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ page: 1, per_page: 100 }),
    });
    const data = await res.json();

    if (data.error) {
      showToast(`❌ ${data.error}`, 'error');
      btn.disabled = false;
      btn.innerHTML = '🔍 Search Apollo';
      return;
    }

    const leads = data.leads || [];
    const resultsDiv = document.getElementById('apollo-results');
    resultsDiv.style.display = 'block';

    // Stats
    document.getElementById('apollo-stats').innerHTML = `
      <div class="stat-card">
        <div class="stat-icon">🏢</div>
        <div class="stat-value">${leads.length}</div>
        <div class="stat-label">Companies Found</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🌍</div>
        <div class="stat-value">${data.total || 0}</div>
        <div class="stat-label">Total Matches</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📧</div>
        <div class="stat-value">0</div>
        <div class="stat-label">Emails (scrape from Apollo)</div>
      </div>
    `;

    document.getElementById('apollo-results-count').textContent = `${leads.length} leads`;

    // Table
    const tbody = document.getElementById('apollo-table-body');
    tbody.innerHTML = leads.map(l => `
      <tr>
        <td>
          <div style="font-weight:600;color:var(--text-heading);">${escHtml(l.company_name)}</div>
          ${l.website ? `<div style="font-size:0.72rem;color:var(--text-muted);">${escHtml(l.website)}</div>` : ''}
        </td>
        <td>${escHtml(l.person || '-')}</td>
        <td>${escHtml(l.primary_designation || '-')}</td>
        <td>${getFlag(l.country)} ${escHtml(l.country || 'N/A')}</td>
        <td>${escHtml(l.industry || '-')}</td>
        <td>${l.employees || '-'}</td>
      </tr>
    `).join('');

    // Show download button
    document.getElementById('btn-apollo-download').style.display = 'inline-flex';

    showToast(`✅ Found ${leads.length} leads! Excel ready for download.`, 'success');

  } catch (e) {
    showToast('❌ Apollo search failed: ' + e.message, 'error');
  }

  btn.disabled = false;
  btn.innerHTML = '🔍 Search Apollo';
}

function downloadApolloExcel() {
  window.open(`${API}/api/apollo/download`, '_blank');
  showToast('📥 Downloading Excel...', 'info');
}

// ═══════════════════════════════════════════════════════════════
//  UPLOAD EMAILS
// ═══════════════════════════════════════════════════════════════

let selectedFile = null;

function setupUploadDropzone() {
  const dropzone = document.getElementById('upload-dropzone');
  if (!dropzone) return;

  dropzone.addEventListener('click', () => {
    document.getElementById('email-file-input').click();
  });

  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });

  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('dragover');
  });

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length) {
      selectedFile = files[0];
      showSelectedFile(selectedFile);
    }
  });
}

function handleFileSelect(event) {
  const files = event.target.files;
  if (files.length) {
    selectedFile = files[0];
    showSelectedFile(selectedFile);
  }
}

function showSelectedFile(file) {
  document.getElementById('upload-file-info').style.display = 'block';
  document.getElementById('upload-file-name').textContent = `📄 Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
  document.getElementById('btn-upload').style.display = 'inline-flex';

  const dropzone = document.getElementById('upload-dropzone');
  dropzone.innerHTML = `
    <div class="upload-icon">✅</div>
    <h3>${escHtml(file.name)}</h3>
    <p>${(file.size / 1024).toFixed(1)} KB — Click "Upload & Merge" below</p>
  `;
}

async function uploadEmails() {
  if (!selectedFile) {
    showToast('⚠️ Select a file first', 'error');
    return;
  }

  const btn = document.getElementById('btn-upload');
  btn.disabled = true;
  btn.innerHTML = '<span class="loading-spinner"></span> Uploading...';

  const formData = new FormData();
  formData.append('file', selectedFile);

  try {
    const res = await fetch(`${API}/api/leads/upload-emails`, {
      method: 'POST',
      body: formData,
    });
    const data = await res.json();

    if (data.error) {
      showToast(`❌ ${data.error}`, 'error');
    } else {
      showToast(`✅ ${data.message}`, 'success');

      const resultsDiv = document.getElementById('upload-results');
      resultsDiv.style.display = 'block';
      document.getElementById('upload-results-content').innerHTML = `
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon">🔄</div>
            <div class="stat-value">${data.updated}</div>
            <div class="stat-label">Existing Leads Updated</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">➕</div>
            <div class="stat-value">${data.new}</div>
            <div class="stat-label">New Leads Added</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">👥</div>
            <div class="stat-value">${data.total_leads}</div>
            <div class="stat-label">Total Leads</div>
          </div>
        </div>
        <p style="color:var(--accent-emerald);margin-top:12px;">✅ Emails merged successfully! Go to <a href="#" onclick="showPage('bulk-email')" style="color:var(--accent-blue);text-decoration:underline;">Bulk Email</a> to generate & send.</p>
      `;

      // Refresh dashboard
      loadDashboard();
    }
  } catch (e) {
    showToast('❌ Upload failed: ' + e.message, 'error');
  }

  btn.disabled = false;
  btn.innerHTML = '📤 Upload & Merge Emails';
}

// ═══════════════════════════════════════════════════════════════
//  BULK EMAIL (Generate + Send All)
// ═══════════════════════════════════════════════════════════════

async function loadBulkEmail() {
  // Load previously generated emails
  try {
    const res = await fetch(`${API}/api/emails/generated`);
    const data = await res.json();
    generatedEmails = data.emails || [];

    if (generatedEmails.length > 0) {
      renderBulkEmails(generatedEmails);
      document.getElementById('btn-send-all').style.display = 'inline-flex';
    }
  } catch (e) {
    console.error('Load bulk email error:', e);
  }
}

async function generateAllEmails() {
  const emailType = document.getElementById('bulk-email-type').value;
  const generationMethod = document.getElementById('bulk-generation-method').value;
  const btn = document.getElementById('btn-generate-all');

  btn.disabled = true;
  btn.innerHTML = '<span class="loading-spinner"></span> Generating with Gemini Pro...';

  // Show progress
  const progress = document.getElementById('bulk-progress');
  progress.style.display = 'block';
  document.getElementById('bulk-progress-text').textContent = 'Generating personalized emails with Gemini Pro...';
  document.getElementById('bulk-progress-bar').style.width = '30%';

  try {
    const res = await fetch(`${API}/api/emails/generate-all`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email_type: emailType, generation_method: generationMethod }),
    });

    document.getElementById('bulk-progress-bar').style.width = '90%';

    const data = await res.json();

    if (data.error) {
      showToast(`❌ ${data.error}`, 'error');
      progress.style.display = 'none';
      btn.disabled = false;
      btn.innerHTML = '✨ Generate All Emails (Gemini Pro)';
      return;
    }

    generatedEmails = data.emails || [];
    document.getElementById('bulk-progress-bar').style.width = '100%';

    setTimeout(() => {
      progress.style.display = 'none';
      renderBulkEmails(generatedEmails);
      document.getElementById('btn-send-all').style.display = 'inline-flex';
      showToast(`✅ ${data.message || `Generated ${generatedEmails.length} emails!`}`, 'success');
    }, 500);

  } catch (e) {
    showToast('❌ Generation failed: ' + e.message, 'error');
    progress.style.display = 'none';
  }

  btn.disabled = false;
  btn.innerHTML = '✨ Generate All Emails (Gemini Pro)';
}

function renderBulkEmails(emails) {
  const container = document.getElementById('bulk-email-list');

  if (!emails.length) {
    container.innerHTML = `<div class="empty-state">
      <div class="empty-icon">✉️</div>
      <h3>No emails generated yet</h3>
      <p>Click "Generate All Emails" to create personalized emails for all leads with email addresses</p>
    </div>`;
    return;
  }

  container.innerHTML = `
    <div class="card">
      <div class="card-header">
        <div class="card-title">📧 Generated Emails (${emails.length})</div>
        <span class="badge badge-replied">${emails.filter(e => e.ai_generated).length} AI-generated</span>
      </div>
      <div class="bulk-email-grid">
        ${emails.map((email, i) => {
    const quality = email.quality_score || {};
    const scoreColor = (quality.overall || 0) >= 80 ? 'var(--accent-emerald)' :
      (quality.overall || 0) >= 60 ? 'var(--accent-amber)' : 'var(--accent-rose)';
    return `
            <div class="bulk-email-card" style="cursor:pointer; position:relative; padding-bottom: 30px;" onclick="openBulkEditModal(${i})">
              <div style="position:absolute; bottom:12px; right:15px; font-size:0.75rem; color:var(--text-muted);">
                ✏️ Click to Edit
              </div>
              <div class="bulk-email-header">
                <div>
                  <div class="bulk-email-company">${escHtml(email.company_name || 'Unknown')}</div>
                  <div class="bulk-email-to">${escHtml(email.to_email || email.contact_name || 'No email')}</div>
                </div>
                <span class="badge" style="background:${scoreColor}20;color:${scoreColor};">${quality.overall || '-'}</span>
              </div>
              <div class="bulk-email-subject">📧 ${escHtml(email.subject || '')}</div>
              <div class="bulk-email-body">${escHtml((email.body || '').substring(0, 150))}...</div>
              <div class="bulk-email-meta">
                ${email.ai_generated ? '🤖 Gemini Pro' : '📝 Template'} • ${email.model || 'N/A'}
              </div>
            </div>`;
  }).join('')}
      </div>
    </div>`;
}

function openBulkEditModal(index) {
  const email = generatedEmails[index];
  if (!email) return;
  document.getElementById('bulk-edit-index').value = index;
  document.getElementById('bulk-edit-subject').value = email.subject || '';
  document.getElementById('bulk-edit-body').value = email.body || '';
  document.getElementById('bulk-edit-modal').style.display = 'flex';
}

function closeBulkEditModal() {
  document.getElementById('bulk-edit-modal').style.display = 'none';
}

function saveBulkEmailEdit() {
  const index = document.getElementById('bulk-edit-index').value;
  const newSubject = document.getElementById('bulk-edit-subject').value;
  const newBody = document.getElementById('bulk-edit-body').value;
  if (index !== "" && generatedEmails[index]) {
    generatedEmails[index].subject = newSubject;
    generatedEmails[index].body = newBody;
    renderBulkEmails(generatedEmails);
    closeBulkEditModal();
    showToast('💾 Email edit saved locally!', 'success');
  }
}

function confirmSendAllEmails() {
  const modal = document.getElementById('modal-content');
  modal.innerHTML = `
    <div class="modal-header">
      <h3>📨 Confirm Send All Emails</h3>
      <button class="modal-close" onclick="closeModal()">&times;</button>
    </div>
    <div style="color:var(--text-secondary);margin-bottom:16px;">
      <p>You're about to send <strong>${generatedEmails.length} personalized emails</strong> from <strong>vaibhav@bassiclothing.in</strong>.</p>
      <div class="mt-2" style="padding:12px;background:rgba(245,158,11,0.1);border-radius:8px;">
        <p style="color:var(--accent-amber);">⚠️ <strong>Note:</strong> Emails will be sent with rate limiting (${generatedEmails.length > 30 ? 'max 30/day' : 'all at once'}). DRY_RUN mode will log but not actually send.</p>
      </div>
    </div>
    <div class="btn-group">
      <button class="btn btn-success" onclick="sendAllEmails()">✅ Yes, Send All</button>
      <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
    </div>
  `;
  document.getElementById('modal-overlay').classList.add('active');
}

async function sendAllEmails() {
  closeModal();

  const btn = document.getElementById('btn-send-all');
  btn.disabled = true;
  btn.innerHTML = '<span class="loading-spinner"></span> Sending...';

  showToast('📨 Sending emails...', 'info');

  try {
    const res = await fetch(`${API}/api/emails/send-all`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ emails: generatedEmails }),
    });
    const data = await res.json();

    if (data.error) {
      showToast(`❌ ${data.error}`, 'error');
    } else {
      const resultsDiv = document.getElementById('send-results');
      resultsDiv.style.display = 'block';

      const isDryRun = data.dry_run_mode;
      document.getElementById('send-results-content').innerHTML = `
        ${isDryRun ? '<div style="padding:12px;background:rgba(245,158,11,0.1);border-radius:8px;margin-bottom:16px;"><p style="color:var(--accent-amber);font-size:0.85rem;">🔍 <strong>DRY RUN MODE</strong> — Emails were logged but not actually sent. Set DRY_RUN=false in .env to send for real.</p></div>' : ''}
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon">${isDryRun ? '🔍' : '✅'}</div>
            <div class="stat-value">${isDryRun ? (data.dry_run || 0) : (data.sent || 0)}</div>
            <div class="stat-label">${isDryRun ? 'Dry Run' : 'Sent'}</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">⏭️</div>
            <div class="stat-value">${data.skipped || 0}</div>
            <div class="stat-label">Skipped</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">❌</div>
            <div class="stat-value">${data.errors || 0}</div>
            <div class="stat-label">Errors</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">📊</div>
            <div class="stat-value">${data.total_processed || 0}</div>
            <div class="stat-label">Total Processed</div>
          </div>
        </div>
        ${(data.details || []).length > 0 ? `
        <div class="table-container mt-2">
          <table>
            <thead><tr><th>Company</th><th>Email</th><th>Status</th><th>Message</th></tr></thead>
            <tbody>
              ${(data.details || []).map(d => `
                <tr>
                  <td style="font-weight:600;">${escHtml(d.company || '')}</td>
                  <td>${escHtml(d.email || '-')}</td>
                  <td><span class="badge badge-${d.status === 'sent' || d.status === 'dry_run' ? 'replied' : d.status === 'skipped' ? 'contacted' : 'lost'}">${d.status}</span></td>
                  <td style="font-size:0.8rem;color:var(--text-muted);">${escHtml(d.message || d.reason || '')}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>` : ''}
      `;

      showToast(`✅ Processed ${data.total_processed || 0} emails!`, 'success');
    }
  } catch (e) {
    showToast('❌ Send failed: ' + e.message, 'error');
  }

  btn.disabled = false;
  btn.innerHTML = '📨 Send All Emails';
}

// ═══════════════════════════════════════════════════════════════
//  LEADS
// ═══════════════════════════════════════════════════════════════

async function loadLeads() {
  try {
    const res = await fetch(`${API}/api/leads`);
    const data = await res.json();
    allLeads = data.leads || [];
    renderLeadsTable(allLeads);
  } catch (e) {
    console.error('Load leads error:', e);
  }
}

function renderLeadsTable(leads) {
  const tbody = document.getElementById('leads-table-body');
  if (!leads.length) {
    tbody.innerHTML = `<tr><td colspan="6"><div class="empty-state">
      <div class="empty-icon">👥</div>
      <h3>No leads found</h3>
      <p>Import your leads from the Apollo CSV</p>
      <button class="btn btn-primary mt-2" onclick="importLeads()">📥 Import Leads</button>
    </div></td></tr>`;
    return;
  }

  tbody.innerHTML = leads.map(lead => {
    const contact = lead.contacts?.[0];
    return `
      <tr>
        <td>
          <div style="font-weight:600;color:var(--text-heading);">${escHtml(lead.company_name)}</div>
          ${contact?.name ? `<div style="font-size:0.75rem;color:var(--text-muted);">${escHtml(contact.name)} — ${escHtml(contact.title || '')}</div>` : ''}
        </td>
        <td>${getFlag(lead.country)} ${escHtml(lead.country || 'N/A')}</td>
        <td>${escHtml(lead.industry || 'N/A')}</td>
        <td>${lead.employees || '-'}</td>
        <td><span class="badge badge-${lead.stage}">${lead.stage?.replace('_', ' ') || 'new'}</span></td>
        <td>
          <div class="btn-group">
            <button class="btn btn-sm btn-secondary" onclick="viewLeadDetail('${lead.id}')" title="View">👁️</button>
            <button class="btn btn-sm btn-primary" onclick="generateEmailForLead('${lead.id}')" title="Generate Email">✨</button>
            <button class="btn btn-sm btn-danger" onclick="confirmDeleteLead('${lead.id}', '${escHtml(lead.company_name).replace(/'/g, "\\'")}')" title="Move to Bin">🗑️</button>
          </div>
        </td>
      </tr>`;
  }).join('');
}

async function filterLeads() {
  const country = document.getElementById('filter-country').value;
  const stage = document.getElementById('filter-stage').value;
  const query = document.getElementById('filter-query').value;

  let url = `${API}/api/leads?`;
  if (country) url += `country=${encodeURIComponent(country)}&`;
  if (stage) url += `stage=${encodeURIComponent(stage)}&`;
  if (query) url += `query=${encodeURIComponent(query)}&`;

  try {
    const res = await fetch(url);
    const data = await res.json();
    renderLeadsTable(data.leads || []);
  } catch (e) {
    console.error('Filter error:', e);
  }
}

async function importLeads() {
  showToast('📥 Importing leads from CSV...', 'info');
  try {
    const res = await fetch(`${API}/api/leads/import`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    const data = await res.json();
    if (data.error) {
      showToast(`❌ ${data.error}`, 'error');
    } else {
      showToast(`✅ Imported ${data.total_imported} leads! Total: ${data.total_in_database}`, 'success');
      loadDashboard();
      if (currentPage === 'leads') loadLeads();
    }
  } catch (e) {
    showToast('❌ Import failed: ' + e.message, 'error');
  }
}

function viewLeadDetail(leadId) {
  const lead = allLeads.find(l => l.id === leadId);
  if (!lead) return;

  const contact = lead.contacts?.[0] || {};
  const modal = document.getElementById('modal-content');
  modal.innerHTML = `
    <div class="modal-header">
      <h3>${escHtml(lead.company_name)}</h3>
      <button class="modal-close" onclick="closeModal()">&times;</button>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
      <div>
        <div class="form-label">Country</div>
        <p>${getFlag(lead.country)} ${escHtml(lead.country)}</p>
      </div>
      <div>
        <div class="form-label">Industry</div>
        <p>${escHtml(lead.industry || 'N/A')}</p>
      </div>
      <div>
        <div class="form-label">Employees</div>
        <p>${lead.employees || 'N/A'}</p>
      </div>
      <div>
        <div class="form-label">Revenue</div>
        <p>${lead.revenue || 'N/A'}</p>
      </div>
      <div>
        <div class="form-label">Website</div>
        <p><a href="${escHtml(lead.website)}" target="_blank" style="color:var(--accent-blue);">${escHtml(lead.website)}</a></p>
      </div>
      <div>
        <div class="form-label">Stage</div>
        <p><span class="badge badge-${lead.stage}">${lead.stage?.replace('_', ' ')}</span></p>
      </div>
    </div>
    ${contact.name ? `
    <div class="mt-2">
      <div class="form-label">Primary Contact</div>
      <p>${escHtml(contact.name)} — ${escHtml(contact.title || 'N/A')}</p>
      ${contact.email ? `<p style="font-size:0.85rem;color:var(--text-muted);">📧 ${escHtml(contact.email)}</p>` : ''}
      ${contact.phone ? `<p style="font-size:0.85rem;color:var(--text-muted);">📞 ${escHtml(contact.phone)}</p>` : ''}
    </div>` : ''}
    ${lead.about ? `
    <div class="mt-2">
      <div class="form-label">About</div>
      <p style="font-size:0.85rem;color:var(--text-secondary);line-height:1.7;">${escHtml(lead.about)}</p>
    </div>` : ''}
    <div class="mt-2">
      <div class="form-label">Update Stage</div>
      <select class="form-select" onchange="updateLeadStage('${lead.id}', this.value)">
        ${['new', 'contacted', 'replied', 'meeting_booked', 'negotiation', 'won', 'lost'].map(s =>
    `<option value="${s}" ${s === lead.stage ? 'selected' : ''}>${s.replace('_', ' ')}</option>`
  ).join('')}
      </select>
    </div>
    <div class="mt-2 btn-group">
      <button class="btn btn-primary" onclick="generateEmailForLead('${lead.id}')">✨ Generate Email</button>
      <button class="btn btn-danger" onclick="confirmDeleteLead('${lead.id}', '${escHtml(lead.company_name).replace(/'/g, "\\'")}'); closeModal();">🗑️ Move to Bin</button>
    </div>
  `;
  document.getElementById('modal-overlay').classList.add('active');
}

async function updateLeadStage(leadId, stage) {
  try {
    await fetch(`${API}/api/leads/${leadId}/stage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stage }),
    });
    showToast(`✅ Stage updated to "${stage.replace('_', ' ')}"`, 'success');
    loadLeads();
  } catch (e) {
    showToast('❌ Update failed', 'error');
  }
}

// ═══════════════════════════════════════════════════════════════
//  SINGLE EMAIL GENERATOR
// ═══════════════════════════════════════════════════════════════

async function loadEmailGenOptions() {
  try {
    const res = await fetch(`${API}/api/leads`);
    const data = await res.json();
    window.emailGenLeads = data.leads || [];
    const select = document.getElementById('email-lead-select');
    select.innerHTML = '<option value="">Choose a company...</option>' +
      (window.emailGenLeads).map(l => {
        let emailDisplay = '';
        if (l.contacts && l.contacts.length > 0 && l.contacts[0].email) {
          emailDisplay = ` - ${escHtml(l.contacts[0].email)}`;
        }
        return `<option value="${l.id}">${escHtml(l.company_name)} (${escHtml(l.country)})${emailDisplay}</option>`;
      }).join('');
  } catch (e) {
    console.error('Load options error:', e);
  }
}

function onEmailLeadSelectChange() {
  const leadId = document.getElementById('email-lead-select').value;
  const addressInput = document.getElementById('email-lead-address');
  addressInput.value = '';

  if (!leadId || !window.emailGenLeads) return;
  const lead = window.emailGenLeads.find(l => l.id === leadId);
  if (lead && lead.contacts && lead.contacts.length > 0 && lead.contacts[0].email) {
    addressInput.value = lead.contacts[0].email;
  }
}

function generateEmailForLead(leadId) {
  showPage('email-gen');
  setTimeout(() => {
    const select = document.getElementById('email-lead-select');
    if (select) select.value = leadId;
    generateEmail();
  }, 300);
}

async function generateEmail() {
  const leadId = document.getElementById('email-lead-select').value;
  const emailType = document.getElementById('email-type-select').value;

  if (!leadId) {
    showToast('⚠️ Please select a lead', 'error');
    return;
  }

  const btn = document.getElementById('btn-generate');
  btn.disabled = true;
  btn.innerHTML = '<span class="loading-spinner"></span> Generating...';

  const generationMethod = document.getElementById('generation-method-select').value;

  try {
    const res = await fetch(`${API}/api/emails/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lead_id: leadId, email_type: emailType, generation_method: generationMethod }),
    });
    const email = await res.json();

    const resultDiv = document.getElementById('email-result');
    const qualityBadge = document.getElementById('email-quality-badge');

    if (email.error && !email.subject) {
      resultDiv.innerHTML = `<div class="empty-state"><div class="empty-icon">❌</div><h3>Generation Error</h3><p>${escHtml(email.error)}</p></div>`;
      btn.disabled = false;
      btn.innerHTML = '✨ Generate Email';
      return;
    }

    const quality = email.quality_score || {};
    const gradeColor = quality.overall >= 80 ? 'var(--accent-emerald)' :
      quality.overall >= 60 ? 'var(--accent-amber)' : 'var(--accent-rose)';

    qualityBadge.innerHTML = `<span class="badge" style="background:${gradeColor}20;color:${gradeColor};">Score: ${quality.overall || '-'}/100</span>`;

    resultDiv.innerHTML = `
      <div class="email-preview">
        <label class="form-label" style="font-size: 0.8rem; margin-bottom: 4px;">Subject</label>
        <input type="text" id="edit-email-subject" class="form-input mb-2" value="${escHtml(email.subject)}" style="margin-bottom: 12px; font-weight: 500;" />
        <label class="form-label" style="font-size: 0.8rem; margin-bottom: 4px;">Body</label>
        <textarea id="edit-email-body" class="form-textarea" rows="12">${escHtml(email.body)}</textarea>
      </div>
      <div class="mt-2" style="font-size:0.8rem;color:var(--text-muted);">
        ${email.ai_generated ? '🤖 Gemini Pro' : '📝 Template Based'} •
        ${email.model || 'N/A'}
      </div>
      <div class="mt-2">
        <h4 style="font-size:0.85rem;color:var(--text-secondary);margin-bottom:8px;">Quality Breakdown</h4>
        ${renderScoreBreakdown(quality)}
      </div>
      <div class="mt-2 btn-group">
        <button class="btn btn-success" id="btn-send-single" onclick="sendSingleEmail()">
          📨 Send This Email
        </button>
      </div>
    `;

    // Store email data for sending
    const selectedLead = allLeads.find(l => l.id === leadId);
    const contact = selectedLead?.contacts?.find(c => c.email) || selectedLead?.contacts?.[0];
    lastGeneratedEmail = {
      lead_id: leadId,
      to_email: document.getElementById('email-lead-address').value.trim(),
      to_name: contact?.name || '',
      company_name: selectedLead?.company_name || email.company_name || '',
      subject: email.subject,
      body: email.body,
      email_type: emailType,
    };

    showToast('✅ Email generated!', 'success');

  } catch (e) {
    showToast('❌ Generation failed: ' + e.message, 'error');
  }

  btn.disabled = false;
  btn.innerHTML = '✨ Generate Email';
}

async function sendSingleEmail() {
  if (!lastGeneratedEmail) {
    showToast('⚠️ No email to send. Generate one first.', 'error');
    return;
  }

  const overrideEmail = document.getElementById('email-lead-address').value.trim();
  if (overrideEmail && lastGeneratedEmail) {
    lastGeneratedEmail.to_email = overrideEmail;
  }

  if (!lastGeneratedEmail.to_email) {
    showToast('❌ Please provide a valid receiver email.', 'error');
    return;
  }

  if (document.getElementById('edit-email-subject')) {
    lastGeneratedEmail.subject = document.getElementById('edit-email-subject').value;
    lastGeneratedEmail.body = document.getElementById('edit-email-body').value;
  }

  const btn = document.getElementById('btn-send-single');
  btn.disabled = true;
  btn.innerHTML = '<span class="loading-spinner"></span> Sending...';

  try {
    const res = await fetch(`${API}/api/emails/send-single`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(lastGeneratedEmail),
    });
    const result = await res.json();

    if (result.error) {
      showToast(`❌ ${result.error}`, 'error');
    } else if (result.status === 'sent') {
      showToast(`✅ Email sent to ${lastGeneratedEmail.to_email}!`, 'success');
      btn.innerHTML = '✅ Sent!';
      btn.style.opacity = '0.7';
      return; // keep button disabled
    } else if (result.status === 'dry_run') {
      showToast(`🔍 DRY RUN — Email logged but not sent. Set DRY_RUN=false in .env to send for real.`, 'info');
      btn.innerHTML = '🔍 Dry Run Logged';
      btn.style.opacity = '0.7';
      return;
    } else if (result.status === 'skipped') {
      showToast(`⚠️ Skipped: ${result.reason}`, 'error');
    } else {
      showToast(`❌ ${result.reason || 'Send failed'}`, 'error');
    }
  } catch (e) {
    showToast('❌ Send failed: ' + e.message, 'error');
  }

  btn.disabled = false;
  btn.innerHTML = '📨 Send This Email';
}

function renderScoreBreakdown(scores) {
  const dims = ['personalization', 'length', 'cta_clarity', 'subject_line'];
  return dims.map(dim => {
    const score = scores[dim] || 0;
    const color = score >= 80 ? 'var(--accent-emerald)' : score >= 60 ? 'var(--accent-amber)' : 'var(--accent-rose)';
    return `
      <div class="score-meter" style="margin-bottom:6px;">
        <span style="font-size:0.75rem;width:110px;color:var(--text-muted);">${dim.replace('_', ' ')}</span>
        <div class="score-bar">
          <div class="score-bar-fill" style="width:${score}%;background:${color};"></div>
        </div>
        <span class="score-value" style="color:${color};">${score}</span>
      </div>`;
  }).join('');
}

// ═══════════════════════════════════════════════════════════════
//  CAMPAIGNS
// ═══════════════════════════════════════════════════════════════

async function loadCampaigns() {
  try {
    // Auto-sync stats first
    await syncCampaignStats(true);

    const res = await fetch(`${API}/api/campaigns`);
    const data = await res.json();
    const campaigns = data.campaigns || [];
    const container = document.getElementById('campaigns-list');

    if (!campaigns.length) {
      container.innerHTML = `<div class="empty-state">
        <div class="empty-icon">📧</div>
        <h3>No campaigns yet</h3>
        <p>Create your first campaign to start outreach</p>
      </div>`;
      return;
    }

    container.innerHTML = `
      <div class="table-container">
        <table>
          <thead><tr><th>Campaign</th><th>Type</th><th>Status</th><th>Sent</th><th>Opens</th><th>Replies</th><th>Bounced</th><th>Created</th></tr></thead>
          <tbody>
            ${campaigns.map(c => `
              <tr>
                <td style="font-weight:600;color:var(--text-heading);">${escHtml(c.name)}</td>
                <td>${escHtml(c.email_type?.replace('_', ' '))}</td>
                <td><span class="badge badge-${c.status === 'running' ? 'replied' : c.status === 'completed' ? 'won' : 'new'}">${c.status}</span></td>
                <td>${c.stats?.emails_sent || 0}</td>
                <td>${c.stats?.emails_opened || 0}</td>
                <td>${c.stats?.replies || 0}</td>
                <td>${c.stats?.bounces || 0}</td>
                <td style="color:var(--text-muted);">${new Date(c.created_at).toLocaleDateString()}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>`;
  } catch (e) {
    console.error('Campaigns error:', e);
  }
}

async function syncCampaignStats(silent = false) {
  try {
    const res = await fetch(`${API}/api/campaigns/sync`, { method: 'POST' });
    const data = await res.json();
    
    // Update global analytics cards
    const el = (id) => document.getElementById(id);
    if (el('camp-stat-sent')) el('camp-stat-sent').textContent = data.total_sent || 0;
    if (el('camp-stat-opened')) el('camp-stat-opened').textContent = data.total_opened || 0;
    if (el('camp-stat-replies')) el('camp-stat-replies').textContent = data.total_replied || 0;
    if (el('camp-stat-bounced')) el('camp-stat-bounced').textContent = data.total_bounced || 0;
    if (el('camp-stat-open-rate')) el('camp-stat-open-rate').textContent = data.open_rate || '0%';
    if (el('camp-stat-reply-rate')) el('camp-stat-reply-rate').textContent = data.reply_rate || '0%';

    if (!silent) showToast('🔄 Stats synced!', 'success');
  } catch(e) {
    if (!silent) showToast('❌ Sync failed', 'error');
  }
}

function showCreateCampaignModal() {
  const modal = document.getElementById('modal-content');
  modal.innerHTML = `
    <div class="modal-header">
      <h3>Create New Campaign</h3>
      <button class="modal-close" onclick="closeModal()">&times;</button>
    </div>
    <div class="form-group">
      <label class="form-label">Campaign Name</label>
      <input class="form-input" id="new-campaign-name" placeholder="e.g., UK Retailers Q2 Outreach"/>
    </div>
    <div class="form-group">
      <label class="form-label">Email Type</label>
      <select class="form-select" id="new-campaign-type">
        <option value="cold_outreach">Cold Outreach</option>
        <option value="follow_up_case_study">Follow-up: Case Study</option>
        <option value="follow_up_samples">Follow-up: Samples</option>
        <option value="breakup">Breakup</option>
      </select>
    </div>
    <div class="form-group">
      <label class="form-label">Description</label>
      <textarea class="form-textarea" id="new-campaign-desc" rows="3" placeholder="Campaign description..."></textarea>
    </div>
    <button class="btn btn-primary" onclick="createCampaign()">✅ Create Campaign</button>
  `;
  document.getElementById('modal-overlay').classList.add('active');
}

async function createCampaign() {
  const name = document.getElementById('new-campaign-name').value;
  if (!name) { showToast('⚠️ Enter a campaign name', 'error'); return; }

  try {
    await fetch(`${API}/api/campaigns`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name,
        email_type: document.getElementById('new-campaign-type').value,
        description: document.getElementById('new-campaign-desc').value,
      }),
    });
    closeModal();
    showToast('✅ Campaign created!', 'success');
    loadCampaigns();
  } catch (e) {
    showToast('❌ Failed to create campaign', 'error');
  }
}

// ═══════════════════════════════════════════════════════════════
//  REPLIES INBOX
// ═══════════════════════════════════════════════════════════════

async function loadReplies() {
  try {
    const res = await fetch(`${API}/api/replies`);
    const data = await res.json();
    const replies = data.replies || [];
    const stats = data.stats || {};

    // Update stats cards
    const el = (id) => document.getElementById(id);
    if (el('reply-stat-total')) el('reply-stat-total').textContent = stats.total_replies || 0;
    if (el('reply-stat-unread')) el('reply-stat-unread').textContent = stats.unread || 0;
    if (el('reply-stat-positive')) el('reply-stat-positive').textContent = stats.sentiments?.positive || 0;
    if (el('reply-stat-negative')) el('reply-stat-negative').textContent = stats.sentiments?.negative || 0;

    // Update sidebar badge
    const badge = el('replies-unread-badge');
    if (badge) {
      badge.textContent = stats.unread || 0;
      badge.style.display = (stats.unread || 0) > 0 ? '' : 'none';
    }

    const container = document.getElementById('replies-list');
    if (!replies.length) {
      container.innerHTML = `<div class="empty-state">
        <div class="empty-icon">📭</div>
        <h3>No replies yet</h3>
        <p>Click "Scan Inbox" to check for new replies from your leads</p>
      </div>`;
      return;
    }

    container.innerHTML = `<div style="padding:16px; display:flex; flex-direction:column; gap:12px;">
      ${replies.map(r => {
        const sentimentColor = r.sentiment === 'positive' ? 'var(--accent-emerald)' :
                               r.sentiment === 'negative' ? 'var(--accent-rose)' : 'var(--accent-amber)';
        const sentimentEmoji = r.sentiment === 'positive' ? '😊' :
                               r.sentiment === 'negative' ? '😞' : '😐';
        const unreadStyle = !r.read ? 'border-left: 3px solid var(--accent-violet);' : '';
        const date = new Date(r.received_at).toLocaleString();
        return `
          <div class="card" style="margin:0; padding:16px; cursor:pointer; ${unreadStyle}" onclick="toggleReplyBody('${r.id}')">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
              <div>
                <strong style="color:var(--text-heading);">${escHtml(r.company_name)}</strong>
                <span style="color:var(--text-muted); font-size:0.85rem;"> — ${escHtml(r.from_name || r.from_email)}</span>
              </div>
              <div style="display:flex; align-items:center; gap:8px;">
                <span class="badge" style="background:${sentimentColor}20;color:${sentimentColor};">${sentimentEmoji} ${r.sentiment}</span>
                ${!r.read ? '<span class="badge" style="background:var(--accent-violet)20;color:var(--accent-violet);">NEW</span>' : ''}
                <span style="font-size:0.75rem; color:var(--text-muted);">${date}</span>
              </div>
            </div>
            <div style="font-weight:500; color:var(--text-secondary); margin-bottom:4px;">${escHtml(r.subject)}</div>
            <div id="reply-body-${r.id}" style="display:none; margin-top:12px; padding:12px; background:var(--bg-elevated); border-radius:8px; font-size:0.9rem; color:var(--text-secondary); white-space:pre-wrap;">${escHtml(r.body_preview)}</div>
          </div>
        `;
      }).join('')}
    </div>`;

  } catch (e) {
    console.error('Replies error:', e);
  }
}

function toggleReplyBody(replyId) {
  const bodyEl = document.getElementById('reply-body-' + replyId);
  if (bodyEl) {
    const isHidden = bodyEl.style.display === 'none';
    bodyEl.style.display = isHidden ? 'block' : 'none';
    if (isHidden) {
      // Let's find the card and remove the NEW badge and unread border so it updates visually
      const card = bodyEl.closest('.card');
      let wasUnread = false;
      if (card) {
        const newBadge = Array.from(card.querySelectorAll('.badge')).find(b => b.textContent === 'NEW');
        if (newBadge) {
          newBadge.remove();
          wasUnread = true;
        }
        card.style.borderLeft = '';
      }
      
      // Mark as read in backend
      fetch(`${API}/api/replies/${replyId}/read`, { method: 'POST' }).then(() => {
        // If it was unread, let's just quietly update the stats without re-rendering the list
        if (wasUnread) {
          fetch(`${API}/api/replies/stats`).then(res => res.json()).then(stats => {
            const el = (id) => document.getElementById(id);
            if (el('reply-stat-unread')) el('reply-stat-unread').textContent = stats.unread || 0;
            const badge = el('replies-unread-badge');
            if (badge) {
              badge.textContent = stats.unread || 0;
              badge.style.display = (stats.unread || 0) > 0 ? '' : 'none';
            }
          });
        }
      });
    }
  }
}

async function scanInbox() {
  const btn = document.getElementById('btn-scan-inbox');
  btn.disabled = true;
  btn.innerHTML = '<span class="loading-spinner"></span> Scanning...';

  try {
    const res = await fetch(`${API}/api/replies/scan`, { method: 'POST' });
    const data = await res.json();

    if (data.error) {
      showToast('❌ ' + data.error, 'error');
    } else {
      showToast(`📬 Scan complete! ${data.new_replies || 0} new replies found.`, 'success');
      loadReplies();
    }
  } catch(e) {
    showToast('❌ Scan failed: ' + e.message, 'error');
  }

  btn.disabled = false;
  btn.innerHTML = '🔄 Scan Inbox';
}

// ═══════════════════════════════════════════════════════════════
//  PIPELINE (KANBAN)
// ═══════════════════════════════════════════════════════════════

async function loadPipeline() {
  try {
    const res = await fetch(`${API}/api/leads`);
    const data = await res.json();
    const leads = data.leads || [];

    const stages = {
      new: { label: 'New', color: '#6366f1' },
      contacted: { label: 'Contacted', color: '#8b5cf6' },
      replied: { label: 'Replied', color: '#3b82f6' },
      meeting_booked: { label: 'Meeting Booked', color: '#06b6d4' },
      negotiation: { label: 'Negotiation', color: '#f59e0b' },
      won: { label: 'Won ✅', color: '#10b981' },
      lost: { label: 'Lost ❌', color: '#ef4444' },
    };

    const board = document.getElementById('kanban-board');
    board.innerHTML = Object.entries(stages).map(([key, info]) => {
      const stageLeads = leads.filter(l => l.stage === key);
      return `
        <div class="kanban-column">
          <div class="kanban-column-header" style="border-bottom:2px solid ${info.color};">
            <span class="kanban-column-title" style="color:${info.color};">${info.label}</span>
            <span class="kanban-column-count">${stageLeads.length}</span>
          </div>
          <div class="kanban-column-body">
            ${stageLeads.length ? stageLeads.map(l => `
              <div class="kanban-card" onclick="viewLeadDetail('${l.id}')">
                <div class="company-name">${escHtml(l.company_name)}</div>
                <div class="company-meta">${getFlag(l.country)} ${escHtml(l.country)} • ${escHtml(l.industry || '')}</div>
              </div>
            `).join('') : '<p style="color:var(--text-muted);font-size:0.8rem;text-align:center;padding:20px;">No leads</p>'}
          </div>
        </div>`;
    }).join('');
  } catch (e) {
    console.error('Pipeline error:', e);
  }
}

// ═══════════════════════════════════════════════════════════════
//  SCORING
// ═══════════════════════════════════════════════════════════════

async function loadScoring() {
  try {
    const res = await fetch(`${API}/api/scoring`);
    const data = await res.json();

    // Stats
    const statsDiv = document.getElementById('scoring-stats');
    const gc = data.grade_counts || {};
    statsDiv.innerHTML = `
      <div class="stat-card"><div class="stat-icon">🏆</div><div class="stat-value">${gc.A || 0}</div><div class="stat-label">Grade A (Best Fit)</div></div>
      <div class="stat-card"><div class="stat-icon">👍</div><div class="stat-value">${gc.B || 0}</div><div class="stat-label">Grade B (Good Fit)</div></div>
      <div class="stat-card"><div class="stat-icon">🤔</div><div class="stat-value">${gc.C || 0}</div><div class="stat-label">Grade C (Moderate)</div></div>
      <div class="stat-card"><div class="stat-icon">👎</div><div class="stat-value">${gc.D || 0}</div><div class="stat-label">Grade D (Low Fit)</div></div>
      <div class="stat-card"><div class="stat-icon">📊</div><div class="stat-value">${data.average_score || 0}</div><div class="stat-label">Average Score</div></div>
    `;

    // Top leads table
    const tbody = document.getElementById('scoring-table-body');
    const topLeads = data.top_10 || [];
    tbody.innerHTML = topLeads.map(lead => {
      const scoreColor = lead.overall >= 80 ? 'var(--accent-emerald)' :
        lead.overall >= 60 ? 'var(--accent-amber)' : 'var(--accent-rose)';
      return `
        <tr>
          <td style="font-weight:600;color:var(--text-heading);">${escHtml(lead.company_name)}</td>
          <td>${getFlag(lead.country)} ${escHtml(lead.country)}</td>
          <td>${escHtml(lead.industry || 'N/A')}</td>
          <td>
            <div class="score-meter">
              <div class="score-bar" style="width:80px;">
                <div class="score-bar-fill" style="width:${lead.overall}%;background:${scoreColor};"></div>
              </div>
              <span class="score-value" style="color:${scoreColor};">${lead.overall}</span>
            </div>
          </td>
          <td><span class="badge badge-grade-${lead.grade}">${lead.grade}</span></td>
          <td style="font-size:0.8rem;color:var(--text-muted);">${escHtml(lead.recommendation || '')}</td>
          <td style="font-size:0.8rem;color:var(--text-muted);">${escHtml(lead.reason || '')}</td>
        </tr>`;
    }).join('');

    showToast('✅ Scores calculated!', 'success');
  } catch (e) {
    console.error('Scoring error:', e);
    showToast('❌ Scoring failed', 'error');
  }
}

// ═══════════════════════════════════════════════════════════════
//  CONTENT OPS
// ═══════════════════════════════════════════════════════════════

async function loadCatalog() {
  try {
    const res = await fetch(`${API}/api/content/catalog`);
    const data = await res.json();
    document.getElementById('catalog-content').textContent = data.content || 'No catalog content';
  } catch (e) {
    console.error('Catalog error:', e);
  }
}

async function saveCatalog(format) {
  try {
    await fetch(`${API}/api/content/catalog/save`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ format }),
    });
    showToast(`✅ Catalog exported as ${format}!`, 'success');
  } catch (e) {
    showToast('❌ Export failed', 'error');
  }
}

async function loadCaseStudies() {
  try {
    const res = await fetch(`${API}/api/content/case-studies`);
    const data = await res.json();
    const studies = data.case_studies || [];
    const container = document.getElementById('case-studies-list');

    if (!studies.length) {
      container.innerHTML = '<div class="empty-state"><div class="empty-icon">📋</div><h3>No case studies</h3></div>';
      return;
    }

    container.innerHTML = studies.map(cs => `
      <div class="card">
        <div class="card-header">
          <div class="card-title">${escHtml(cs.title)}</div>
          <span class="badge badge-new">${escHtml(cs.country)}</span>
        </div>
        <p style="font-size:0.85rem;color:var(--text-secondary);margin-bottom:12px;">
          <strong>Client:</strong> ${escHtml(cs.client)} | <strong>Industry:</strong> ${escHtml(cs.industry)}
        </p>
        <p style="font-size:0.85rem;color:var(--text-secondary);margin-bottom:12px;">
          <strong>Challenge:</strong> ${escHtml(cs.challenge?.substring(0, 200))}...
        </p>
        <div class="flex gap-2" style="flex-wrap:wrap;">
          ${Object.entries(cs.results || {}).map(([k, v]) =>
      `<span class="badge badge-replied">${k.replace('_', ' ')}: ${escHtml(v)}</span>`
    ).join('')}
        </div>
      </div>
    `).join('');
  } catch (e) {
    console.error('Case studies error:', e);
  }
}

async function loadCalendar() {
  try {
    const month = document.getElementById('calendar-month')?.value || '';
    const url = month ? `${API}/api/content/calendar?month=${month}` : `${API}/api/content/calendar`;
    const res = await fetch(url);
    const data = await res.json();
    const container = document.getElementById('calendar-content');

    const items = data.content_items || [];
    if (!items.length) {
      container.innerHTML = '<p class="text-center" style="color:var(--text-muted);">No content planned</p>';
      return;
    }

    container.innerHTML = `
      <h3 style="margin-bottom:16px;color:var(--text-heading);">📅 ${escHtml(data.month || '')} ${data.year || ''}</h3>
      <div class="table-container">
        <table>
          <thead><tr><th>Week</th><th>Type</th><th>Topic</th><th>Goal</th><th>Status</th></tr></thead>
          <tbody>
            ${items.map(item => `
              <tr>
                <td>Week ${item.week}</td>
                <td><span class="badge badge-new">${escHtml(item.content_type)}</span></td>
                <td style="color:var(--text-heading);max-width:300px;">${escHtml(item.topic)}</td>
                <td style="color:var(--text-muted);">${escHtml(item.goal)}</td>
                <td><span class="badge badge-contacted">${item.status}</span></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>`;
  } catch (e) {
    console.error('Calendar error:', e);
  }
}

// ═══════════════════════════════════════════════════════════════
//  UTILITIES
// ═══════════════════════════════════════════════════════════════

function escHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function getFlag(country) {
  const flags = {
    'United Kingdom': '🇬🇧', 'France': '🇫🇷', 'Germany': '🇩🇪',
    'Netherlands': '🇳🇱', 'Sweden': '🇸🇪', 'Denmark': '🇩🇰',
    'Italy': '🇮🇹', 'Spain': '🇪🇸', 'Belgium': '🇧🇪', 'Ireland': '🇮🇪',
    'Portugal': '🇵🇹', 'Norway': '🇳🇴', 'Finland': '🇫🇮', 'Austria': '🇦🇹',
    'Hungary': '🇭🇺', 'Poland': '🇵🇱', 'Australia': '🇦🇺',
  };
  return flags[country] || '🌍';
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

function closeModal(event) {
  if (event && event.target !== document.getElementById('modal-overlay')) return;
  document.getElementById('modal-overlay').classList.remove('active');
}

// ═══════════════════════════════════════════════════════════════
//  BIN / TRASH
// ═══════════════════════════════════════════════════════════════

function confirmDeleteLead(leadId, companyName) {
  const modal = document.getElementById('modal-content');
  modal.innerHTML = `
    <div class="modal-header">
      <h3>🗑️ Move to Bin</h3>
      <button class="modal-close" onclick="closeModal()">&times;</button>
    </div>
    <div style="color:var(--text-secondary);margin-bottom:16px;">
      <p>Are you sure you want to move <strong>${companyName}</strong> to the bin?</p>
      <div class="mt-2" style="padding:12px;background:rgba(244,63,94,0.08);border-radius:8px;">
        <p style="color:var(--accent-amber);font-size:0.85rem;">⚠️ This will remove the lead from your active list. You can restore it from the Bin later.</p>
      </div>
    </div>
    <div class="btn-group">
      <button class="btn btn-danger" onclick="deleteLead('${leadId}')">🗑️ Yes, Move to Bin</button>
      <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
    </div>
  `;
  document.getElementById('modal-overlay').classList.add('active');
}

async function deleteLead(leadId) {
  closeModal();
  try {
    const res = await fetch(`${API}/api/leads/${leadId}/delete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    const data = await res.json();
    if (data.success) {
      showToast('🗑️ Lead moved to bin', 'success');
      loadLeads();
      loadDashboard();
    } else {
      showToast(`❌ ${data.error || 'Delete failed'}`, 'error');
    }
  } catch (e) {
    showToast('❌ Delete failed: ' + e.message, 'error');
  }
}

async function loadBin() {
  try {
    const res = await fetch(`${API}/api/bin`);
    const data = await res.json();
    const binLeads = data.leads || [];
    renderBinTable(binLeads);

    const emptyBtn = document.getElementById('btn-empty-bin');
    if (emptyBtn) emptyBtn.style.display = binLeads.length > 0 ? 'inline-flex' : 'none';
  } catch (e) {
    console.error('Load bin error:', e);
  }
}

function renderBinTable(leads) {
  const tbody = document.getElementById('bin-table-body');
  if (!leads.length) {
    tbody.innerHTML = `<tr><td colspan="5"><div class="empty-state">
      <div class="empty-icon">🗑️</div>
      <h3>Bin is empty</h3>
      <p>Deleted leads will appear here</p>
    </div></td></tr>`;
    return;
  }

  tbody.innerHTML = leads.map(lead => {
    const deletedAt = lead.deleted_at ? new Date(lead.deleted_at).toLocaleDateString('en-GB', {
      day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
    }) : 'Unknown';
    return `
      <tr>
        <td>
          <div style="font-weight:600;color:var(--text-heading);opacity:0.7;">${escHtml(lead.company_name)}</div>
          <div style="font-size:0.72rem;color:var(--text-muted);">${lead.contacts?.[0]?.email || 'No email'}</div>
        </td>
        <td>${getFlag(lead.country)} ${escHtml(lead.country || 'N/A')}</td>
        <td>${escHtml(lead.industry || 'N/A')}</td>
        <td style="font-size:0.8rem;color:var(--text-muted);">${deletedAt}</td>
        <td>
          <div class="btn-group">
            <button class="btn btn-sm btn-success" onclick="restoreLead('${lead.id}')" title="Restore">♻️ Restore</button>
            <button class="btn btn-sm btn-danger" onclick="confirmPermanentDelete('${lead.id}', '${escHtml(lead.company_name).replace(/'/g, "\\'")}')" title="Delete Forever">❌ Delete</button>
          </div>
        </td>
      </tr>`;
  }).join('');
}

async function restoreLead(leadId) {
  try {
    const res = await fetch(`${API}/api/bin/${leadId}/restore`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    const data = await res.json();
    if (data.success) {
      showToast('♻️ Lead restored!', 'success');
      loadBin();
      loadDashboard();
    } else {
      showToast(`❌ ${data.error || 'Restore failed'}`, 'error');
    }
  } catch (e) {
    showToast('❌ Restore failed: ' + e.message, 'error');
  }
}

function confirmPermanentDelete(leadId, companyName) {
  const modal = document.getElementById('modal-content');
  modal.innerHTML = `
    <div class="modal-header">
      <h3>❌ Permanently Delete</h3>
      <button class="modal-close" onclick="closeModal()">&times;</button>
    </div>
    <div style="color:var(--text-secondary);margin-bottom:16px;">
      <p>Are you sure you want to <strong>permanently delete</strong> <strong>${companyName}</strong>?</p>
      <div class="mt-2" style="padding:12px;background:rgba(244,63,94,0.12);border-radius:8px;">
        <p style="color:var(--accent-rose);font-size:0.85rem;">🚨 <strong>This cannot be undone.</strong> The lead and all associated data will be permanently erased.</p>
      </div>
    </div>
    <div class="btn-group">
      <button class="btn btn-danger" onclick="permanentDeleteLead('${leadId}')">🗑️ Yes, Delete Forever</button>
      <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
    </div>
  `;
  document.getElementById('modal-overlay').classList.add('active');
}

async function permanentDeleteLead(leadId) {
  closeModal();
  try {
    const res = await fetch(`${API}/api/bin/${leadId}`, {
      method: 'DELETE',
    });
    const data = await res.json();
    if (data.success) {
      showToast('💥 Lead permanently deleted', 'success');
      loadBin();
      loadDashboard();
    } else {
      showToast(`❌ ${data.error || 'Delete failed'}`, 'error');
    }
  } catch (e) {
    showToast('❌ Delete failed: ' + e.message, 'error');
  }
}

function confirmEmptyBin() {
  const modal = document.getElementById('modal-content');
  modal.innerHTML = `
    <div class="modal-header">
      <h3>🗑️ Empty Entire Bin</h3>
      <button class="modal-close" onclick="closeModal()">&times;</button>
    </div>
    <div style="color:var(--text-secondary);margin-bottom:16px;">
      <p>Are you sure you want to <strong>permanently delete ALL leads</strong> in the bin?</p>
      <div class="mt-2" style="padding:12px;background:rgba(244,63,94,0.15);border-radius:8px;">
        <p style="color:var(--accent-rose);font-size:0.85rem;">🚨 <strong>This cannot be undone.</strong> All leads in the bin will be permanently erased.</p>
      </div>
    </div>
    <div class="btn-group">
      <button class="btn btn-danger" onclick="emptyBin()">🗑️ Yes, Empty Bin</button>
      <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
    </div>
  `;
  document.getElementById('modal-overlay').classList.add('active');
}

async function emptyBin() {
  closeModal();
  try {
    const res = await fetch(`${API}/api/bin`, {
      method: 'DELETE',
    });
    const data = await res.json();
    if (data.success) {
      showToast(`🗑️ Bin emptied — ${data.deleted} leads permanently deleted`, 'success');
      loadBin();
      loadDashboard();
    } else {
      showToast('❌ Failed to empty bin', 'error');
    }
  } catch (e) {
    showToast('❌ Failed to empty bin: ' + e.message, 'error');
  }
}

// Close modal on escape
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeModal();
});
