const $ = (id) => document.getElementById(id);
const form = $('taskForm');
const list = $('taskList');
const message = $('message');

function notify(text, success = false) {
  message.textContent = text;
  message.className = success ? 'message success' : 'message';
}

async function request(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers }
  });
  const data = response.status === 204 ? null : await response.json();
  if (!response.ok) throw new Error(data?.error || '요청 처리에 실패했습니다.');
  return data;
}

function escapeHtml(value = '') {
  return String(value).replace(/[&<>"']/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[char]);
}

function resetForm() {
  form.reset();
  $('taskId').value = '';
  $('formTitle').textContent = '새 업무 등록';
  $('submitBtn').textContent = '업무 등록';
  $('cancelBtn').classList.add('hidden');
}

function renderTasks(tasks) {
  $('totalCount').textContent = tasks.length;
  $('progressCount').textContent = tasks.filter((task) => task.status === '진행 중').length;
  $('doneCount').textContent = tasks.filter((task) => task.status === '완료').length;
  $('listCount').textContent = `${tasks.length}건`;

  if (!tasks.length) {
    list.innerHTML = '<p class="empty">등록된 업무가 없습니다.</p>';
    return;
  }

  list.innerHTML = tasks.map((task) => {
    const badgeClass = task.status === '완료' ? 'done' : task.status === '진행 중' ? 'progress' : '';
    return `<article class="task">
      <div><h3>${escapeHtml(task.title)}</h3><p>${escapeHtml(task.description || '상세 내용 없음')}</p>
      <div class="task-meta"><span class="badge ${badgeClass}">${escapeHtml(task.status)}</span><span class="muted">${escapeHtml(task.created_at)}</span></div></div>
      <div class="task-actions"><button class="button secondary" data-action="edit" data-id="${task.id}">수정</button><button class="button secondary" data-action="delete" data-id="${task.id}">삭제</button></div>
    </article>`;
  }).join('');
}

async function loadTasks() {
  try {
    renderTasks(await request('/tasks'));
    notify('');
  } catch (error) {
    notify(error.message);
    list.innerHTML = '<p class="empty">업무 목록을 불러오지 못했습니다.</p>';
  }
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const id = $('taskId').value;
  const payload = {
    title: $('title').value.trim(),
    description: $('description').value.trim(),
    status: $('status').value
  };
  if (!payload.title) return notify('업무 제목을 입력하세요.');

  try {
    await request(id ? `/tasks/${id}` : '/tasks', {
      method: id ? 'PUT' : 'POST', body: JSON.stringify(payload)
    });
    resetForm();
    notify(id ? '업무를 수정했습니다.' : '업무를 등록했습니다.', true);
    await loadTasks();
  } catch (error) { notify(error.message); }
});

list.addEventListener('click', async (event) => {
  const button = event.target.closest('button[data-action]');
  if (!button) return;
  const id = button.dataset.id;
  try {
    if (button.dataset.action === 'delete') {
      if (!window.confirm('이 업무를 삭제할까요?')) return;
      await request(`/tasks/${id}`, { method: 'DELETE' });
      notify('업무를 삭제했습니다.', true);
    } else {
      const task = await request(`/tasks/${id}`);
      $('taskId').value = task.id;
      $('title').value = task.title;
      $('description').value = task.description || '';
      $('status').value = task.status;
      $('formTitle').textContent = '업무 수정';
      $('submitBtn').textContent = '수정 저장';
      $('cancelBtn').classList.remove('hidden');
      $('title').focus();
    }
    await loadTasks();
  } catch (error) { notify(error.message); }
});

$('cancelBtn').addEventListener('click', resetForm);
$('refreshBtn').addEventListener('click', loadTasks);
loadTasks();
