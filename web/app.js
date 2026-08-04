const chat = document.querySelector('#chat');
const form = document.querySelector('#composer');
const input = document.querySelector('#message');
const send = document.querySelector('#send');
const topK = document.querySelector('#topK');
const topKValue = document.querySelector('#topKValue');
let history = [];

const apiUrl = window.location.protocol === 'file:' ? 'http://127.0.0.1:8000/api/chat' : '/api/chat';
const escapeHtml = (text = '') => String(text).replace(/[&<>'"]/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
}[char]));
const regexEscape = text => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

function highlightSnippet(text, query) {
  let safe = escapeHtml(String(text || '').slice(0, 320));
  const terms = [...new Set(String(query || '').toLocaleLowerCase('vi').match(/[\p{L}\p{N}]+/gu) || [])]
    .filter(term => term.length >= 3)
    .sort((a, b) => b.length - a.length);
  if (!terms.length) return safe;
  return safe.replace(new RegExp(`(${terms.map(regexEscape).join('|')})`, 'giu'), '<mark>$1</mark>');
}

function scrollDown() { chat.scrollTop = chat.scrollHeight; }

function addMessage(role, content, extraClass = '') {
  const message = document.createElement('article');
  message.className = `message ${role} ${extraClass}`;
  message.innerHTML = role === 'assistant'
    ? `<div class="avatar">✦</div><div class="bubble">${content}</div>`
    : `<div class="bubble">${escapeHtml(content)}</div>`;
  chat.append(message);
  scrollDown();
  return message;
}

function addRunMeta(data) {
  const meta = document.createElement('div');
  meta.className = 'run-meta';
  meta.innerHTML = `<span>Retrieval: ${escapeHtml(data.retrieval_source || 'unknown')}</span><span>Generation: ${escapeHtml(data.generation_mode || 'unknown')}</span>`;
  chat.append(meta);
}

function addSources(sources, query) {
  if (!sources?.length) return;
  const template = document.querySelector('#sourceTemplate');
  const details = template.content.firstElementChild.cloneNode(true);
  details.querySelector('summary span').textContent = `(${sources.length} tài liệu)`;
  const list = details.querySelector('.source-list');
  const maxScore = Math.max(...sources.map(source => Number(source.score) || 0), 0.0001);

  sources.forEach((source, i) => {
    const meta = source.metadata || {};
    const name = meta.source || `Tài liệu ${i + 1}`;
    const type = meta.type || 'document';
    const numericScore = Number(source.score) || 0;
    const score = numericScore.toFixed(3);
    const scoreWidth = Math.max(4, Math.round(numericScore / maxScore * 100));
    const citation = source.citation
      ? `<span class="citation-chip">${escapeHtml(source.citation)}</span>` : '';
    list.insertAdjacentHTML('beforeend', `
      <article class="source-card">
        <div class="source-head"><strong>${i + 1}. ${escapeHtml(name)}</strong><span class="score-chip" title="Điểm retrieval">Score ${score}</span></div>
        <small>${escapeHtml(type)}</small>${citation}
        <div class="score-track" aria-label="Điểm liên quan ${score}"><i style="width:${scoreWidth}%"></i></div>
        <p>${highlightSnippet(source.content, query)}…</p>
      </article>`);
  });
  chat.append(details);
  scrollDown();
}

function resetChat() {
  chat.innerHTML = '<article class="message assistant welcome"><div class="avatar">✦</div><div class="bubble"><p class="greeting">Một hải trình mới bắt đầu.</p><p>Mình sẵn sàng giúp bạn khám phá kho tư liệu về Vịnh Hạ Long.</p></div></article>';
  history = [];
  input.focus();
}

async function submitQuestion(question) {
  const message = question.trim();
  if (!message) return;
  addMessage('user', message);
  input.value = '';
  input.style.height = 'auto';
  send.disabled = true;
  history.push({ role: 'user', content: message });
  const loading = addMessage('assistant', 'Đang rà bản đồ tri thức<span class="dots"></span>', 'loading');
  try {
    const response = await fetch(apiUrl, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, top_k: topK.value, history: history.slice(0, -1) })
    });
    const data = await response.json().catch(() => ({ error: 'Máy chủ trả về phản hồi không hợp lệ.' }));
    loading.remove();
    if (!response.ok) throw new Error(data.error || 'Đã xảy ra lỗi không xác định.');
    addMessage('assistant', escapeHtml(data.answer).replace(/\n/g, '<br>'));
    addRunMeta(data);
    addSources(data.sources, message);
    history.push({ role: 'assistant', content: data.answer });
  } catch (error) {
    loading.remove();
    const detail = error instanceof TypeError
      ? 'Không thể kết nối với máy chủ. Hãy chạy <code>python app.py</code> rồi mở <code>http://127.0.0.1:8000</code>.'
      : escapeHtml(error.message);
    addMessage('assistant', `<p class="greeting">Chưa thể ra khơi</p><p>${detail}</p>`);
  } finally {
    send.disabled = false;
    input.focus();
  }
}

form.addEventListener('submit', event => { event.preventDefault(); submitQuestion(input.value); });
input.addEventListener('input', () => { input.style.height = 'auto'; input.style.height = `${Math.min(input.scrollHeight, 140)}px`; });
input.addEventListener('keydown', event => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); form.requestSubmit(); } });
document.querySelector('#suggestions').addEventListener('click', event => { if (event.target.matches('button')) submitQuestion(event.target.textContent); });
document.querySelector('#newChat').addEventListener('click', resetChat);
topK.addEventListener('input', () => { topKValue.value = topK.value; });
