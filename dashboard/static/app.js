/* ═══════════════════════════════════════════════════════════════
   Bassi Clothing — AI Marketing Dashboard JS
   ═══════════════════════════════════════════════════════════════ */

const API = '';  // Same origin

// ─── State ───
let allLeads = [];
let currentPage = 'dashboard';

// ─── Init ───
document.addEventListener('DOMContentLoaded', () => {
  loadDashboard();
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
    case 'leads': loadLeads(); break;
    case 'email-gen': loadEmailGenOptions(); break;
    case 'campaigns': loadCampaigns(); break;
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

    // Update badge
    const badge = document.getElementById('leads-count-badge');
    if (badge) badge.textContent = stats.total_leads || 0;

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
            <button class="btn btn-sm btn-secondary" onclick="viewLeadDetail('${lead.id}')">👁️</button>
            <button class="btn btn-sm btn-primary" onclick="generateEmailForLead('${lead.id}')">✨</button>
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
  showToast('📥 Importing leads from Apollo CSV...', 'info');
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
        ${['new','contacted','replied','meeting_booked','negotiation','won','lost'].map(s =>
          `<option value="${s}" ${s === lead.stage ? 'selected' : ''}>${s.replace('_', ' ')}</option>`
        ).join('')}
      </select>
    </div>
    <div class="mt-2 btn-group">
      <button class="btn btn-primary" onclick="generateEmailForLead('${lead.id}')">✨ Generate Email</button>
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
//  EMAIL GENERATOR
// ═══════════════════════════════════════════════════════════════

async function loadEmailGenOptions() {
  try {
    const res = await fetch(`${API}/api/leads`);
    const data = await res.json();
    const select = document.getElementById('email-lead-select');
    select.innerHTML = '<option value="">Choose a company...</option>' +
      (data.leads || []).map(l =>
        `<option value="${l.id}">${escHtml(l.company_name)} (${escHtml(l.country)})</option>`
      ).join('');
  } catch (e) {
    console.error('Load options error:', e);
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

  try {
    const res = await fetch(`${API}/api/emails/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lead_id: leadId, email_type: emailType }),
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
        <div class="email-subject">📧 ${escHtml(email.subject)}</div>
        <div class="email-body">${escHtml(email.body)}</div>
      </div>
      <div class="mt-2" style="font-size:0.8rem;color:var(--text-muted);">
        ${email.ai_generated ? '🤖 AI Generated' : '📝 Template Based'} •
        ${email.model || 'N/A'} •
        ${email.tokens_used ? email.tokens_used + ' tokens' : ''}
      </div>
      <div class="mt-2">
        <h4 style="font-size:0.85rem;color:var(--text-secondary);margin-bottom:8px;">Quality Breakdown</h4>
        ${renderScoreBreakdown(quality)}
      </div>
    `;
    showToast('✅ Email generated!', 'success');

  } catch (e) {
    showToast('❌ Generation failed: ' + e.message, 'error');
  }

  btn.disabled = false;
  btn.innerHTML = '✨ Generate Email';
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
          <thead><tr><th>Campaign</th><th>Type</th><th>Status</th><th>Sent</th><th>Replies</th><th>Created</th></tr></thead>
          <tbody>
            ${campaigns.map(c => `
              <tr>
                <td style="font-weight:600;color:var(--text-heading);">${escHtml(c.name)}</td>
                <td>${escHtml(c.email_type?.replace('_', ' '))}</td>
                <td><span class="badge badge-${c.status === 'running' ? 'replied' : c.status === 'completed' ? 'won' : 'new'}">${c.status}</span></td>
                <td>${c.stats?.emails_sent || 0}</td>
                <td>${c.stats?.replies || 0}</td>
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

// Close modal on escape
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeModal();
});
