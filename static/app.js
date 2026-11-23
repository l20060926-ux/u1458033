const grid = document.querySelector('#jobGrid');
const count = document.querySelector('#count');
const state = { q: '', category: '', quick_tag: '', no_experience: false, sort: 'newest' };
let activeJob = null;
const money = n => new Intl.NumberFormat('zh-TW').format(n);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function loadJobs() {
  const params = new URLSearchParams();
  for (const [k,v] of Object.entries(state)) if (v !== '' && v !== false) params.set(k, v);
  if (state.no_experience) params.set('no_experience','true');
  grid.innerHTML = '<div class="loading">正在為你找好工作…</div>';
  try {
    const r = await fetch(`/api/jobs?${params}`); const data = await r.json();
    if (!r.ok) throw new Error(data.error || '載入失敗');
    count.textContent = data.count;
    document.querySelector('#resultLabel').textContent = data.count ? `找到 ${data.count} 個適合你的機會` : '換個條件，再看看好工作';
    const category = document.querySelector('#category');
    if (category.options.length === 1) data.categories.slice(1).forEach(c => category.add(new Option(c,c)));
    grid.innerHTML = data.jobs.length ? data.jobs.map(job => `<article class="job-card"><div class="card-top"><span class="company-mark">${job.category==='餐飲服務'?'☕':job.category==='活動展場'?'✳':job.category==='家教伴讀'?'✎':'☼'}</span><span class="fresh">${job.status==='open'?'正在招募':job.status==='applied'?'已應徵':'已完成'}</span></div><h3>${esc(job.title)}</h3><div class="company">${esc(job.company)}</div><div class="pay-row"><strong>NT$ ${money(job.pay_per_hour)}</strong><span>/ 小時</span><span class="total">${job.hours} 小時約 <b>$${money(job.pay_per_hour*job.hours)}</b></span></div><div class="meta"><span>${esc(job.location)} · ${esc(job.category)}</span><span>${esc(job.schedule)}</span></div><div class="tags">${job.no_experience?'<span class="tag">免經驗・新手友善</span>':''}${(job.tags||[]).slice(0,2).map(t=>`<span class="tag ${t.includes('高時薪')?'orange':''}">${esc(t)}</span>`).join('')}</div><div class="card-actions"><button class="apply-btn" data-apply="${job.id}" ${job.status!=='open'?'disabled':''}>${job.status==='open'?'一鍵快速應徵 →':job.status==='applied'?'已送出應徵':'已完成'}</button><button class="detail-btn" data-detail="${job.id}">工作內容</button></div></article>`).join('') : '<div class="empty">目前沒有符合條件的職缺，試試清除篩選條件吧。</div>';
  } catch(e) { grid.innerHTML = `<div class="empty">${esc(e.message)}</div>`; }
}
document.querySelector('#searchForm').addEventListener('submit', e => {e.preventDefault();state.q=document.querySelector('#searchInput').value.trim();loadJobs()});
document.querySelectorAll('[data-search]').forEach(b=>b.addEventListener('click',()=>{document.querySelector('#searchInput').value=b.dataset.search;state.q=b.dataset.search;loadJobs()}));
document.querySelectorAll('.filter').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('.filter').forEach(x=>x.classList.remove('active'));b.classList.add('active');state.quick_tag=b.dataset.filter==='no_experience'?'':b.dataset.filter;state.no_experience=b.dataset.filter==='no_experience';loadJobs()}));
document.querySelector('#category').addEventListener('change',e=>{state.category=e.target.value;loadJobs()});
document.querySelector('#sort').addEventListener('change',e=>{state.sort=e.target.value;loadJobs()});
document.querySelector('#clearFilters').addEventListener('click',()=>{Object.assign(state,{q:'',category:'',quick_tag:'',no_experience:false,sort:'newest'});document.querySelector('#searchInput').value='';document.querySelector('#category').value='全部';document.querySelector('#sort').value='newest';document.querySelectorAll('.filter').forEach((x,i)=>x.classList.toggle('active',i===0));loadJobs()});
grid.addEventListener('click', async e=>{
  const apply=e.target.closest('[data-apply]');
  const detail=e.target.closest('[data-detail]');
  if(detail){const r=await fetch(`/api/jobs/${detail.dataset.detail}`);const j=await r.json();toast(j.description||j.error);return}
  if(apply){const r=await fetch(`/api/jobs/${apply.dataset.apply}`);activeJob=await r.json();document.querySelector('#applyTitle').textContent=`${activeJob.title} · ${activeJob.company}`;document.querySelector('#applyDialog').showModal()}
});
document.querySelector('#applyForm').addEventListener('submit',async e=>{if(e.submitter?.value==='cancel')return;e.preventDefault();if(!activeJob)return;const form=new FormData(e.currentTarget);const button=document.querySelector('#applySubmit');button.disabled=true;try{const r=await fetch(`/api/jobs/${activeJob.id}/apply`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({applicant:form.get('applicant'),available_note:form.get('available_note')})});const d=await r.json();if(!r.ok)throw new Error(d.error);document.querySelector('#applyDialog').close();toast(`已為你送出「${d.title}」應徵！`);loadJobs()}catch(err){toast(err.message)}finally{button.disabled=false}});
document.querySelector('#applyDialog').addEventListener('click',e=>{if(e.target===e.currentTarget)e.currentTarget.close()});
function toast(message){const el=document.querySelector('#toast');el.textContent=message;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),3200)}
document.querySelector('#resetDemo').addEventListener('click',async()=>{const r=await fetch('/api/reset',{method:'POST'});const d=await r.json();toast(`示範資料已重置，共 ${d.count} 個職缺`);loadJobs()});
fetch('/api/quick-tip').then(r=>r.json()).then(d=>{document.querySelector('#tipText').textContent=d.tip+(d.source==='fallback'?' '+d.extra_tip:'')}).catch(()=>{document.querySelector('#tipText').textContent='面試前確認時薪、排班與工作內容；遇到要求先繳費或交出證件正本請提高警覺。'});
loadJobs();
