'use strict';

// ── Layout constants ──────────────────────────────────────────────────────────
const LW     = 228;   // label column width (px)
const HC     = 42;    // hours sub-column (rightmost part of LW)
const ROW_H  = 27;    // task row height
const PH_H   = 21;    // phase-header row height
const GAP    = 10;    // gap between phase groups
const PAD_T  = 50;    // top padding (date axis)
const PAD_B  = 10;
const PAD_R  = 18;
const BAR_H  = 13;    // bar height

// ── Project range ─────────────────────────────────────────────────────────────
const T0      = new Date('2026-06-08');
const T_END   = new Date('2026-08-22');   // exclusive (day after last)
const SPAN_MS = T_END - T0;
const DAYS    = SPAN_MS / 864e5;          // 75
const WEEKS   = 11;

// ── Phase colours ─────────────────────────────────────────────────────────────
const C = { P1:'#3b82f6', P2:'#10b981', P3:'#f59e0b', P4:'#8b5cf6', P5:'#ec4899', OH:'#6b7280' };
const PHASE_ORDER = ['P1','P2','P3','P4','P5','OH'];

// ── State ─────────────────────────────────────────────────────────────────────
let plan, entries = [], actuals = {};
let showCP = true, showMS = true, showLo = true;
const collapsedPhases = new Set();

// ── Boot ──────────────────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', async () => {
  if (location.protocol === 'file:') {
    die('Fetch is blocked on <code>file://</code>. Serve locally:<br>' +
        'Run <code>python3 -m http.server 8080</code> from the project root, then open ' +
        '<code>http://localhost:8080/docs/gantt.html</code>');
    return;
  }

  try {
    const r = await fetch('project_timeline.json');
    if (!r.ok) throw new Error(r.status);
    plan = await r.json();
  } catch(e) { die(`Could not load <code>project_timeline.json</code>: ${e.message}`); return; }

  try {
    const r = await fetch('time_log.jsonl');
    if (r.ok) {
      const txt = await r.text();
      entries = txt.trim().split('\n').filter(l => l.trim())
        .map(l => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean);
    }
  } catch { /* no log yet */ }

  actuals = {};
  entries.forEach(e => { actuals[e.task_id] = (actuals[e.task_id] || 0) + e.hours; });

  const m = plan.meta;
  $('meta').textContent =
    `${m.engagement_start} – ${m.engagement_end}  ·  ${m.budget_hours} hrs budgeted  ·  v${m.version.replace('v','')}`;
  if (entries.length) $('log-count').textContent = `· ${entries.length} time entries logged`;

  buildLegend();
  $('b-cp').addEventListener('click', () => { showCP = tog('b-cp', showCP); redraw(); });
  $('b-ms').addEventListener('click', () => { showMS = tog('b-ms', showMS); redraw(); });
  $('b-lo').addEventListener('click', () => {
    showLo = tog('b-lo', showLo);
    $('load-card').style.display = showLo ? '' : 'none';
    redraw();
  });
  window.addEventListener('resize', redraw);
  $('gantt').addEventListener('click', e => {
    const pid = e.target.getAttribute('data-phase');
    if (!pid) return;
    if (collapsedPhases.has(pid)) collapsedPhases.delete(pid);
    else collapsedPhases.add(pid);
    redraw();
  });
  redraw();
});

function redraw() { if (plan) { drawGantt(); if (showLo) drawLoad(); } }

// ── Gantt ─────────────────────────────────────────────────────────────────────
function drawGantt() {
  const svg = $('gantt');
  const W  = svg.clientWidth || 1200;
  const CW = W - LW - PAD_R;

  // Date → x pixel
  const x = d => LW + ((new Date(d) - T0) / SPAN_MS) * CW;

  // Build ordered row list
  const rows = [];
  let yc = PAD_T, prevPh = null;
  PHASE_ORDER.forEach(pid => {
    const phase = plan.phases.find(p => p.id === pid);
    if (!phase) return;
    const tasks = plan.tasks.filter(t => t.phase === pid)
      .sort((a,b) => new Date(a.start) - new Date(b.start));
    if (!tasks.length) return;
    if (prevPh !== null) yc += GAP;
    prevPh = pid;
    rows.push({ type:'phase', phase, y: yc }); yc += PH_H;
    if (!collapsedPhases.has(pid)) {
      tasks.forEach(task => { rows.push({ type:'task', task, y: yc }); yc += ROW_H; });
    }
  });
  const H = yc + PAD_B;
  svg.setAttribute('height', H);

  const out = [];

  // ── Background & grid ──────────────────────────────────────────────────────
  out.push(R(0,0,W,H,{fill:'white'}));
  for (let wi = 0; wi <= WEEKS; wi++) {
    const wx = LW + (wi * 7 / DAYS) * CW;
    const isMonth = weekDate(wi).getDate() <= 7;
    out.push(L(wx, PAD_T - 14, wx, H - PAD_B, {
      stroke: isMonth ? '#e2e8f0' : '#f8fafc',
      'stroke-width': isMonth ? 1 : 0.5
    }));
  }

  // ── Left panel overlay (drawn over grid, under bars) ───────────────────────
  out.push(R(0,0,LW,H,{fill:'#f8fafc'}));
  out.push(R(LW-HC,0,HC,H,{fill:'#f1f5f9'}));
  out.push(L(LW,0,LW,H,{stroke:'#e2e8f0','stroke-width':1}));

  // ── Date axis ─────────────────────────────────────────────────────────────
  out.push(R(LW, 0, CW + PAD_R, PAD_T - 14, {fill:'white'}));
  [['Jun','2026-06-08'],['Jul','2026-07-06'],['Aug','2026-08-03']].forEach(([lbl,dt]) => {
    out.push(T(x(dt)+3, PAD_T-30, lbl, {'font-size':'12','font-weight':'700',fill:'#374151'}));
  });
  for (let wi = 0; wi < WEEKS; wi++) {
    const x0 = LW + (wi * 7 / DAYS) * CW;
    const x1 = LW + ((wi+1) * 7 / DAYS) * CW;
    const mid = (x0 + x1) / 2;
    out.push(T(mid, PAD_T-17, `W${wi+1}`, {'font-size':'9',fill:'#94a3b8','text-anchor':'middle'}));
    out.push(T(mid, PAD_T-5,  fmtShort(weekDate(wi)), {'font-size':'8',fill:'#cbd5e1','text-anchor':'middle'}));
  }
  out.push(T(LW-HC/2, PAD_T-17, 'Est.', {'font-size':'9','font-weight':'700',fill:'#64748b','text-anchor':'middle'}));

  // ── Today line ────────────────────────────────────────────────────────────
  const today = new Date();
  const tx = x(today);
  if (tx >= LW && tx <= W - PAD_R) {
    out.push(L(tx, PAD_T-14, tx, H-PAD_B, {stroke:'#ef4444','stroke-width':1.5,'stroke-dasharray':'4 3',opacity:.9}));
    out.push(T(tx+3, PAD_T-16, 'today', {'font-size':'9',fill:'#ef4444','font-weight':'600'}));
  }

  // ── Rows ──────────────────────────────────────────────────────────────────
  rows.forEach(row => {
    if (row.type === 'phase') {
      const { phase, y } = row;
      const col = C[phase.id];
      const isCollapsed = collapsedPhases.has(phase.id);
      const arrow = isCollapsed ? '▶' : '▼';
      out.push(R(0, y, W, PH_H, {fill: col+'14', 'pointer-events':'none'}));
      out.push(R(0, y, 3, PH_H, {fill: col, 'pointer-events':'none'}));
      out.push(T(9, y+PH_H-6, `${arrow} ${phase.label}`, {'font-size':'10','font-weight':'700',fill:col,'pointer-events':'none'}));
      if (!isCollapsed) {
        const px = x(phase.start), pw = x(phase.end) - px;
        out.push(R(px, y+5, pw, PH_H-9, {fill: col+'22', rx:2, 'pointer-events':'none'}));
      }
      out.push(R(0, y, W, PH_H, {fill:'transparent', class:'ph', 'data-phase':phase.id, style:'cursor:pointer'}));
    } else {
      const { task: tk, y } = row;
      const col = C[tk.phase];
      const isCP = tk.critical_path && showCP;

      out.push(R(0, y, W, ROW_H, {fill:'transparent', class:'tr', 'data-id':tk.id, style:'cursor:default'}));

      out.push(T(9, y+ROW_H-7, trunc(tk.label, 25), {
        'font-size':'11', fill: tk.status==='completed' ? '#94a3b8' : '#334155'
      }));

      const logNew  = actuals[tk.id] || 0;
      const logSeed = tk.hours_actual || 0;
      const totalLogged = logNew + logSeed;
      const hLbl = totalLogged > 0
        ? `${totalLogged.toFixed(1)}/${tk.hours_estimated}h`
        : `${tk.hours_estimated}h`;
      out.push(T(LW-HC/2, y+ROW_H-7, hLbl, {'font-size':'10','font-weight':'500',fill:'#475569','text-anchor':'middle'}));

      const bx = x(tk.start);
      const bw = Math.max(6, x(tk.end) - bx);
      const by = y + Math.floor((ROW_H - BAR_H) / 2);
      const alpha = tk.status === 'not-started' ? '55' : '';

      // Work block: hours_estimated scaled at 16h/wk budget
      const pxPerHour = CW * 7 / (DAYS * 16);
      const wbw = Math.max(6, Math.min(bw, tk.hours_estimated * pxPerHour));

      // Window bar (faint — scheduling window / deadline)
      out.push(R(bx, by, bw, BAR_H, {fill: col+'22', rx:3}));

      // Work block (solid — estimated effort)
      if (isCP) out.push(R(bx-2, by-2, wbw+4, BAR_H+4, {fill:'none',stroke:'#fbbf24','stroke-width':1.5,rx:4,opacity:.8}));
      out.push(R(bx, by, wbw, BAR_H, {
        fill: col+alpha, rx:3,
        stroke: isCP ? '#d97706' : 'none', 'stroke-width': isCP ? 1 : 0
      }));

      const prog = tk.hours_estimated > 0
        ? (logNew > 0 ? Math.min(1, totalLogged / tk.hours_estimated) : tk.progress / 100)
        : tk.progress / 100;
      if (prog > 0 && wbw > 0) {
        out.push(R(bx, by, wbw * prog, BAR_H, {fill:'rgba(0,0,0,0.35)', rx:3}));
      }

      if (tk.status === 'in-progress') {
        out.push(R(bx, by, 3, BAR_H, {fill:'white', opacity:.65, rx:2}));
      }
    }
  });

  // ── Milestones ────────────────────────────────────────────────────────────
  if (showMS) {
    plan.milestones.forEach(ms => {
      const mx = x(ms.date);
      if (mx < LW || mx > W - PAD_R) return;
      const isApproval = /approv/i.test(ms.label);
      const fc = isApproval ? '#ef4444' : (ms.critical_path ? '#0f172a' : '#64748b');
      const sz = 7, my = PAD_T - sz - 5;

      out.push(L(mx, PAD_T - 2, mx, H - PAD_B, {
        stroke: fc, 'stroke-width': .5, 'stroke-dasharray':'2 3', opacity:.3
      }));
      out.push(`<polygon points="${mx},${my} ${mx+sz},${my+sz} ${mx},${my+sz*2} ${mx-sz},${my+sz}" ` +
        `fill="${isApproval ? fc : 'white'}" stroke="${fc}" stroke-width="1.5" ` +
        `class="ms" data-id="${ms.id}" style="cursor:default"/>`);
    });
  }

  // Separator drawn last so it stays on top of phase header fills
  out.push(L(LW-HC, PAD_T-20, LW-HC, H-PAD_B, {stroke:'#cbd5e1','stroke-width':1}));

  svg.innerHTML = out.join('');
  bindTips(svg);
}

// ── Hour Load ─────────────────────────────────────────────────────────────────
function drawLoad() {
  const svg = $('load');
  const W  = svg.clientWidth || 1200;
  const CW = W - LW - PAD_R;
  const wi2x = wi => LW + (wi * 7 / DAYS) * CW;

  const H = 118, CH = 72, PT = 10, PB = 26;
  svg.setAttribute('height', H);

  const wkHrs = Array.from({length: WEEKS}, (_, wi) => {
    const ws = new Date(T0.getTime() + wi * 7 * 864e5);
    const we = new Date(T0.getTime() + (wi+1) * 7 * 864e5);
    const byPhase = {};
    PHASE_ORDER.forEach(p => byPhase[p] = 0);
    plan.tasks.forEach(tk => {
      const ts = new Date(tk.start);
      const te = new Date(new Date(tk.end).getTime() + 864e5);
      const ov = Math.max(0, Math.min(te,we) - Math.max(ts,ws));
      if (!ov) return;
      const td = Math.max(1, te - ts);
      byPhase[tk.phase] += tk.hours_estimated * (ov / td);
    });
    return byPhase;
  });

  const totals = wkHrs.map(w => PHASE_ORDER.reduce((s,p) => s + w[p], 0));
  const maxH = Math.max(22, ...totals);
  const yS = v => PT + CH - (v / maxH) * CH;

  const out = [R(0,0,W,H,{fill:'white'})];

  wkHrs.forEach((w, wi) => {
    const x0 = wi2x(wi) + 1, x1 = wi2x(wi+1) - 1;
    const bw = x1 - x0;
    let top = PT + CH;
    PHASE_ORDER.forEach(p => {
      const h = w[p];
      if (h < 0.05) return;
      const bh = (h / maxH) * CH;
      top -= bh;
      out.push(R(x0, top, bw, bh, {fill: C[p], opacity:.82}));
    });
    out.push(T((x0+x1)/2, H-8, `W${wi+1}`, {'font-size':'8',fill:'#94a3b8','text-anchor':'middle'}));
  });

  const budY = yS(16);
  out.push(L(LW, budY, W-PAD_R, budY, {stroke:'#ef4444','stroke-width':1,'stroke-dasharray':'4 3',opacity:.7}));
  out.push(T(LW+4, budY-3, '16h/wk budget', {'font-size':'8',fill:'#ef4444'}));

  [0, 8, 16, Math.ceil(maxH/8)*8].filter((v,i,a) => a.indexOf(v)===i && v <= maxH+1).forEach(v => {
    const y = yS(v);
    out.push(L(LW-3, y, LW, y, {stroke:'#e2e8f0','stroke-width':1}));
    out.push(T(LW-5, y+3, `${v}h`, {'font-size':'8',fill:'#94a3b8','text-anchor':'end'}));
  });

  out.push(R(0, 0, LW, H, {fill:'#f8fafc'}));
  out.push(L(LW, 0, LW, H, {stroke:'#e2e8f0','stroke-width':1}));
  out.push(T(9, PT+10, 'Estimated', {'font-size':'9',fill:'#94a3b8'}));

  const actWk = Array(WEEKS).fill(0);
  entries.forEach(e => {
    const wi = Math.floor((new Date(e.date) - T0) / (7 * 864e5));
    if (wi >= 0 && wi < WEEKS) actWk[wi] += e.hours;
  });
  const hasAct = actWk.some(v => v > 0);
  if (hasAct) {
    out.push(T(9, PT+22, 'Actual ●', {'font-size':'9',fill:'#0f172a'}));
    actWk.forEach((h, wi) => {
      if (!h) return;
      const cx = (wi2x(wi) + wi2x(wi+1)) / 2;
      const cy = yS(h);
      out.push(`<circle cx="${cx}" cy="${cy}" r="3.5" fill="#0f172a" stroke="white" stroke-width="1.5"/>`);
    });
  }

  out.push(R(LW, PT, CW, CH, {fill:'none',stroke:'#f1f5f9','stroke-width':1}));
  svg.innerHTML = out.join('');
}

// ── Tooltips ──────────────────────────────────────────────────────────────────
function bindTips(svg) {
  const tip = $('tip');

  svg.addEventListener('mousemove', e => {
    const el = e.target;
    const did = el.getAttribute('data-id');

    if (el.classList.contains('tr')) {
      const tk = plan.tasks.find(t => t.id === did);
      if (!tk) return hideT();
      const ph = plan.phases.find(p => p.id === tk.phase);
      const logNew = actuals[tk.id] || 0;
      const logSeed = tk.hours_actual || 0;
      const tot = logNew + logSeed;
      const deps = tk.dependencies.length ? tk.dependencies.join(', ') : '—';
      tip.innerHTML =
        `<div class="tt">${tk.id} · ${tk.label}</div>` +
        row('Phase',      ph?.label || tk.phase) +
        row('Dates',      `${tk.start} → ${tk.end}`) +
        row('Hours',      tot > 0 ? `${tot.toFixed(1)} logged / ${tk.hours_estimated} est.` : `${tk.hours_estimated} est.`) +
        row('Status',     tk.status) +
        row('Confidence', tk.confidence) +
        (tk.critical_path && showCP ? `<div><span class="tl">⚡ </span><span class="tv">Critical path</span></div>` : '') +
        row('Depends on', deps) +
        (tk.notes ? `<div class="tn">${tk.notes.slice(0,160)}${tk.notes.length>160?'…':''}</div>` : '');
      showT(tip, e.clientX, e.clientY);

    } else if (el.classList.contains('ms')) {
      const ms = plan.milestones.find(m => m.id === did);
      if (!ms) return hideT();
      const deps = ms.dependencies.length ? ms.dependencies.join(', ') : '—';
      const isAp = /approv/i.test(ms.label);
      tip.innerHTML =
        `<div class="tt">${isAp ? '⚑ ' : '◆ '}${ms.label}</div>` +
        row('Date',       ms.date) +
        row('Phase',      ms.phase) +
        (ms.critical_path ? `<div><span class="tl">⚡ </span><span class="tv">Critical path</span></div>` : '') +
        row('Depends on', deps) +
        (ms.notes ? `<div class="tn">${ms.notes.slice(0,200)}</div>` : '');
      showT(tip, e.clientX, e.clientY);

    } else { hideT(); }
  });

  svg.addEventListener('mouseleave', hideT);
}

function row(lbl, val) {
  return `<div><span class="tl">${lbl}: </span><span class="tv">${esc(String(val))}</span></div>`;
}
function showT(tip, mx, my) {
  tip.style.display = 'block';
  const tw = tip.offsetWidth, th = tip.offsetHeight;
  const W = window.innerWidth, H = window.innerHeight;
  let left = mx + 14, top = my - 10;
  if (left + tw > W - 8) left = mx - tw - 14;
  if (top + th > H - 8) top = H - th - 8;
  tip.style.left = left + 'px'; tip.style.top = top + 'px';
}
function hideT() { $('tip').style.display = 'none'; }

// ── Legend ────────────────────────────────────────────────────────────────────
function buildLegend() {
  const phases = [
    ['P1','Phase 1 · Process Design'],['P2','Phase 2 · Data Collection'],
    ['P3','Phase 3 · Workshop Design'],['P4','Phase 4 · Facilitation'],
    ['P5','Phase 5 · Post-Analysis'],['OH','Overhead'],
  ];
  $('legend').innerHTML =
    phases.map(([id,lbl]) =>
      `<div class="li"><div class="ls" style="background:${C[id]}"></div>${lbl}</div>`
    ).join('') +
    `<div class="li"><svg width="18" height="12"><rect x="0" y="1" width="18" height="10" fill="${C.P1}" rx="2" stroke="#fbbf24" stroke-width="1.5"/></svg>Critical path</div>` +
    `<div class="li"><svg width="12" height="14"><polygon points="6,0 12,7 6,14 0,7" fill="#ef4444"/></svg>Approval gate</div>` +
    `<div class="li"><svg width="12" height="14"><polygon points="6,0 12,7 6,14 0,7" fill="white" stroke="#0f172a" stroke-width="1.5"/></svg>Milestone</div>` +
    `<div class="li"><svg width="9" height="12"><circle cx="4.5" cy="6" r="3.5" fill="#0f172a" stroke="white" stroke-width="1.5"/></svg>Actual hours (time log)</div>`;
}

// ── SVG helpers ───────────────────────────────────────────────────────────────
function R(x,y,w,h,a={}) { return `<rect ${attrs({x,y,width:w,height:h,...a})}/>`; }
function L(x1,y1,x2,y2,a={}) { return `<line ${attrs({x1,y1,x2,y2,...a})}/>`; }
function T(x,y,s,a={}) { return `<text ${attrs({x,y,...a})}>${esc(String(s))}</text>`; }
function attrs(o) { return Object.entries(o).map(([k,v]) => `${k}="${v}"`).join(' '); }
function esc(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function trunc(s,n) { return s.length > n ? s.slice(0,n-1)+'…' : s; }
function weekDate(wi) { return new Date(T0.getTime() + wi * 7 * 864e5); }
function fmtShort(d) {
  return ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][d.getMonth()] + ' ' + d.getDate();
}
function $(id) { return document.getElementById(id); }
function tog(btnId, state) { const n = !state; $(btnId).classList.toggle('on', n); return n; }
function die(msg) { const e = $('err'); e.innerHTML = msg; e.style.display = 'block'; }
