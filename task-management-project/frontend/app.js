const state = { tasks: [], filter: "all", editingId: null };
const el = {
  list: document.querySelector("#task-list"), empty: document.querySelector("#empty-state"),
  message: document.querySelector("#message"), form: document.querySelector("#task-form"),
  formTitle: document.querySelector("#form-title"), title: document.querySelector("#title"),
  description: document.querySelector("#description"), status: document.querySelector("#status"),
  save: document.querySelector("#save-button"), total: document.querySelector("#total-count"),
  progress: document.querySelector("#progress-count"), completed: document.querySelector("#completed-count")
};
const labels = { pending: "Pending", in_progress: "In progress", completed: "Completed" };

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, ch => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
  })[ch]);
}
async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options, headers: { "Content-Type": "application/json", ...(options.headers || {}) }
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error || `Request failed (${response.status})`);
  return body;
}
function message(text, type = "success") {
  el.message.textContent = text;
  el.message.className = `message ${type}`;
  window.setTimeout(() => el.message.classList.add("hidden"), 4000);
}
function render() {
  el.total.textContent = state.tasks.length;
  el.progress.textContent = state.tasks.filter(t => t.status === "in_progress").length;
  el.completed.textContent = state.tasks.filter(t => t.status === "completed").length;
  const visible = state.tasks.filter(t => state.filter === "all" || t.status === state.filter);
  el.list.innerHTML = "";
  for (const task of visible) {
    const card = document.createElement("article");
    card.className = "task-card";
    const created = task.created_at ? new Date(task.created_at).toLocaleDateString() : "";
    card.innerHTML = `
      <div class="task-main">
        <h3 class="task-title ${task.status === "completed" ? "done" : ""}">${escapeHtml(task.title)}</h3>
        ${task.description ? `<p class="task-description">${escapeHtml(task.description)}</p>` : ""}
        <div class="task-meta"><span class="status-pill status-${escapeHtml(task.status)}">${escapeHtml(labels[task.status] || task.status)}</span><span>Created ${escapeHtml(created)}</span></div>
      </div>
      <div class="task-actions">
        <button class="small-button" data-action="toggle" data-id="${task.id}" type="button">${task.status === "completed" ? "Reopen" : "Complete"}</button>
        <button class="small-button" data-action="edit" data-id="${task.id}" type="button">Edit</button>
        <button class="small-button delete" data-action="delete" data-id="${task.id}" type="button">Delete</button>
      </div>`;
    el.list.appendChild(card);
  }
  el.empty.classList.toggle("hidden", visible.length !== 0);
  el.list.classList.toggle("hidden", visible.length === 0);
}
async function loadTasks() {
  try { state.tasks = await api("/api/tasks"); render(); }
  catch (err) { message(`Couldn't load tasks: ${err.message}`, "error"); el.list.classList.add("hidden"); el.empty.classList.add("hidden"); }
}
function openForm(task = null) {
  state.editingId = task ? task.id : null;
  el.formTitle.textContent = task ? "Edit task" : "Create a task";
  el.save.textContent = task ? "Save changes" : "Save task";
  el.title.value = task ? task.title : "";
  el.description.value = task ? (task.description || "") : "";
  el.status.value = task ? task.status : "pending";
  el.form.classList.remove("hidden"); el.title.focus();
}
function closeForm() { el.form.classList.add("hidden"); el.form.reset(); state.editingId = null; }

el.form.addEventListener("submit", async event => {
  event.preventDefault();
  const payload = { title: el.title.value.trim(), description: el.description.value.trim(), status: el.status.value };
  if (!payload.title) return;
  try {
    if (state.editingId) {
      await api(`/api/tasks/${state.editingId}`, { method: "PUT", body: JSON.stringify(payload) });
      message("Task updated successfully.");
    } else {
      await api("/api/tasks", { method: "POST", body: JSON.stringify(payload) });
      message("Task created successfully.");
    }
    closeForm(); await loadTasks();
  } catch (err) { message(err.message, "error"); }
});
el.list.addEventListener("click", async event => {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const id = Number(button.dataset.id);
  const task = state.tasks.find(t => t.id === id);
  if (!task) return;
  try {
    if (button.dataset.action === "edit") { openForm(task); return; }
    if (button.dataset.action === "toggle") {
      const status = task.status === "completed" ? "pending" : "completed";
      await api(`/api/tasks/${id}`, { method: "PUT", body: JSON.stringify({ status }) });
      message(status === "completed" ? "Task completed." : "Task reopened.");
    } else if (button.dataset.action === "delete") {
      if (!window.confirm(`Delete "${task.title}"? This cannot be undone.`)) return;
      await api(`/api/tasks/${id}`, { method: "DELETE" }); message("Task deleted.");
    }
    await loadTasks();
  } catch (err) { message(err.message, "error"); }
});
document.querySelectorAll(".filter").forEach(button => button.addEventListener("click", () => {
  state.filter = button.dataset.filter;
  document.querySelectorAll(".filter").forEach(item => item.classList.toggle("active", item === button));
  render();
}));
document.querySelector("#show-form-button").addEventListener("click", () => openForm());
document.querySelector("#empty-add-button").addEventListener("click", () => openForm());
document.querySelector("#cancel-form-button").addEventListener("click", closeForm);
document.querySelector("#cancel-bottom-button").addEventListener("click", closeForm);
document.querySelector("#refresh-button").addEventListener("click", loadTasks);
loadTasks();
