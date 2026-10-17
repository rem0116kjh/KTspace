'use strict';
const $ = (id) => document.getElementById(id);
const icons = {
  orbit:'<ellipse cx="12" cy="12" rx="10" ry="5.7" transform="rotate(-35 12 12)"/><circle cx="12" cy="12" r="2.7"/><circle cx="19.5" cy="5.6" r="1.5" fill="currentColor" stroke="none"/>',
  sliders:'<path d="M4 7h4m4 0h8M4 17h9m4 0h3"/><circle cx="10" cy="7" r="2"/><circle cx="15" cy="17" r="2"/>',
  layers:'<path d="m12 3 9 5-9 5-9-5 9-5Zm-9 9 9 5 9-5M3 16l9 5 9-5"/>',
  grid:'<rect x="4" y="4" width="6" height="6" rx="1"/><rect x="14" y="4" width="6" height="6" rx="1"/><rect x="4" y="14" width="6" height="6" rx="1"/><rect x="14" y="14" width="6" height="6" rx="1"/>',
  book:'<path d="M12 6c-3-3-6-3-9-2v15c3-1 6-1 9 2 3-3 6-3 9-2V4c-3-1-6-1-9 2Zm0 0v15"/>',
  spark:'<path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5L12 3ZM20 2v4m-2-2h4"/>',
  help:'<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 4 2c-1 .6-1.5 1-1.5 2.5M12 17h.01"/>',
  compass:'<circle cx="12" cy="12" r="9"/><path d="m16 8-2.5 5.5L8 16l2.5-5.5L16 8Z"/>',
  chart:'<path d="M4 4v16h17M7 15l4-5 4 3 5-7"/>',
  compare:'<path d="M4 7h16m-4-4 4 4-4 4M20 17H4m4-4-4 4 4 4"/>',
  expand:'<path d="M9 4H4v5m11-5h5v5M4 15v5h5m11-5v5h-5"/>',
  pause:'<path d="M8 5v14M16 5v14" stroke-width="3"/>',
  play:'<path d="m8 5 11 7-11 7V5Z" fill="currentColor" stroke="none"/>',
  restart:'<path d="M4 10a8 8 0 1 1 1 7M4 4v6h6"/>',
  focus:'<path d="M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5"/><circle cx="12" cy="12" r="3"/>',
  info:'<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10h.01"/>',
  bookmark:'<path d="M6 3h12v18l-6-4-6 4V3Z"/>',
  shield:'<path d="m12 3 8 3v6c0 4-4 7-8 9-4-2-8-5-8-9V6l8-3Z"/><path d="m8 12 3 3 5-6"/>',
  download:'<path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5"/>',
  close:'<path d="m6 6 12 12M18 6 6 18"/>',
  clock:'<circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 2"/>',
  target:'<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="5" ry="8"/><path d="M3 12h18"/>',
  check:'<path d="m5 12 4 4L19 6"/>',
};
const svg = (name) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${icons[name] || icons.orbit}</svg>`;
function hydrateIcons(root = document) { root.querySelectorAll('[data-icon]').forEach(el => { el.innerHTML = svg(el.dataset.icon); }); }
hydrateIcons();

const framed = window.parent !== window;
if (framed) document.body.classList.add('embedded');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
let experiment = null, settings = { mass: .8, radius: 1, model: 'impulse', step: 1 };
let activeLesson = 'mass', activeView = 'lab', activeTab = 'orbit';
let playing = !reducedMotion.matches, speed = 1, simTime = .12, lastFrame = 0;
let notes = [], completed = [], requestTimer, abortController, toastTimer;
try { notes = JSON.parse(localStorage.getItem('orbit-notes-v1') || '[]'); completed = JSON.parse(localStorage.getItem('orbit-completed-v1') || '[]'); } catch { /* private browsers keep the current session usable */ }
if (!Array.isArray(notes)) notes = [];
if (!Array.isArray(completed)) completed = [];
const labels = { ellipse: '타원 궤도', circle: '원궤도', parabola: '포물선 궤도', hyperbola: '쌍곡선 궤도' };
const escapeHTML = value => String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const fmt = (value, digits = 2) => value == null ? '정의 안 됨' : Number(value).toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits });
function streamlitMessage(type, payload = {}) { window.parent.postMessage({ isStreamlitMessage: true, type, ...payload }, '*'); }
function setHeight() { if (framed) streamlitMessage('streamlit:setFrameHeight', { height: Math.max(760, Math.ceil(document.querySelector('.app-shell').getBoundingClientRect().height)) }); }
function toast(message) { $('toast').textContent = message; $('toast').classList.add('show'); clearTimeout(toastTimer); toastTimer = setTimeout(() => $('toast').classList.remove('show'), 3200); }
function setStatus(message, good = true) { $('engine-status-text').textContent = message; document.querySelector('.engine-status i').style.background = good ? '#61dec2' : '#f0b66c'; }

async function requestExperiment() {
  setStatus('궤도 계산 중', false);
  $('save-experiment').disabled = true;
  if (framed) { streamlitMessage('streamlit:setComponentValue', { value: { settings: { ...settings } }, dataType: 'json' }); return; }
  if (abortController) abortController.abort();
  abortController = new AbortController();
  try {
    const response = await fetch('/api/experiment', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(settings), signal: abortController.signal });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || '계산에 실패했습니다.');
    receiveExperiment(data);
  } catch (error) { if (error.name !== 'AbortError') { setStatus('계산 연결 확인 필요', false); toast(error.message); $('loading').textContent = '계산 연결을 확인해주세요. 페이지를 새로고침하면 다시 연결합니다.'; } }
}
function queueExperiment() { syncControls(); $('save-experiment').disabled = true; clearTimeout(requestTimer); requestTimer = setTimeout(requestExperiment, 180); }
function receiveExperiment(data) {
  experiment = data; settings = { ...data.settings }; simTime = Math.min(.12, data.simulation.duration_years);
  playing = !reducedMotion.matches; updatePlayButton();
  $('loading').hidden = true; $('experiment-body').hidden = false; $('save-experiment').disabled = false;
  setStatus('물리 엔진 정상 작동'); syncControls(); renderResults(); renderLessons(); renderLibrary(); renderNotebook();
  requestAnimationFrame(() => { drawAll(); setHeight(); });
}
function syncControls() {
  $('mass-slider').value = settings.mass; $('radius-slider').value = settings.radius; $('step-select').value = settings.step;
  $('mass-value').textContent = settings.mass.toFixed(2);
  const delta = Math.round((settings.mass - 1) * 100);
  $('mass-delta').textContent = delta === 0 ? '현재 태양과 동일' : `현재 대비 ${delta > 0 ? '+' : '−'}${Math.abs(delta)}%`;
  $('radius-value').innerHTML = `${settings.radius.toFixed(2)} <span>AU</span>`;
  ['mass', 'radius'].forEach(key => { const el = $(`${key}-slider`); const percent = (Number(el.value) - Number(el.min)) / (Number(el.max) - Number(el.min)) * 100; el.style.background = `linear-gradient(to right,#61dec2 ${percent}%,#2c3542 ${percent}%)`; });
  document.querySelectorAll('[data-model]').forEach(el => { const selected = el.dataset.model === settings.model; el.classList.toggle('selected', selected); el.setAttribute('aria-pressed', selected); });
  document.querySelectorAll('[data-mass]').forEach(el => el.classList.toggle('selected', Number(el.dataset.mass) === settings.mass));
}
function renderResults() {
  const e = experiment.elements, b = experiment.baseline, s = experiment.simulation;
  $('orbit-type').textContent = labels[e.state]; $('canvas-eccentricity').textContent = e.eccentricity.toFixed(3);
  $('physics-explanation').textContent = experiment.explanation;
  $('duration-label').textContent = `${Math.round(s.duration_years * 365.25)} DAYS`;
  $('solver-label').textContent = `VERLET · Δt ${settings.step}d`;
  const change = e.period_days ? (e.period_days / b.period_days - 1) * 100 : null;
  const metricData = [
    ['공전 주기', e.period_days ? fmt(e.period_days, 1) : '—', e.period_days ? '일' : '', e.period_days ? `<span class="positive">${change >= 0 ? '↗ +' : '↘ '}${fmt(change, 1)}%</span> 동일 거리 기준 대비` : '<span class="amber">열린 궤도 · 주기 없음</span>', 'clock'],
    ['궤도 이심률', fmt(e.eccentricity, 3), 'e', e.eccentricity < 1 ? '0은 원 · 1은 탈출 경계' : '<span class="amber">e ≥ 1 · 탈출 조건 충족</span>', 'orbit'],
    ['궤도 상태', labels[e.state], '', `<span class="${e.bound ? 'positive' : 'amber'}">${e.bound ? '● 중력에 묶인 상태' : '↗ 열린 탈출 궤도'}</span>`, 'target'],
    ['에너지 보존 오차', s.max_energy_error_pct < .0001 ? s.max_energy_error_pct.toExponential(1) : fmt(s.max_energy_error_pct, 4), '%', `전 ${s.steps.toLocaleString()}단계 중 최대 · Δt ${settings.step}일`, 'shield'],
  ];
  $('metrics-grid').innerHTML = metricData.map((m,i) => `<article class="metric-card"><div class="metric-top"><span>${m[0]}</span>${svg(m[4])}</div><div class="metric-value ${i === 2 ? 'metric-state' : ''}">${m[1]}<small>${m[2]}</small></div><div class="metric-detail">${m[3]}</div></article>`).join('');
  const c = experiment.comparison;
  const modelName = settings.model === 'impulse' ? '순간 질량 변화' : '원궤도 비교';
  const otherName = settings.model === 'impulse' ? '원궤도 비교' : '순간 질량 변화';
  $('comparison-table').innerHTML = `<table class="comparison-table"><thead><tr><th>관측값</th><th>${modelName}</th><th>${otherName}</th></tr></thead><tbody>${[
    ['초기 속도 (km/s)', fmt(e.velocity_kms), fmt(c.velocity_kms)],
    ['이심률', fmt(e.eccentricity, 3), fmt(c.eccentricity, 3)],
    ['공전 주기 (일)', e.period_days ? fmt(e.period_days, 1) : '정의 안 됨', c.period_days ? fmt(c.period_days, 1) : '정의 안 됨'],
    ['에너지 (km²/s²)', fmt(e.energy_km2_s2), fmt(c.energy_km2_s2)],
  ].map(row => `<tr>${row.map(v => `<td>${v}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
}

function switchView(view) {
  activeView = view;
  document.querySelectorAll('.view').forEach(el => { el.hidden = el.id !== `view-${view}`; el.classList.toggle('active', !el.hidden); });
  document.querySelectorAll('[data-view]').forEach(el => { el.classList.toggle('active', el.dataset.view === view); if (el.dataset.view === view) el.setAttribute('aria-current','page'); else el.removeAttribute('aria-current'); });
  $('breadcrumb-current').textContent = { lab: '태양계 역학', course: '탐구 커리큘럼', library: '시나리오 라이브러리', notebook: '나의 탐구 노트' }[view];
  if (view === 'notebook') renderNotebook();
  requestAnimationFrame(() => { drawAll(); setHeight(); });
  window.scrollTo({ top: 0, behavior: reducedMotion.matches ? 'instant' : 'smooth' });
}
function switchTab(tab) {
  activeTab = tab;
  document.querySelectorAll('[data-tab]').forEach(el => { const active = el.dataset.tab === tab; el.classList.toggle('active',active); el.setAttribute('aria-selected',active); el.tabIndex = active ? 0 : -1; });
  ['orbit','energy','compare'].forEach(name => { $(`panel-${name}`).hidden = name !== tab; });
  requestAnimationFrame(() => { drawAll(); setHeight(); });
}
function selectLesson(id) {
  const lesson = experiment.lessons.find(l => l.id === id);
  activeLesson = id; $('mission-question').textContent = lesson.question; $('experiment-title').innerHTML = `${{mass:'태양 질량 변화 실험',escape:'탈출 임계값 탐구',kepler:'케플러 법칙 검증',energy:'에너지 보존 검증'}[id]}<span class="live-dot"></span>`;
  document.querySelector('.panel-heading .section-index').textContent = `EXPERIMENT ${lesson.number}`;
  settings = { mass: lesson.mass, radius: lesson.radius, model: lesson.model, step: 1 };
  switchView('lab'); switchTab(id === 'energy' ? 'energy' : id === 'kepler' ? 'compare' : 'orbit'); renderLessons(); queueExperiment();
}
function renderLessons() {
  if (!experiment) return;
  $('lesson-nav').innerHTML = experiment.lessons.map(l => `<button data-lesson="${l.id}" class="${activeLesson === l.id ? 'active ' : ''}${completed.includes(l.id) ? 'completed' : ''}"><span class="lesson-circle">${completed.includes(l.id) ? '✓' : l.number}</span>${{mass:'질량과 궤도의 관계',escape:'태양계를 벗어나는 경계',kepler:'케플러 법칙 검증',energy:'에너지 보존과 오차'}[l.id]}${activeLesson === l.id ? '<span>›</span>' : ''}</button>`).join('');
  $('lesson-cards').innerHTML = experiment.lessons.map(l => `<article class="lesson-card"><span class="section-index">EXPLORATION ${l.number} · ${l.tag}</span><h2>${l.title}</h2><p>${l.question}</p><div class="lesson-card-footer"><span>${completed.includes(l.id) ? '✓ 탐구 기록 완료' : `${l.minutes}분 · 가설과 관찰`}</span><button class="button" data-lesson="${l.id}">탐구 시작하기 <span>→</span></button></div></article>`).join('');
  const count = experiment.lessons.filter(l => completed.includes(l.id)).length;
  $('course-progress-copy').textContent = `${count} / 4 탐구 완료`; $('course-progress-percent').textContent = `${count * 25}%`; $('course-progress-bar').style.width = `${count * 25}%`; $('note-count').textContent = notes.length;
}
const scenarios = [
  ['질량이 20% 가벼워진 태양', .8, 1, 'impulse', 'bound'], ['탈출의 경계, 절반의 태양', .5, 1, 'impulse', 'escape'], ['가벼운 태양을 떠나는 지구', .4, 1, 'impulse', 'escape'],
  ['태양이 1.5배 무거워진다면', 1.5, 1, 'impulse', 'bound'], ['두 배 무거운 태양의 원궤도', 2, 1, 'circular', 'circular'], ['조금 더 멀리, 1.5 AU', 1, 1.5, 'circular', 'circular'],
  ['태양에 더 가까이, 0.7 AU', 1, .7, 'circular', 'circular'], ['지금의 태양계와 비교하기', 1, 1, 'impulse', 'bound'], ['경계에 가까운 타원 궤도', .6, 1, 'impulse', 'bound'],
];
let libraryFilter = 'all';
function renderLibrary() {
  $('library-cards').innerHTML = scenarios.map((s,i) => ({s,i})).filter(({s}) => libraryFilter === 'all' || s[4] === libraryFilter).map(({s,i}) => `<button class="library-card" data-scenario="${i}"><div class="library-orbit">${svg(s[4] === 'escape' ? 'spark' : 'orbit')}</div><span class="section-index">SCENARIO ${String(i+1).padStart(2,'0')}</span><h2>${s[0]}</h2><p>${s[1].toFixed(2)} M☉ · ${s[2].toFixed(2)} AU · ${s[3] === 'impulse' ? '순간 변화' : '원궤도'}</p><span>이 조건으로 실험하기 <span>↗</span></span></button>`).join('');
}
function renderNotebook() {
  if (!notes.length) { $('notebook-list').innerHTML = `<div class="empty-notebook"><span>${svg('book')}</span><h2>첫 번째 발견을 기다리고 있어요.</h2><p>실험실에서 조건을 바꾸고, 관찰한 내용을 노트에 저장해 보세요.</p><button class="button primary" data-view="lab">실험실로 돌아가기 <span>→</span></button></div>`; return; }
  $('notebook-list').innerHTML = [...notes].reverse().map(n => `<article class="note-card"><div class="note-card-head"><h2>${escapeHTML(n.title)}</h2><time>${new Date(n.createdAt).toLocaleString('ko-KR')}</time></div><p class="note-settings">M = ${fmt(n.settings.mass)} M☉ · r₀ = ${fmt(n.settings.radius)} AU · ${n.settings.model === 'impulse' ? '순간 변화' : '원궤도'} · Δt ${n.settings.step}일</p>${n.hypothesis ? `<h3>나의 가설</h3><p>${escapeHTML(n.hypothesis)}</p>` : ''}<h3>관찰과 설명</h3><p>${escapeHTML(n.observation)}</p><h3>저장 시 계산 결과</h3><p>e = ${fmt(n.elements.eccentricity,3)} · ${labels[n.elements.state] || ''} · 공전 주기 ${n.elements.period_days ? fmt(n.elements.period_days,1)+'일' : '정의 안 됨'}</p><div class="note-card-footer"><button class="text-button" data-restore="${escapeHTML(n.id)}">조건 다시 불러오기 →</button><button class="text-button" data-note-csv="${escapeHTML(n.id)}">CSV 저장</button><button class="text-button delete-note" data-delete="${escapeHTML(n.id)}">기록 삭제</button></div></article>`).join('');
}
function storeNotes() {
  localStorage.setItem('orbit-notes-v1', JSON.stringify(notes));
  localStorage.setItem('orbit-completed-v1', JSON.stringify(completed));
}
function download(text, filename, type) { const url = URL.createObjectURL(new Blob([text], {type})); const link = document.createElement('a'); link.href = url; link.download = filename; link.click(); setTimeout(() => URL.revokeObjectURL(url), 3000); }
function exportCSV(data = experiment) {
  const s = data.settings, e = data.elements;
  const lines = [['time_year','x_au','y_au','normalized_energy_error_pct','mass_solar','initial_radius_au','model','step_days','eccentricity','period_days','energy_km2_s2']];
  data.simulation.trajectory.forEach((p,i) => lines.push([...p,data.simulation.diagnostics[i][1],s.mass,s.radius,s.model,s.step,e.eccentricity,e.period_days ?? '',e.energy_km2_s2]));
  download('\uFEFF'+lines.map(row => row.join(',')).join('\r\n'), `orbit-lab_M${s.mass}_r${s.radius}_${s.model}.csv`, 'text/csv;charset=utf-8');
  toast('계산 조건과 궤도 데이터를 CSV로 내보냈습니다.');
}

// Canvas drawing uses the Python trajectory, rather than decorative orbit paths.
function canvasContext(id) {
  const canvas = $(id), rect = canvas.getBoundingClientRect();
  if (!rect.width || !rect.height) return null;
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  if (canvas.width !== Math.round(rect.width*dpr) || canvas.height !== Math.round(rect.height*dpr)) { canvas.width = Math.round(rect.width*dpr); canvas.height = Math.round(rect.height*dpr); }
  const ctx = canvas.getContext('2d'); ctx.setTransform(dpr,0,0,dpr,0,0); ctx.clearRect(0,0,rect.width,rect.height);
  return {ctx,w:rect.width,h:rect.height};
}
function drawOrbit() {
  if (!experiment || activeView !== 'lab' || activeTab !== 'orbit') return;
  const info = canvasContext('orbit-canvas'); if (!info) return;
  const {ctx,w,h} = info, trajectory = experiment.simulation.trajectory;
  const radius = settings.radius;
  let xmin=-radius, xmax=radius, ymin=-radius, ymax=radius;
  trajectory.forEach(p => {xmin=Math.min(xmin,p[1]);xmax=Math.max(xmax,p[1]);ymin=Math.min(ymin,p[2]);ymax=Math.max(ymax,p[2]);});
  const padX = w<420 ? 38 : 65, padY = 56;
  const scale = Math.min((w-padX*2)/(xmax-xmin), (h-padY*2)/(ymax-ymin));
  const centerX=w/2-(xmin+xmax)/2*scale, centerY=h/2+(ymin+ymax)/2*scale;
  const px=x=>centerX+x*scale, py=y=>centerY-y*scale;
  // Quiet deterministic star field.
  for (let i=0;i<95;i++) { const x=((Math.sin(i*54.31+4)*43758.5453)%1+1)%1*w; const y=((Math.sin(i*12.91+8)*27182.31)%1+1)%1*h; ctx.fillStyle=i%9===0?'#76849b66':'#5c71922b';ctx.beginPath();ctx.arc(x,y,i%9===0?.8:.5,0,Math.PI*2);ctx.fill(); }
  ctx.save(); ctx.strokeStyle='#53637914'; ctx.lineWidth=1;
  ctx.beginPath();ctx.moveTo(0,centerY);ctx.lineTo(w,centerY);ctx.moveTo(centerX,0);ctx.lineTo(centerX,h);ctx.stroke();
  const gridStep = Math.max(.5, Math.ceil(Math.max(xmax-xmin,ymax-ymin)/6*2)/2);
  for(let r=gridStep;r<=Math.max(xmax-xmin,ymax-ymin);r+=gridStep) {ctx.beginPath();ctx.arc(centerX,centerY,r*scale,0,Math.PI*2);ctx.stroke();}
  ctx.setLineDash([3,5]);ctx.strokeStyle='#9bacc04d';ctx.lineWidth=1;ctx.beginPath();ctx.arc(centerX,centerY,radius*scale,0,Math.PI*2);ctx.stroke();ctx.setLineDash([]);
  // A small original-orbit marker provides the baseline comparison at equal t.
  const baselineAngle=2*Math.PI*simTime/Math.sqrt(radius**3);
  const bx=px(radius*Math.cos(baselineAngle)),by=py(radius*Math.sin(baselineAngle));
  ctx.fillStyle='#91a1b866';ctx.beginPath();ctx.arc(bx,by,3,0,Math.PI*2);ctx.fill();
  ctx.font='8px -apple-system,sans-serif';ctx.fillStyle='#8291a5';
  if(w>400)ctx.fillText('기준 지구',Math.min(w-50,bx+9),Math.max(55,by-6));
  ctx.beginPath();trajectory.forEach((p,i)=>i?ctx.lineTo(px(p[1]),py(p[2])):ctx.moveTo(px(p[1]),py(p[2])));ctx.strokeStyle='#61dec25e';ctx.lineWidth=1.2;ctx.stroke();
  // Highlight only the elapsed segment, preserving physical time spacing.
  ctx.beginPath();let started=false;trajectory.forEach(p=>{if(p[0]<=simTime){started?ctx.lineTo(px(p[1]),py(p[2])):ctx.moveTo(px(p[1]),py(p[2]));started=true;}});ctx.strokeStyle='#76f0d5';ctx.lineWidth=1.65;ctx.shadowColor='#61dec233';ctx.shadowBlur=6;ctx.stroke();ctx.shadowBlur=0;
  const sunGlow=ctx.createRadialGradient(centerX,centerY,0,centerX,centerY,47);sunGlow.addColorStop(0,'#ffbf702e');sunGlow.addColorStop(.4,'#ff9f2e12');sunGlow.addColorStop(1,'#ff9f2e00');ctx.fillStyle=sunGlow;ctx.beginPath();ctx.arc(centerX,centerY,47,0,Math.PI*2);ctx.fill();
  const sunR=11+Math.sqrt(settings.mass)*3;const sun=ctx.createRadialGradient(centerX-4,centerY-4,0,centerX,centerY,sunR);sun.addColorStop(0,'#ffe6a5');sun.addColorStop(.45,'#ffc567');sun.addColorStop(1,'#ec813b');ctx.fillStyle=sun;ctx.shadowColor='#ffae5d88';ctx.shadowBlur=16;ctx.beginPath();ctx.arc(centerX,centerY,sunR,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0;
  ctx.font='9px -apple-system,sans-serif';ctx.fillStyle='#d9b385';ctx.textAlign='center';ctx.fillText('태양',centerX,centerY+sunR+17);ctx.fillStyle='#8b7865';ctx.font='7px monospace';ctx.fillText(`${settings.mass.toFixed(2)} M☉`,centerX,centerY+sunR+29);
  let index=trajectory.findIndex(p=>p[0]>=simTime);if(index<0)index=trajectory.length-1;const p1=trajectory[Math.max(0,index-1)],p2=trajectory[index];const t=p2[0]===p1[0]?0:(simTime-p1[0])/(p2[0]-p1[0]);
  const x=px(p1[1]+(p2[1]-p1[1])*t),y=py(p1[2]+(p2[2]-p1[2])*t);
  const earth=ctx.createRadialGradient(x-2,y-2,0,x,y,6);earth.addColorStop(0,'#c0f7ed');earth.addColorStop(.55,'#61cbbd');earth.addColorStop(1,'#357f94');ctx.fillStyle=earth;ctx.shadowColor='#61dec288';ctx.shadowBlur=16;ctx.beginPath();ctx.arc(x,y,5.5,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0;
  ctx.strokeStyle='#61dec254';ctx.lineWidth=.6;ctx.beginPath();ctx.arc(x,y,10,0,Math.PI*2);ctx.stroke();ctx.textAlign='left';ctx.font='9px -apple-system,sans-serif';ctx.fillStyle='#b7e7df';ctx.fillText('지구',Math.min(w-36,x+14),Math.max(50,y-7));
  ctx.fillStyle='#5c6d82';ctx.font='7px monospace';ctx.fillText('+X',w-23,Math.min(h-38,centerY-6));ctx.fillText('+Y',Math.min(w-22,centerX+7),43);
  // Scale bar is always one physical AU in the selected view.
  let bar=1;if(scale>120)bar=.5;if(scale<35)bar=2;
  $('scale-mark').style.width=`${scale*bar}px`;$('scale-label').textContent=`${bar} AU`;
  ctx.restore();
  $('simulation-day').textContent=`DAY ${String(Math.floor(simTime*365.25)).padStart(3,'0')}`;
  $('timeline-progress').style.width=`${simTime/experiment.simulation.duration_years*100}%`;
}
function drawEnergy() {
  if (!experiment || activeView!=='lab' || activeTab!=='energy')return;
  const info=canvasContext('energy-canvas');if(!info)return;
  const {ctx,w,h}=info, pts=experiment.simulation.diagnostics;
  const pad={l:53,r:13,t:25,b:34};const max=Math.max(...pts.map(p=>Math.abs(p[1])),.000001)*1.2;
  const X=t=>pad.l+t/experiment.simulation.duration_years*(w-pad.l-pad.r),Y=v=>h-pad.b-(v+max)/(2*max)*(h-pad.t-pad.b);
  ctx.font='8px monospace';ctx.lineWidth=1;
  for(let i=0;i<5;i++){const v=-max+i*max/2;const y=Y(v);ctx.strokeStyle='#34425455';ctx.beginPath();ctx.moveTo(pad.l,y);ctx.lineTo(w-pad.r,y);ctx.stroke();ctx.fillStyle='#8291a5';ctx.textAlign='right';ctx.fillText(Math.abs(v)<1e-12?'0':v.toExponential(1),pad.l-9,y+3);}
  ctx.textAlign='center';for(let i=0;i<5;i++){const t=i*experiment.simulation.duration_years/4;ctx.fillText(`${fmt(t,1)}`,X(t),h-14);}ctx.textAlign='right';ctx.fillText('년',w-pad.r,h-2);
  ctx.beginPath();pts.forEach((p,i)=>i?ctx.lineTo(X(p[0]),Y(p[1])):ctx.moveTo(X(p[0]),Y(p[1])));ctx.strokeStyle='#61dec2';ctx.lineWidth=1.7;ctx.stroke();
  ctx.fillStyle='#61dec2';ctx.textAlign='left';ctx.font='9px -apple-system,sans-serif';ctx.fillText(`최대 ${experiment.simulation.max_energy_error_pct.toExponential(2)}%`,pad.l,12);
}
function drawThreshold() {
  if(!experiment||activeView!=='lab')return;const info=canvasContext('threshold-canvas');if(!info)return;
  const {ctx,w,h}=info,pad={l:37,r:22,t:17,b:30};const X=v=>pad.l+(v-.2)/1.8*(w-pad.l-pad.r),Y=v=>h-pad.b-v/2*(h-pad.t-pad.b);
  ctx.fillStyle='#eab06a07';ctx.fillRect(X(.2),pad.t,X(.5)-X(.2),h-pad.b-pad.t);
  ctx.font='8px monospace';ctx.lineWidth=1;
  [0,.5,1,1.5,2].forEach(v=>{ctx.strokeStyle='#42506435';ctx.beginPath();ctx.moveTo(pad.l,Y(v));ctx.lineTo(w-pad.r,Y(v));ctx.stroke();ctx.textAlign='right';ctx.fillStyle='#78889e';ctx.fillText(v.toFixed(1),pad.l-10,Y(v)+3);});
  [.2,.5,1,1.5,2].forEach(v=>{ctx.textAlign='center';ctx.fillStyle='#78889e';ctx.fillText(v.toFixed(1),X(v),h-12);});
  ctx.setLineDash([3,4]);ctx.strokeStyle='#eeb77580';ctx.beginPath();ctx.moveTo(X(.5),pad.t);ctx.lineTo(X(.5),h-pad.b);ctx.moveTo(pad.l,Y(1));ctx.lineTo(w-pad.r,Y(1));ctx.stroke();ctx.setLineDash([]);
  ctx.save();ctx.beginPath();ctx.rect(pad.l,pad.t,w-pad.l-pad.r,h-pad.t-pad.b);ctx.clip();ctx.beginPath();experiment.threshold.forEach((p,i)=>i?ctx.lineTo(X(p[0]),Y(p[1])):ctx.moveTo(X(p[0]),Y(p[1])));ctx.lineWidth=1.6;ctx.strokeStyle='#61dec2';ctx.stroke();const e=Math.abs(1-settings.mass)/settings.mass;if(e<=2){ctx.fillStyle='#61dec2';ctx.beginPath();ctx.arc(X(settings.mass),Y(e),3.7,0,Math.PI*2);ctx.fill();ctx.strokeStyle='#61dec244';ctx.beginPath();ctx.arc(X(settings.mass),Y(e),7,0,Math.PI*2);ctx.stroke();}ctx.restore();
  ctx.fillStyle='#c9a777';ctx.textAlign='left';ctx.font='8px -apple-system,sans-serif';ctx.fillText('탈출 경계',X(.5)+6,pad.t+7);ctx.fillStyle='#7d8fa6';ctx.font='7px monospace';ctx.textAlign='right';ctx.fillText('M / M☉',w-pad.r,h-1);ctx.textAlign='left';ctx.fillText('e',pad.l-18,10);
}
function drawAll(){drawOrbit();drawEnergy();drawThreshold();}
function updatePlayButton(){ $('play-button').innerHTML=svg(playing?'pause':'play');$('play-button').setAttribute('aria-label',playing?'애니메이션 일시 정지':'애니메이션 재생'); }
function animationFrame(timestamp){
  const delta=Math.min((timestamp-(lastFrame||timestamp))/1000,.08);lastFrame=timestamp;
  if(experiment&&playing&&activeView==='lab'&&activeTab==='orbit'&&!document.hidden){simTime+=delta*.12*speed;if(simTime>=experiment.simulation.duration_years){simTime=experiment.simulation.duration_years;playing=false;updatePlayButton();}drawOrbit();}
  requestAnimationFrame(animationFrame);
}
requestAnimationFrame(animationFrame);

// Interaction handlers.
$('mass-slider').addEventListener('input',event=>{settings.mass=Number(event.target.value);queueExperiment();});
$('radius-slider').addEventListener('input',event=>{settings.radius=Number(event.target.value);queueExperiment();});
$('step-select').addEventListener('change',event=>{settings.step=Number(event.target.value);queueExperiment();});
document.addEventListener('click',event=>{
  const target=event.target.closest('button,a');if(!target)return;
  if(target.dataset.view){event.preventDefault();switchView(target.dataset.view);}
  if(target.dataset.tab)switchTab(target.dataset.tab);
  if(target.dataset.model){settings.model=target.dataset.model;queueExperiment();}
  if(target.dataset.mass){settings.mass=Number(target.dataset.mass);queueExperiment();}
  if(target.dataset.lesson&&experiment)selectLesson(target.dataset.lesson);
  if(target.dataset.filter){libraryFilter=target.dataset.filter;document.querySelectorAll('[data-filter]').forEach(el=>el.classList.toggle('active',el===target));renderLibrary();setHeight();}
  if(target.dataset.scenario!=null){const s=scenarios[Number(target.dataset.scenario)];activeLesson=s[3]==='circular'?'kepler':s[1]<=.5?'escape':'mass';$('mission-question').textContent=`${s[0]}: 궤도와 에너지는 어떻게 달라질까요?`;$('experiment-title').textContent=s[0];settings={mass:s[1],radius:s[2],model:s[3],step:1};switchView('lab');switchTab('orbit');renderLessons();queueExperiment();}
  if(target.dataset.restore){const note=notes.find(n=>n.id===target.dataset.restore);if(note){settings={...note.settings};activeLesson=note.lesson;$('experiment-title').textContent=note.title;$('mission-question').textContent='저장한 실험의 조건과 결과를 다시 검토해 보세요.';switchView('lab');switchTab('orbit');renderLessons();queueExperiment();}}
  if(target.dataset.noteCsv){const note=notes.find(n=>n.id===target.dataset.noteCsv);if(note)exportCSV(note);}
  if(target.dataset.delete){const index=notes.findIndex(n=>n.id===target.dataset.delete);if(index>=0){const [removed]=notes.splice(index,1);try{storeNotes();renderNotebook();renderLessons();setHeight();toast('기록을 삭제했습니다.');}catch{notes.splice(index,0,removed);toast('저장소 오류로 삭제하지 못했습니다.');}}}
  if(target.classList.contains('close-dialog'))target.closest('dialog').close();
});
document.querySelector('.brand').addEventListener('click',event=>{event.preventDefault();switchView('lab');});
$('next-lesson').onclick=()=>{if(experiment){const i=experiment.lessons.findIndex(l=>l.id===activeLesson);selectLesson(experiment.lessons[(i+1)%4].id);}};
['guide-button','help-top'].forEach(id=>$(id).onclick=()=>$('guide-dialog').showModal());
$('assumptions-button').onclick=()=>$('assumptions-dialog').showModal();
$('play-button').onclick=()=>{if(experiment&&simTime>=experiment.simulation.duration_years)simTime=0;playing=!playing;updatePlayButton();drawOrbit();};
$('restart-button').onclick=()=>{simTime=0;drawOrbit();toast('시뮬레이션 시간을 처음으로 되돌렸습니다.');};
$('speed-button').onclick=()=>{speed=({1:2,2:4,4:.5,.5:1})[speed];$('speed-button').innerHTML=`${speed}× <span>⌄</span>`;};
$('reset-view').onclick=()=>{simTime=0;drawOrbit();};
$('reset-settings').onclick=()=>{settings={mass:.8,radius:1,model:'impulse',step:1};queueExperiment();toast('실험 조건을 초기값으로 되돌렸습니다.');};
$('fullscreen-button').onclick=async()=>{try{const panel=document.querySelector('.visualization-panel');if(document.fullscreenElement)await document.exitFullscreen();else await panel.requestFullscreen();setTimeout(drawAll,100);}catch{toast('브라우저의 전체 화면 권한을 확인해주세요.');}};
$('save-experiment').onclick=()=>{$('save-dialog').showModal();};
$('save-form').onsubmit=event=>{
  event.preventDefault();if(!experiment)return;
  const observation=$('note-observation').value.trim();if(!observation){$('note-observation').setCustomValidity('관찰한 내용을 입력해주세요.');$('note-observation').reportValidity();return;}
  const previousCompleted=[...completed];
  const record={id:globalThis.crypto?.randomUUID?.()||`${Date.now()}-${Math.random()}`,createdAt:new Date().toISOString(),title:$('experiment-title').textContent||'나의 궤도 실험',lesson:activeLesson,hypothesis:$('note-hypothesis').value.trim(),observation,settings:{...experiment.settings},elements:{...experiment.elements},simulation:experiment.simulation};
  notes.push(record);if(!completed.includes(activeLesson))completed.push(activeLesson);
  try{storeNotes();$('save-dialog').close();$('save-form').reset();renderLessons();renderNotebook();toast('발견을 저장했습니다. 나의 탐구 노트에서 확인하세요.');setHeight();}catch{notes.pop();completed=previousCompleted;toast('브라우저 저장 공간이 부족합니다. 기존 노트를 백업해 주세요.');}
};
$('note-observation').addEventListener('input',()=>{$('note-observation').setCustomValidity('');});
$('export-csv').onclick=()=>experiment&&exportCSV();
$('export-notes').onclick=()=>{download(JSON.stringify({version:1,exportedAt:new Date().toISOString(),notes,completed},null,2),'orbit-lab-notes.json','application/json');toast('탐구 노트를 JSON 파일로 백업했습니다.');};
document.querySelector('.tabs').addEventListener('keydown',event=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;event.preventDefault();const tabs=['orbit','energy','compare'];let i=tabs.indexOf(activeTab);i=event.key==='Home'?0:event.key==='End'?2:(i+(event.key==='ArrowRight'?1:2))%3;switchTab(tabs[i]);$(`tab-${tabs[i]}`).focus();});
document.querySelectorAll('dialog').forEach(dialog=>dialog.addEventListener('click',event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();}}));
window.addEventListener('resize',()=>{drawAll();setHeight();});
document.addEventListener('fullscreenchange',()=>setTimeout(drawAll,80));
reducedMotion.addEventListener('change',event=>{if(event.matches){playing=false;updatePlayButton();}});
new ResizeObserver(()=>setHeight()).observe(document.querySelector('.app-shell'));

if(framed){
  window.addEventListener('message',event=>{if(event.source===window.parent&&event.data?.type==='streamlit:render'&&event.data.args?.experiment)receiveExperiment(event.data.args.experiment);});
  streamlitMessage('streamlit:componentReady',{apiVersion:1});setHeight();
}else{requestExperiment();}
