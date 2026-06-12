const API_BASE = window.location.protocol.startsWith("http")
  ? window.location.origin
  : "http://localhost:8000";

const CLINICAL_OPTIONS = [
  { value: "Température", label: "Température" },
  { value: "Tension", label: "Tension (PA)" },
  { value: "Fréquence Cardiaque", label: "Fréq. cardiaque" },
  { value: "Saturation O2", label: "Sat. O2" },
  { value: "Glycémie", label: "Glycémie" },
  { value: "Douleur", label: "Niveau douleur" },
  { value: "Autre", label: "Autre" },
];

const WELCOME_HTML = `
  <div class="welcome" id="welcome-screen">
    <div class="welcome__icon" aria-hidden="true">
      <svg viewBox="0 0 48 48" fill="none">
        <circle cx="24" cy="24" r="22" stroke="currentColor" stroke-width="1.5" opacity="0.2"/>
        <path d="M24 14v20M14 24h20" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
      </svg>
    </div>
    <h2 class="welcome__title">Bonjour, Collègue</h2>
    <p class="welcome__text">
      Je suis votre assistant clinique intelligent. Décrivez vos observations ou
      structurez les données patient avec les champs cliniques.
    </p>
    <div class="quick-prompts" id="quick-prompts">
      <button type="button" class="quick-prompt" data-prompt="Quels sont les signes d'alerte d'une déshydratation ?">
        Signes de déshydratation
      </button>
      <button type="button" class="quick-prompt" data-prompt="Comment interpréter une tension artérielle élevée ?">
        Interpréter la tension
      </button>
      <button type="button" class="quick-prompt" data-prompt="Quelles sont les contre-indications de l'ibuprofène ?">
        Contre-indications ibuprofène
      </button>
    </div>
  </div>
`;

const state = {
  isLoading: false,
  hasMessages: false,
  activeConversationId: null,
};

const els = {};

document.addEventListener("DOMContentLoaded", init);

function init() {
  cacheElements();
  bindEvents();
  checkConnection();
  loadHistory();
  autoResizeTextarea();
  els.userInput.focus();
}

function cacheElements() {
  els.chatForm = document.getElementById("chat-form");
  els.userInput = document.getElementById("user-input");
  els.chatMessages = document.getElementById("chat-messages");
  els.sendBtn = document.getElementById("send-btn");
  els.clearChatBtn = document.getElementById("clear-chat");
  els.addFieldBtn = document.getElementById("add-field-btn");
  els.clearFieldsBtn = document.getElementById("clear-fields-btn");
  els.dynamicFields = document.getElementById("dynamic-fields");
  els.historyList = document.getElementById("history-list");
  els.historyEmpty = document.getElementById("history-empty");
  els.newChatBtn = document.getElementById("new-chat-btn");
  els.connectionStatus = document.getElementById("connection-status");
  els.sidebar = document.getElementById("sidebar");
  els.sidebarOverlay = document.getElementById("sidebar-overlay");
  els.toggleSidebar = document.getElementById("toggle-sidebar");
  els.toastContainer = document.getElementById("toast-container");
}

function bindEvents() {
  els.chatForm.addEventListener("submit", handleSendMessage);
  els.userInput.addEventListener("input", onInputChange);
  els.userInput.addEventListener("keydown", onInputKeydown);
  els.addFieldBtn.addEventListener("click", addClinicalField);
  els.clearFieldsBtn.addEventListener("click", clearClinicalFields);
  els.clearChatBtn.addEventListener("click", clearChat);
  els.newChatBtn.addEventListener("click", startNewChat);
  els.toggleSidebar?.addEventListener("click", openSidebar);
  els.sidebarOverlay.addEventListener("click", closeSidebar);

  els.chatMessages.addEventListener("click", (e) => {
    const prompt = e.target.closest(".quick-prompt");
    if (prompt) {
      els.userInput.value = prompt.dataset.prompt;
      onInputChange();
      els.userInput.focus();
    }
  });
}

function onInputChange() {
  autoResizeTextarea();
  updateSendButton();
}

function onInputKeydown(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    if (!state.isLoading && !els.sendBtn.disabled) {
      els.chatForm.requestSubmit();
    }
  }
}

function updateSendButton() {
  const hasText = els.userInput.value.trim().length > 0;
  const hasClinical = collectClinicalData().length > 0;
  els.sendBtn.disabled = state.isLoading || (!hasText && !hasClinical);
}

function autoResizeTextarea() {
  const ta = els.userInput;
  ta.style.height = "auto";
  ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`;
}

async function checkConnection() {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);
  try {
    const res = await fetch(`${API_BASE}/api/`, { signal: controller.signal });
    setConnectionStatus(res.ok);
  } catch {
    setConnectionStatus(false);
  } finally {
    clearTimeout(timeout);
  }
}

function setConnectionStatus(online) {
  els.connectionStatus.classList.toggle("is-online", online);
  els.connectionStatus.classList.toggle("is-offline", !online);
  els.connectionStatus.querySelector(".connection-status__text").textContent =
    online ? "Serveur connecté" : "Serveur hors ligne";
}

async function loadHistory() {
  try {
    const res = await fetch(`${API_BASE}/api/chat/history`);
    if (!res.ok) return;

    const data = await res.json();
    renderHistory(data.items || []);
  } catch {
    /* historique optionnel */
  }
}

function renderHistory(items) {
  els.historyList
    .querySelectorAll(".history-item")
    .forEach((el) => el.remove());

  if (!items.length) {
    els.historyEmpty.classList.remove("hidden");
    return;
  }

  els.historyEmpty.classList.add("hidden");

  items.forEach((item, index) => {
    const el = document.createElement("button");
    el.type = "button";
    el.className = "history-item";
    el.style.animationDelay = `${index * 40}ms`;
    el.dataset.id = item.id;
    el.setAttribute("role", "listitem");

    const previewSource =
      item.title || item.items?.[0]?.message || "Conversation";
    const preview = truncate(previewSource.replace(/\n/g, " "), 52);
    const date = formatDate(item.updated_at || item.created_at);
    const countLabel =
      item.count > 1 ? `${item.count} échanges` : `${item.count} échange`;

    el.innerHTML = `
      <span class="history-item__preview">${escapeHtml(preview)}</span>
      <span class="history-item__meta">${escapeHtml(countLabel)}</span>
      <span class="history-item__date">${escapeHtml(date)}</span>
    `;

    el.addEventListener("click", () => loadHistoryItem(item, el));
    els.historyList.appendChild(el);
  });

  if (state.activeConversationId !== null) {
    const active = els.historyList.querySelector(
      `.history-item[data-id="${state.activeConversationId}"]`,
    );
    active?.classList.add("is-active");
  }
}

function loadHistoryItem(item, el) {
  els.historyList
    .querySelectorAll(".history-item")
    .forEach((h) => h.classList.remove("is-active"));
  el.classList.add("is-active");
  state.activeConversationId = item.id;

  clearMessages();
  item.items.forEach((turn) => {
    addMessage(turn.message, "user", new Date(turn.created_at));
    addMessage(turn.response, "assistant", new Date(turn.created_at));
  });
  closeSidebar();
}

function startNewChat() {
  state.activeConversationId = null;
  els.historyList
    .querySelectorAll(".history-item")
    .forEach((h) => h.classList.remove("is-active"));
  clearMessages();
  closeSidebar();
  els.userInput.focus();
  showToast("Nouvelle conversation", "success");
}

function clearChat() {
  if (!state.hasMessages) return;
  startNewChat();
}

function clearMessages() {
  els.chatMessages.innerHTML = WELCOME_HTML;
  state.hasMessages = false;
}

function addClinicalField() {
  const field = document.createElement("div");
  field.className = "clinical-field";

  const options = CLINICAL_OPTIONS.map(
    (opt) => `<option value="${opt.value}">${opt.label}</option>`,
  ).join("");

  field.innerHTML = `
    <select class="clinical-field__select" aria-label="Type de mesure">${options}</select>
    <input type="text" class="clinical-field__value" placeholder="Valeur" aria-label="Valeur">
    <button type="button" class="clinical-field__remove" aria-label="Supprimer">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M18 6L6 18M6 6l12 12" stroke-linecap="round"/>
      </svg>
    </button>
  `;

  field
    .querySelector(".clinical-field__remove")
    .addEventListener("click", () => {
      field.remove();
      updateSendButton();
    });

  field
    .querySelector(".clinical-field__value")
    .addEventListener("input", updateSendButton);

  els.dynamicFields.appendChild(field);
  field.querySelector("input").focus();
  updateSendButton();
}

function clearClinicalFields() {
  els.dynamicFields.innerHTML = "";
  updateSendButton();
}

function collectClinicalData() {
  const lines = [];
  els.dynamicFields.querySelectorAll(".clinical-field").forEach((field) => {
    const type = field.querySelector("select").value;
    const value = field.querySelector("input").value.trim();
    if (value) lines.push({ type, value });
  });
  return lines;
}

function formatDisplayMessage(userText, clinicalLines) {
  if (!clinicalLines.length) return userText;

  const clinicalHtml = clinicalLines
    .map(({ type, value }) => `${escapeHtml(type)} : ${escapeHtml(value)}`)
    .join("<br>");

  const textPart = userText ? `<p>${formatText(userText)}</p>` : "";
  return `${textPart}<div class="clinical-block"><strong>Données cliniques</strong><br>${clinicalHtml}</div>`;
}

function buildApiPrompt(userText, clinicalLines) {
  if (!clinicalLines.length) return userText;

  const summary = clinicalLines
    .map(({ type, value }) => `- ${type}: ${value}`)
    .join("\n");
  return `DONNÉES CLINIQUES DU PATIENT :\n${summary}\nOBSERVATION COMPLÉMENTAIRE :\n${userText || "Aucune"}`;
}

async function handleSendMessage(e) {
  e.preventDefault();

  const clinicalLines = collectClinicalData();
  const userText = els.userInput.value.trim();

  if (!clinicalLines.length && !userText) return;

  removeWelcome();
  hideTypingIndicator();

  const displayHtml = formatDisplayMessage(userText, clinicalLines);
  addMessage(displayHtml, "user", new Date(), true);

  const apiPrompt = buildApiPrompt(userText, clinicalLines);

  els.userInput.value = "";
  els.userInput.style.height = "auto";
  els.dynamicFields.innerHTML = "";

  setLoading(true);
  showTypingIndicator();

  try {
    const response = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: apiPrompt,
        conversation_id: state.activeConversationId,
      }),
    });

    if (!response.ok) throw new Error("Erreur API");

    const data = await response.json();
    state.activeConversationId =
      data.conversation_id ?? state.activeConversationId;
    hideTypingIndicator();
    addMessage(data.response, "assistant");
    setConnectionStatus(true);
    loadHistory();
  } catch (error) {
    console.error("Erreur:", error);
    hideTypingIndicator();
    addMessage(
      "Une erreur est survenue. Vérifiez que le serveur FastAPI est démarré et qu'Ollama est accessible.",
      "assistant",
    );
    setConnectionStatus(false);
    showToast("Échec de l'envoi du message", "error");
  } finally {
    setLoading(false);
    updateSendButton();
    els.userInput.focus();
  }
}

function setLoading(loading) {
  state.isLoading = loading;
  els.sendBtn.disabled = loading;
  els.sendBtn.querySelector(".icon-send").classList.toggle("hidden", loading);
  els.sendBtn
    .querySelector(".icon-loading")
    .classList.toggle("hidden", !loading);
  els.userInput.disabled = loading;
}

function removeWelcome() {
  const welcome = document.getElementById("welcome-screen");
  if (welcome) welcome.remove();
  state.hasMessages = true;
}

function addMessage(text, sender, date = new Date(), isHtml = false) {
  removeWelcome();

  const message = document.createElement("article");
  message.className = `message message--${sender}`;

  const timeStr = formatTime(date);
  const avatarLabel = sender === "assistant" ? "AI" : "Vous";
  const avatarContent =
    sender === "assistant"
      ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="16" height="16"><rect x="4" y="8" width="16" height="12" rx="2"/><circle cx="9" cy="13" r="1" fill="currentColor"/><circle cx="15" cy="13" r="1" fill="currentColor"/></svg>`
      : avatarLabel.charAt(0);

  const content = isHtml ? text : formatText(text);

  message.innerHTML = `
    <div class="message__avatar" aria-hidden="true">${avatarContent}</div>
    <div class="message__body">
      <div class="message__content">${content}</div>
      <time class="message__time" datetime="${date.toISOString()}">${timeStr}</time>
    </div>
  `;

  els.chatMessages.appendChild(message);
  scrollToBottom();
}

function showTypingIndicator() {
  hideTypingIndicator();

  const typing = document.createElement("div");
  typing.className = "typing-bubble";
  typing.id = "typing-indicator";
  typing.innerHTML = `
    <div class="message__avatar" aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="16" height="16">
        <rect x="4" y="8" width="16" height="12" rx="2"/>
        <circle cx="9" cy="13" r="1" fill="currentColor"/>
        <circle cx="15" cy="13" r="1" fill="currentColor"/>
      </svg>
    </div>
    <div class="typing-bubble__content" aria-label="L'assistant rédige une réponse">
      <span></span><span></span><span></span>
    </div>
  `;

  els.chatMessages.appendChild(typing);
  scrollToBottom();
}

function hideTypingIndicator() {
  document.getElementById("typing-indicator")?.remove();
}

function scrollToBottom() {
  requestAnimationFrame(() => {
    els.chatMessages.scrollTo({
      top: els.chatMessages.scrollHeight,
      behavior: "smooth",
    });
  });
}

function openSidebar() {
  els.sidebar.classList.add("is-open");
  els.sidebarOverlay.classList.add("is-visible");
  els.sidebarOverlay.setAttribute("aria-hidden", "false");
}

function closeSidebar() {
  els.sidebar.classList.remove("is-open");
  els.sidebarOverlay.classList.remove("is-visible");
  els.sidebarOverlay.setAttribute("aria-hidden", "true");
}

function showToast(message, type = "default") {
  const toast = document.createElement("div");
  toast.className = `toast${type !== "default" ? ` toast--${type}` : ""}`;
  toast.textContent = message;
  els.toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.classList.add("is-leaving");
    toast.addEventListener("animationend", () => toast.remove());
  }, 3000);
}

function formatText(text) {
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br>");
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function formatTime(date) {
  return date.toLocaleTimeString("fr-FR", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDate(iso) {
  const date = new Date(iso);
  const now = new Date();
  const diff = now - date;

  if (diff < 86400000 && date.getDate() === now.getDate()) {
    return `Aujourd'hui · ${formatTime(date)}`;
  }
  if (diff < 172800000) {
    return `Hier · ${formatTime(date)}`;
  }
  return date.toLocaleDateString("fr-FR", { day: "numeric", month: "short" });
}

function truncate(str, max) {
  return str.length > max ? `${str.slice(0, max)}…` : str;
}
