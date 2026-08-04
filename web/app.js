const chat = document.querySelector('#chat');
const form = document.querySelector('#composer');
const input = document.querySelector('#message');
const send = document.querySelector('#send');
const topK = document.querySelector('#topK');
const topKValue = document.querySelector('#topKValue');
let history = [];
// When index.html is double-clicked, its origin is file:// and relative fetch()
// cannot find Flask. In that case, use the standard local server explicitly.
const apiUrl = window.location.protocol === 'file:'
  ? 'http://127.0.0.1:8000/api/chat'
  : '/api/chat';

const escapeHtml = (text = '') => String(text).replace(/[&<>'"]/g, char => ({ '&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;' }[char]));
function scrollDown() { chat.scrollTop = chat.scrollHeight; }
function addMessage(role, content, extraClass = '') {
  const message = document.createElement('article');
  message.className = `message ${role} ${extraClass}`;
  message.innerHTML = role === 'assistant'
    ? `<div class="avatar">✦</div><div class="bubble">${content}</div>`
    : `<div class="bubble">${escapeHtml(content)}</div>`;
  chat.append(message); scrollDown(); return message;
}
function addSources(sources) {
  if (!sources?.length) return;
  const template = document.querySelector('#sourceTemplate');
  const details = template.content.firstElementChild.cloneNode(true);
  details.querySelector('summary span').textContent = `(${sources.length} tài liệu)`;
  const list = details.querySelector('.source-list');
  sources.forEach((source, i) => {
    const meta = source.metadata || {};
    const name = meta.source || `Tài liệu ${i + 1}`;
    const type = meta.type || 'document';
    const score = Number(source.score || 0).toFixed(3);
    list.insertAdjacentHTML('beforeend', `<div class="source-card"><strong>${i + 1}. ${escapeHtml(name)}</strong><small> · ${escapeHtml(type)} · ${score}</small><p>${escapeHtml(String(source.content || '').slice(0, 260))}…</p></div>`);
  });
  chat.append(details); scrollDown();
}
function resetChat() {
  chat.innerHTML = `<article class="message assistant welcome"><div class="avatar">✦</div><div class="bubble"><p class="greeting">Một hải trình mới bắt đầu.</p><p>Mình sẵn sàng giúp bạn khám phá kho tư liệu về Vịnh Hạ Long.</p></div></article>`;
  input.focus();
  history = [];
}
async function submitQuestion(question) {
  const message = question.trim(); if (!message) return;
  addMessage('user', message); input.value = ''; input.style.height = 'auto'; send.disabled = true;
  history.push({ role: 'user', content: message });
  const loading = addMessage('assistant', `Đang rà bản đồ tri thức<span class="dots"></span>`, 'loading');
  try {
    const response = await fetch(apiUrl, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message, top_k: topK.value, history: history.slice(0, -1) }) });
    const data = await response.json().catch(() => ({ error: 'Máy chủ trả về phản hồi không hợp lệ.' }));
    loading.remove();
    if (!response.ok) throw new Error(data.error || 'Đã xảy ra lỗi không xác định.');
    addMessage('assistant', escapeHtml(data.answer).replace(/\n/g, '<br>'));
    addSources(data.sources);
    history.push({ role: 'assistant', content: data.answer });
  } catch (error) {
    loading.remove();
    const detail = error instanceof TypeError
      ? 'Không thể kết nối với máy chủ. Hãy chạy <code>python app.py</code>, rồi mở <code>http://127.0.0.1:8000</code>.'
      : escapeHtml(error.message);
    addMessage('assistant', `<p class="greeting">Chưa thể ra khơi</p><p>${detail}</p>`);
  }
  finally { send.disabled = false; input.focus(); }
}
form.addEventListener('submit', event => { event.preventDefault(); submitQuestion(input.value); });
input.addEventListener('input', () => { input.style.height = 'auto'; input.style.height = `${Math.min(input.scrollHeight, 140)}px`; });
input.addEventListener('keydown', event => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); form.requestSubmit(); } });
document.querySelector('#suggestions').addEventListener('click', event => { if (event.target.matches('button')) submitQuestion(event.target.textContent); });
document.querySelector('#newChat').addEventListener('click', resetChat);
topK.addEventListener('input', () => topKValue.value = topK.value);
