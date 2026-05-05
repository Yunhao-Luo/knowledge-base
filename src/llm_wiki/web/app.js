const state = {
  wikiFiles: [],
  rawFiles: [],
  pendingSources: [],
  filter: "",
  tabs: [],
  activeTabId: null,
  nextTabId: 1,
  activeFile: null,
  activeTool: null,
  collapsedGroups: {},
  collapsedSections: {},
  navigationError: "",
};

const SPECIAL_WIKI_FILES = new Set(["index.md", "overview.md", "log.md"]);
const SIDEBAR_WIDTH_KEY = "llm-wiki-sidebar-width";
const TOOL_LABELS = {
  query: "Query",
  ingest: "Ingest",
  lint: "Lint",
};

const els = {
  appShell: document.querySelector(".app-shell"),
  statusCards: document.getElementById("status-cards"),
  panelResizer: document.getElementById("panel-resizer"),
  wikiFiles: document.getElementById("wiki-files"),
  rawFiles: document.getElementById("raw-files"),
  toggleWikiSection: document.getElementById("toggle-wiki-section"),
  toggleRawSection: document.getElementById("toggle-raw-section"),
  openIndexLink: document.getElementById("open-index-link"),
  openOverviewLink: document.getElementById("open-overview-link"),
  openLogLink: document.getElementById("open-log-link"),
  fileFilter: document.getElementById("file-filter"),
  tabStrip: document.getElementById("tab-strip"),
  viewerTitle: document.getElementById("viewer-title"),
  viewerMeta: document.getElementById("viewer-meta"),
  renderedView: document.getElementById("rendered-view"),
  openQueryTool: document.getElementById("open-query-tool"),
  openIngestTool: document.getElementById("open-ingest-tool"),
  openLintTool: document.getElementById("open-lint-tool"),
  refreshData: document.getElementById("refresh-data"),
  ingestAllTop: document.getElementById("ingest-all-top"),
};

document.addEventListener("DOMContentLoaded", () => {
  applyStoredSidebarWidth();
  bindEvents();
  loadBootstrap();
});

function bindEvents() {
  els.fileFilter.addEventListener("input", (event) => {
    state.filter = event.target.value.toLowerCase();
    renderFileLists();
  });
  els.toggleWikiSection.addEventListener("click", () => toggleSection("wiki"));
  els.toggleRawSection.addEventListener("click", () => toggleSection("raw"));
  els.openIndexLink.addEventListener("click", () => openFile("wiki", "index.md"));
  els.openOverviewLink.addEventListener("click", () => openFile("wiki", "overview.md"));
  els.openLogLink.addEventListener("click", () => openFile("wiki", "log.md"));
  els.openQueryTool.addEventListener("click", () => openToolTab("query"));
  els.openIngestTool.addEventListener("click", () => openToolTab("ingest"));
  els.openLintTool.addEventListener("click", () => openToolTab("lint"));
  els.refreshData.addEventListener("click", loadBootstrap);
  els.ingestAllTop.addEventListener("click", () => {
    runIngest(true);
  });
  els.panelResizer.addEventListener("pointerdown", startSidebarResize);
  document.body.addEventListener("click", (event) => {
    const link = event.target.closest(".internal-link");
    if (!link) return;
    event.preventDefault();
    openFile(link.dataset.scope, link.dataset.path);
  });
}

async function loadBootstrap() {
  try {
    const data = await fetchJson("/api/bootstrap");
    state.wikiFiles = data.wikiFiles;
    state.rawFiles = data.rawFiles;
    state.pendingSources = data.pendingSources;
    renderStatus(data.status);
    renderFileLists();
    renderPendingSources();
    if (!state.activeFile && state.wikiFiles.length) {
      openFile("wiki", "overview.md");
    }
  } catch (error) {
    renderError(error.message);
  }
}

function renderStatus(status) {
  const activeFile = state.activeFile ? `${state.activeFile.scope}: ${state.activeFile.path}` : "no file selected";
  const activeTool = state.activeTool ? `tool ${state.activeTool}` : "tool none";
  els.statusCards.dataset.providerAvailable = status.providerAvailable ? "true" : "false";
  els.statusCards.dataset.pendingSourceCount = String(status.pendingSourceCount ?? 0);
  els.statusCards.dataset.providerError = status.providerError || "";
  els.statusCards.innerHTML = `
    <div class="status-bar-left">
      <div class="dock-item">
        <span class="dock-dot ${status.providerAvailable ? "is-ready" : "is-missing"}"></span>
        <span>Provider ${status.providerAvailable ? "ready" : "missing"}</span>
      </div>
      <div class="dock-item">
        <span class="dock-dot ${status.pendingSourceCount ? "is-pending" : "is-clear"}"></span>
        <span>${status.pendingSourceCount} pending</span>
      </div>
    </div>
    <div class="status-bar-right">
      ${state.navigationError ? `<span class="status-text is-error">${escapeHtml(state.navigationError)}</span>` : ""}
      <span class="status-text">${escapeHtml(activeTool)}</span>
      <span class="status-text">${escapeHtml(activeFile)}</span>
    </div>
  `;
}

function renderFileLists() {
  renderSectionToggles();
  renderFileList(els.wikiFiles, state.wikiFiles.filter((file) => !SPECIAL_WIKI_FILES.has(file.path)), "wiki");
  renderFileList(els.rawFiles, state.rawFiles, "raw");
}

function renderFileList(container, files, scope) {
  if (state.collapsedSections[scope]) {
    container.innerHTML = "";
    container.classList.add("is-hidden");
    return;
  }
  container.classList.remove("is-hidden");
  const filter = state.filter;
  const visible = files.filter((file) => {
    const haystack = `${file.path} ${file.name}`.toLowerCase();
    return !filter || haystack.includes(filter);
  });
  const tree = buildExplorerTree(visible, scope);
  container.innerHTML = renderExplorerTree(tree, scope);
  for (const button of container.querySelectorAll(".file-item")) {
    button.addEventListener("click", () => openFile(button.dataset.scope, button.dataset.path));
  }
  for (const toggle of container.querySelectorAll("[data-toggle-group]")) {
    toggle.addEventListener("click", () => toggleExplorerGroup(toggle.dataset.toggleGroup));
  }
}

function buildExplorerTree(files, scope) {
  const root = { id: `${scope}:root`, folders: new Map(), files: [] };
  for (const file of files) {
    const parts = file.path.split("/");
    if (parts.length === 1) {
      root.files.push(file);
      continue;
    }
    let cursor = root;
    let folderPath = "";
    for (const segment of parts.slice(0, -1)) {
      folderPath = folderPath ? `${folderPath}/${segment}` : segment;
      if (!cursor.folders.has(segment)) {
        cursor.folders.set(segment, {
          id: `${scope}:${folderPath}`,
          name: segment,
          folders: new Map(),
          files: [],
        });
      }
      cursor = cursor.folders.get(segment);
    }
    cursor.files.push(file);
  }
  sortExplorerNode(root);
  return root;
}

function sortExplorerNode(node) {
  node.files.sort((a, b) => a.name.localeCompare(b.name) || a.path.localeCompare(b.path));
  const sortedFolders = Array.from(node.folders.entries()).sort(([a], [b]) => a.localeCompare(b));
  node.folders = new Map(sortedFolders);
  for (const folder of node.folders.values()) {
    sortExplorerNode(folder);
  }
}

function renderExplorerTree(tree, scope, depth = 0) {
  const folders = Array.from(tree.folders.values())
    .map((folder) => renderExplorerFolder(folder, scope, depth))
    .join("");
  const files = tree.files.map((file) => renderExplorerFile(file, scope, depth)).join("");
  return folders + files;
}

function renderExplorerFolder(folder, scope, depth) {
  const collapsed = Boolean(state.collapsedGroups[folder.id]);
  return `
    <section class="explorer-group depth-${depth}">
      <button class="explorer-label ${collapsed ? "is-collapsed" : ""}" data-toggle-group="${escapeHtml(folder.id)}">
        <span class="explorer-caret">${collapsed ? "▸" : "▾"}</span>
        <span>${escapeHtml(folder.name)}</span>
      </button>
      <div class="explorer-children ${collapsed ? "is-hidden" : ""}">
        ${renderExplorerTree(folder, scope, depth + 1)}
      </div>
    </section>
  `;
}

function renderExplorerFile(file, scope, depth) {
  return `
    <button class="file-item depth-${depth} ${state.activeFile?.path === file.path && state.activeFile?.scope === scope ? "active" : ""}"
      data-scope="${scope}" data-path="${file.path}" title="${escapeHtml(file.path)}">
      <strong>${escapeHtml(file.name)}</strong>
    </button>
  `;
}

function renderPendingSources() {
  const activeTab = state.tabs.find((tab) => tab.id === state.activeTabId);
  if (activeTab?.type === "tool" && activeTab.kind === "ingest") {
    renderActiveTab();
  }
}

function toggleExplorerGroup(groupId) {
  state.collapsedGroups[groupId] = !state.collapsedGroups[groupId];
  renderFileLists();
}

function toggleSection(scope) {
  state.collapsedSections[scope] = !state.collapsedSections[scope];
  renderFileLists();
}

function renderSectionToggles() {
  syncSectionToggle(els.toggleWikiSection, "wiki");
  syncSectionToggle(els.toggleRawSection, "raw");
}

function syncSectionToggle(button, scope) {
  const collapsed = Boolean(state.collapsedSections[scope]);
  button.classList.toggle("is-collapsed", collapsed);
  const caret = button.querySelector(".explorer-caret");
  if (caret) caret.textContent = collapsed ? "▸" : "▾";
}

function applyStoredSidebarWidth() {
  const stored = Number(window.localStorage.getItem(SIDEBAR_WIDTH_KEY) || "");
  if (!Number.isFinite(stored) || stored <= 0) return;
  setSidebarWidth(stored);
}

function startSidebarResize(event) {
  event.preventDefault();
  document.body.classList.add("is-resizing");
  els.panelResizer.setPointerCapture?.(event.pointerId);
  const handleMove = (moveEvent) => {
    setSidebarWidth(moveEvent.clientX);
  };
  const handleUp = () => {
    document.body.classList.remove("is-resizing");
    window.removeEventListener("pointermove", handleMove);
    window.removeEventListener("pointerup", handleUp);
    window.localStorage.setItem(
      SIDEBAR_WIDTH_KEY,
      String(parseInt(getComputedStyle(document.documentElement).getPropertyValue("--sidebar-width"), 10))
    );
  };
  window.addEventListener("pointermove", handleMove);
  window.addEventListener("pointerup", handleUp);
}

function setSidebarWidth(rawWidth) {
  const minWidth = 220;
  const maxWidth = Math.min(window.innerWidth * 0.6, 560);
  const width = Math.max(minWidth, Math.min(maxWidth, rawWidth));
  document.documentElement.style.setProperty("--sidebar-width", `${Math.round(width)}px`);
}

async function openFile(scope, path) {
  try {
    const data = await fetchJson(`/api/file?scope=${encodeURIComponent(scope)}&path=${encodeURIComponent(path)}`);
    upsertFileTab({
      scope: data.scope || scope,
      path: data.path || path,
      title: fileTabTitle(data.path || path),
      meta: data.scope || scope,
      html: data.html || `<pre>${escapeHtml(data.markdown)}</pre>`,
    });
    state.navigationError = "";
  } catch (error) {
    state.navigationError = `open failed: ${scope}:${path}`;
    renderStatusFromCurrentState();
    openResultTab({
      kind: "error",
      title: "Open Error",
      meta: `${scope}:${path}`,
      html: `<div class="error-banner">${escapeHtml(error.message)}</div>`,
    });
  }
}

async function runQuery() {
  const toolTab = getActiveToolTab("query");
  const question = (toolTab?.question || "").trim();
  if (!question) return;
  const tabId = openResultTab({
    kind: "query",
    title: "Query",
    meta: "working",
    html: `<div class="notice">Working…</div>`,
  });
  await performAction("/api/action/query", { question }, renderQueryResult, tabId);
}

async function runIngest(all) {
  const toolTab = getActiveToolTab("ingest");
  const payload = all ? { all: true } : { source: (toolTab?.source || "").trim() };
  if (!all && !payload.source) return;
  const tabId = openResultTab({
    kind: "ingest",
    title: all ? "Ingest All" : "Ingest",
    meta: "working",
    html: `<div class="notice">Working…</div>`,
  });
  await performAction("/api/action/ingest", payload, renderIngestResult, tabId);
}

async function runLint(apply) {
  const tabId = openResultTab({
    kind: "lint",
    title: apply ? "Lint Apply" : "Lint",
    meta: "working",
    html: `<div class="notice">Working…</div>`,
  });
  await performAction("/api/action/lint", { apply }, renderLintResult, tabId);
}

async function performAction(url, payload, onSuccess, tabId) {
  try {
    const data = await fetchJson(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (data.status) renderStatus(data.status);
    if (data.pendingSources) {
      state.pendingSources = data.pendingSources;
      renderPendingSources();
    }
    updateResultTab(tabId, onSuccess(data));
    await refreshFileData();
  } catch (error) {
    updateResultTab(tabId, {
      title: "Error",
      meta: "assistant",
      html: `<div class="error-banner">${escapeHtml(error.message)}</div>`,
    });
  }
}

async function refreshFileData() {
  const [wiki, raw] = await Promise.all([
    fetchJson("/api/files?scope=wiki"),
    fetchJson("/api/files?scope=raw"),
  ]);
  state.wikiFiles = wiki.files;
  state.rawFiles = raw.files;
  renderFileLists();
}

function renderQueryResult(data) {
  return {
    title: "Query",
    meta: "assistant",
    html: `
      <div class="result-section">
        <p class="eyebrow">Query Answer</p>
        <div>${data.html}</div>
      </div>
    `,
  };
}

function renderIngestResult(data) {
  if (!data.plans.length) {
    return {
      title: "Ingest",
      meta: "assistant",
      html: `<div class="notice">No pending raw markdown files to ingest.</div>`,
    };
  }
  const html = data.plans
    .map(
      (plan) => `
        <div class="result-section">
          <p class="eyebrow">Ingested</p>
          <h3>${escapeHtml(plan.sourceSummaryPath)}</h3>
          <div class="inline-list">
            ${plan.wikiUpdates.map((update) => `<div>${escapeHtml(update.path)}</div>`).join("") || "<div>No additional wiki updates.</div>"}
          </div>
          ${plan.assistantNotes ? `<div class="notice">${escapeHtml(plan.assistantNotes)}</div>` : ""}
        </div>`
    )
    .join("");
  return {
    title: data.plans.length > 1 ? "Ingest All" : "Ingest",
    meta: `${data.plans.length} source${data.plans.length === 1 ? "" : "s"}`,
    html,
  };
}

function renderLintResult(data) {
  const report = data.report;
  return {
    title: report.wikiUpdates.length ? "Lint Apply" : "Lint",
    meta: `${report.findings.length} finding${report.findings.length === 1 ? "" : "s"}`,
    html: `
      <div class="result-section">
        <p class="eyebrow">Lint Summary</p>
        <p>${escapeHtml(report.summary)}</p>
        ${report.findings.length ? `<div class="inline-list">${report.findings.map((item) => `<div>${escapeHtml(item)}</div>`).join("")}</div>` : ""}
      </div>
      ${
        report.wikiUpdates.length
          ? `<div class="result-section">
              <p class="eyebrow">Applied Updates</p>
              <div class="inline-list">${report.wikiUpdates.map((update) => `<div>${escapeHtml(update.path)}</div>`).join("")}</div>
            </div>`
          : ""
      }
      ${
        report.suggestedPages.length
          ? `<div class="result-section">
              <p class="eyebrow">Suggested Pages</p>
              <div class="inline-list">${report.suggestedPages.map((path) => `<div>${escapeHtml(path)}</div>`).join("")}</div>
            </div>`
          : ""
      }
      ${report.assistantNotes ? `<div class="notice">${escapeHtml(report.assistantNotes)}</div>` : ""}
    `,
  };
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Request failed.");
  }
  return data;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function renderStatusFromCurrentState() {
  const providerAvailable = els.statusCards.dataset.providerAvailable === "true";
  const pendingSourceCount = Number(els.statusCards.dataset.pendingSourceCount || "0");
  const providerError = els.statusCards.dataset.providerError || "";
  syncToolButtons();
  renderStatus({ providerAvailable, pendingSourceCount, providerError });
}

function syncToolButtons() {
  els.openQueryTool.classList.toggle("active", state.activeTool === "query");
  els.openIngestTool.classList.toggle("active", state.activeTool === "ingest");
  els.openLintTool.classList.toggle("active", state.activeTool === "lint");
}

function renderError(message) {
  openResultTab({
    kind: "error",
    title: "Error",
    meta: "assistant",
    html: `<div class="error-banner">${escapeHtml(message)}</div>`,
  });
}

function fileTabTitle(path) {
  const parts = path.split("/");
  return parts[parts.length - 1].replace(/\.md$/i, "");
}

function upsertFileTab({ scope, path, title, meta, html }) {
  const existing = state.tabs.find((tab) => tab.type === "file" && tab.scope === scope && tab.path === path);
  if (existing) {
    existing.title = title;
    existing.meta = meta;
    existing.html = html;
    activateTab(existing.id);
    return existing.id;
  }
  return createTab({
    type: "file",
    scope,
    path,
    title,
    meta,
    html,
    closable: true,
  });
}

function openResultTab({ kind, title, meta, html }) {
  return createTab({
    type: "result",
    kind,
    title,
    meta,
    html,
    closable: true,
  });
}

function openToolTab(kind) {
  const existing = state.tabs.find((tab) => tab.type === "tool" && tab.kind === kind);
  if (existing) {
    activateTab(existing.id);
    return existing.id;
  }
  return createTab({
    type: "tool",
    kind,
    title: TOOL_LABELS[kind],
    meta: "assistant tool",
    question: "",
    source: "",
    closable: true,
  });
}

function getActiveToolTab(kind) {
  const activeTab = state.tabs.find((tab) => tab.id === state.activeTabId);
  if (!activeTab || activeTab.type !== "tool") return null;
  if (kind && activeTab.kind !== kind) return null;
  return activeTab;
}

function updateResultTab(tabId, patch) {
  const tab = state.tabs.find((item) => item.id === tabId);
  if (!tab) return;
  Object.assign(tab, patch);
  activateTab(tabId);
}

function createTab(tab) {
  const id = `tab-${state.nextTabId++}`;
  state.tabs.push({ id, ...tab });
  activateTab(id);
  return id;
}

function activateTab(tabId) {
  state.activeTabId = tabId;
  const activeTab = state.tabs.find((tab) => tab.id === tabId) || null;
  state.activeFile = activeTab && activeTab.type === "file" ? { scope: activeTab.scope, path: activeTab.path } : null;
  state.activeTool = activeTab && activeTab.type !== "file" ? activeTab.kind || null : null;
  renderTabs();
  renderActiveTab();
  renderStatusFromCurrentState();
  renderFileLists();
}

function closeTab(tabId) {
  const index = state.tabs.findIndex((tab) => tab.id === tabId);
  if (index === -1) return;
  const wasActive = state.activeTabId === tabId;
  state.tabs.splice(index, 1);
  if (!state.tabs.length) {
    state.activeTabId = null;
    state.activeFile = null;
    renderTabs();
    renderActiveTab();
    renderStatusFromCurrentState();
    renderFileLists();
    return;
  }
  if (wasActive) {
    const nextTab = state.tabs[Math.max(0, index - 1)] || state.tabs[0];
    activateTab(nextTab.id);
    return;
  }
  renderTabs();
  renderStatusFromCurrentState();
}

function renderTabs() {
  if (!state.tabs.length) {
    els.tabStrip.innerHTML = "";
    return;
  }
  els.tabStrip.innerHTML = state.tabs
    .map(
      (tab) => `
        <button class="tab ${tab.id === state.activeTabId ? "active" : ""}" data-tab-id="${escapeHtml(tab.id)}" title="${escapeHtml(tab.title)}">
          <span class="tab-label">${escapeHtml(tab.title)}</span>
          ${tab.closable ? `<span class="tab-close" data-close-tab="${escapeHtml(tab.id)}">×</span>` : ""}
        </button>
      `
    )
    .join("");
  for (const tabButton of els.tabStrip.querySelectorAll("[data-tab-id]")) {
    tabButton.addEventListener("click", (event) => {
      const closeTarget = event.target.closest("[data-close-tab]");
      if (closeTarget) {
        event.stopPropagation();
        closeTab(closeTarget.dataset.closeTab);
        return;
      }
      activateTab(tabButton.dataset.tabId);
    });
  }
}

function renderActiveTab() {
  const activeTab = state.tabs.find((tab) => tab.id === state.activeTabId);
  if (!activeTab) {
    els.viewerTitle.textContent = "Select a page";
    els.viewerMeta.textContent = "";
    els.renderedView.classList.add("empty-state");
    els.renderedView.innerHTML = "Choose a wiki page, raw source, or assistant action to open it here.";
    return;
  }
  els.viewerTitle.textContent = activeTab.title;
  els.viewerMeta.textContent = activeTab.meta || "";
  els.renderedView.classList.remove("empty-state");
  const renderedHtml = activeTab.type === "tool" ? renderToolTab(activeTab) : activeTab.html;
  els.renderedView.innerHTML = stripThinkingTokens(renderedHtml);
  if (activeTab.type === "tool") {
    bindToolTab(activeTab);
  }
}

function renderToolTab(tab) {
  if (tab.kind === "query") {
    return `
      <section class="tool-tab">
        <p class="eyebrow">Query</p>
        <h3>Ask the wiki a question</h3>
        <textarea class="tool-input" data-tool-field="question" placeholder="Ask the wiki a question">${escapeHtml(tab.question || "")}</textarea>
        <div class="action-row">
          <button class="primary-button" data-tool-action="run-query">Run Query</button>
        </div>
      </section>
    `;
  }
  if (tab.kind === "ingest") {
    return `
      <section class="tool-tab">
        <p class="eyebrow">Ingest</p>
        <h3>Ingest source material</h3>
        <input class="text-input tool-input" type="text" data-tool-field="source" placeholder="knowledge/raw/example.md" value="${escapeHtml(tab.source || "")}">
        <div class="action-row">
          <button class="secondary-button" data-tool-action="run-ingest">Ingest One</button>
          <button class="ghost-button" data-tool-action="run-ingest-all">Ingest All New</button>
        </div>
        <div class="pending-list">
          ${
            state.pendingSources.length
              ? state.pendingSources
                  .slice(0, 10)
                  .map(
                    (path) =>
                      `<button class="pending-pill" data-tool-pending="${escapeHtml(path)}">${escapeHtml(path)}</button>`
                  )
                  .join("")
              : `<div class="notice">No pending raw sources.</div>`
          }
        </div>
      </section>
    `;
  }
  return `
    <section class="tool-tab">
      <p class="eyebrow">Lint</p>
      <h3>Inspect or repair the wiki</h3>
      <p class="muted">Check structural health or let the assistant apply repairs directly.</p>
      <div class="action-row">
        <button class="secondary-button" data-tool-action="run-lint">Analyze</button>
        <button class="primary-button" data-tool-action="run-lint-apply">Analyze &amp; Apply</button>
      </div>
    </section>
  `;
}

function bindToolTab(tab) {
  const field = els.renderedView.querySelector("[data-tool-field]");
  if (field) {
    field.addEventListener("input", (event) => {
      tab[event.target.dataset.toolField] = event.target.value;
    });
  }
  for (const button of els.renderedView.querySelectorAll("[data-tool-action]")) {
    button.addEventListener("click", () => {
      const action = button.dataset.toolAction;
      if (action === "run-query") {
        runQuery();
      } else if (action === "run-ingest") {
        runIngest(false);
      } else if (action === "run-ingest-all") {
        runIngest(true);
      } else if (action === "run-lint") {
        runLint(false);
      } else if (action === "run-lint-apply") {
        runLint(true);
      }
    });
  }
  for (const button of els.renderedView.querySelectorAll("[data-tool-pending]")) {
    button.addEventListener("click", () => {
      tab.source = `knowledge/raw/${button.dataset.toolPending}`;
      renderActiveTab();
    });
  }
}

function stripThinkingTokens(value) {
  return String(value)
    .replace(/<\s*think\b[^>]*>[\s\S]*?(?:<\s*\/\s*think\s*>|$)/gi, "")
    .replace(/&lt;\s*think\b[\s\S]*?(?:&lt;\s*\/\s*think\s*&gt;|$)/gi, "")
    .trim();
}
