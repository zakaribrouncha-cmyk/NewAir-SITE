(function () {
  const discordUrl = "https://discord.gg/UyzapQ2zap";
  const tiktokUrl = "https://www.tiktok.com/@nhc0023";
  const whitelistKey = "newair-whitelist-candidatures";
  const adminEmail = "admin@newair.fr";
  const adminPass = "newairadmin";
  let illegalRulesCache = null;
  const tiktokSvg = '<svg viewBox="0 0 24 24" fill="currentColor" class="w-5 h-5" aria-hidden="true"><path d="M16.6 3c.31 2.16 1.52 3.73 3.58 4.43v3.31a7.77 7.77 0 0 1-3.55-.98v5.46c0 3.53-2.35 5.78-5.64 5.78-3.1 0-5.17-2.02-5.17-4.9 0-3.25 2.55-5.26 6.03-4.83v3.4c-1.32-.25-2.26.29-2.26 1.34 0 .86.68 1.45 1.64 1.45 1.1 0 1.82-.66 1.82-2.18V3h3.55Z"></path></svg>';
  const blockedPaths = ["/cartes", "/jeu", "/combat", "/marche", "/classement"];
  const colorRules = [
    [/rgba?\(\s*214\s*,\s*189\s*,\s*150\s*(?:,\s*([^)]+))?\)/gi, "rgba(11,42,91,$1)"],
    [/rgba?\(\s*234\s*,\s*220\s*,\s*200\s*(?:,\s*([^)]+))?\)/gi, "rgba(30,79,143,$1)"],
    [/rgba?\(\s*184\s*,\s*148\s*,\s*100\s*(?:,\s*([^)]+))?\)/gi, "rgba(7,26,61,$1)"],
    [/rgba?\(\s*139\s*,\s*92\s*,\s*246\s*(?:,\s*([^)]+))?\)/gi, "rgba(11,42,91,$1)"],
    [/rgba?\(\s*167\s*,\s*139\s*,\s*250\s*(?:,\s*([^)]+))?\)/gi, "rgba(30,79,143,$1)"],
    [/rgba?\(\s*217\s*,\s*70\s*,\s*239\s*(?:,\s*([^)]+))?\)/gi, "rgba(11,42,91,$1)"],
    [/#d6bd96/gi, "#0b2a5b"], [/#eadcc8/gi, "#1e4f8f"], [/#b89464/gi, "#071a3d"],
    [/#dac3a4/gi, "#123a7a"], [/#c9aa7f/gi, "#0f376f"], [/#9d784c/gi, "#06152f"],
    [/#6f5237/gi, "#041024"], [/#5c4630/gi, "#030b1b"], [/#2f241a/gi, "#020713"],
    [/#f7f0e5/gi, "#d9e9ff"], [/#fbf6ed/gi, "#d9e9ff"], [/#8b5cf6/gi, "#0b2a5b"],
    [/#a78bfa/gi, "#1e4f8f"], [/#7c3aed/gi, "#071a3d"], [/#9333ea/gi, "#0b2a5b"],
    [/#c084fc/gi, "#123a7a"], [/#d946ef/gi, "#0b2a5b"]
  ];
  const textRules = [
    [/OBSIDIAN/g, "NewAir"], [/Obsidian/g, "NewAir"], [/obsidian/g, "newair"],
    [/CITYBACK/g, "NewAir"], [/CityBack/g, "NewAir"], [/cityback/g, "newair"],
    [/email@newair\.fr|email@obsidian\.fr|email@cityback\.fr/g, "email@newair.fr"]
  ];

  function transformCss(text) {
    return colorRules.reduce((value, rule) => value.replace(rule[0], (match, alpha) => {
      if (!rule[1].includes("$1")) return rule[1];
      return rule[1].replace("$1", alpha || "0.65");
    }), text);
  }

  function transformText(text) {
    return textRules.reduce((value, rule) => value.replace(rule[0], rule[1]), text);
  }

  function walkText(root) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      const next = transformText(node.nodeValue || "");
      if (next !== node.nodeValue) node.nodeValue = next;
    });
  }

  function fixNode(root) {
    if (!root || root.nodeType !== 1) return;
    const nodes = [root, ...(root.querySelectorAll ? Array.from(root.querySelectorAll("*")) : [])];
    nodes.forEach((node) => {
      if (node.hasAttribute("style")) {
        const next = transformCss(node.getAttribute("style") || "");
        if (next !== node.getAttribute("style")) node.setAttribute("style", next);
      }
      ["href", "src", "alt", "aria-label", "placeholder", "title"].forEach((attr) => {
        if (!node.hasAttribute(attr)) return;
        let value = transformText(node.getAttribute(attr) || "");
        value = value.replace(/https:\/\/discord\.gg\/[^"'\s]+/g, discordUrl)
          .replace(/https:\/\/www\.tiktok\.com\/@[^"'\s]+/g, tiktokUrl)
          .replace(/\/assets\/obsidian-/g, "/assets/newair-")
          .replace(/\/assets\/cityback-/g, "/assets/newair-");
        if (value !== node.getAttribute(attr)) node.setAttribute(attr, value);
      });
    });
    walkText(root);
  }

  function installSocials() {
    document.querySelectorAll('a[href*="discord.gg"]').forEach((link) => { link.href = discordUrl; });
    const oldSocials = Array.from(document.querySelectorAll('a[href*="instagram.com"], a[href*="youtube.com"], a[href*="tiktok.com"]'));
    const containers = new Set(oldSocials.map((link) => link.parentElement).filter(Boolean));
    document.querySelectorAll('a[href*="discord.gg"]').forEach((link) => {
      if (link.parentElement && link.parentElement.querySelector("svg")) containers.add(link.parentElement);
    });
    oldSocials.forEach((link) => link.remove());
    containers.forEach((container) => {
      if (container.querySelector(`a[href="${tiktokUrl}"]`)) return;
      const link = document.createElement("a");
      link.href = tiktokUrl;
      link.target = "_blank";
      link.rel = "noreferrer";
      link.setAttribute("aria-label", "TikTok");
      link.className = "hover:text-white transition-colors";
      link.innerHTML = tiktokSvg;
      container.appendChild(link);
    });
  }

  function saveLocalCandidature(data) {
    const rows = JSON.parse(localStorage.getItem(whitelistKey) || "[]");
    const row = { id: `wl_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`, created_at: new Date().toISOString(), status: "pending", ...data };
    rows.unshift(row);
    localStorage.setItem(whitelistKey, JSON.stringify(rows));
    return row;
  }

  function isAdmin() {
    return sessionStorage.getItem("newair-admin") === "1";
  }

  function readCandidatures() {
    try { return JSON.parse(localStorage.getItem(whitelistKey) || "[]"); }
    catch { return []; }
  }

  function writeCandidatures(rows) {
    localStorage.setItem(whitelistKey, JSON.stringify(rows));
  }

  function escapeHtml(value) {
    return String(value || "Non renseigné").replace(/[<>&"]/g, (char) => ({
      "<": "&lt;",
      ">": "&gt;",
      "&": "&amp;",
      '"': "&quot;"
    })[char]);
  }

  function adminField(label, value) {
    return `<div class="newair-admin-label">${label}</div><pre>${escapeHtml(value)}</pre>`;
  }

  function adminDetails(row) {
    if (!row) return '<div class="newair-admin-empty">Aucune candidature sélectionnée.</div>';
    return `<div class="newair-admin-top">
      <div>
        <div class="newair-admin-label">Candidat</div>
        <h2>${escapeHtml(`${row.rp_firstname || ""} ${row.rp_lastname || ""}`.trim() || "Sans nom")}</h2>
        <p>${escapeHtml(row.email || "email non renseigné")} - ${escapeHtml(row.age || "?")} ans</p>
      </div>
      <div class="newair-admin-actions">
        <button class="newair-admin-btn" data-admin-status="accepted" data-admin-id="${escapeHtml(row.id)}">Accepter</button>
        <button class="newair-admin-btn danger" data-admin-status="rejected" data-admin-id="${escapeHtml(row.id)}">Refuser</button>
      </div>
    </div>
    ${adminField("Statut", row.status || "pending")}
    ${adminField("Discord", row.discord_tag)}
    ${adminField("Heures GTA RP", row.hours_gtarp || "Non renseigné")}
    ${adminField("Projet RP", row.rp_project)}
    ${adminField("Background", row.rp_background)}
    ${adminField("Motivations", row.motivation)}
    <div class="newair-admin-label">Signature</div>
    ${row.signature ? `<img class="newair-admin-signature" src="${row.signature}" alt="Signature">` : '<p class="newair-admin-empty">Aucune signature.</p>'}`;
  }

  function renderAdminPanel(target) {
    const rows = readCandidatures();
    const selectedId = sessionStorage.getItem("newair-admin-selected") || rows[0]?.id || "";
    const selected = rows.find((row) => row.id === selectedId) || rows[0] || null;
    if (selected) sessionStorage.setItem("newair-admin-selected", selected.id);
    target.innerHTML = `<section class="newair-admin-panel">
      <header class="newair-admin-header">
        <div>
          <span>Panneau staff</span>
          <h1>ADMIN NewAir</h1>
          <p>${rows.length} candidature(s) whitelist</p>
        </div>
        <div class="newair-admin-actions">
          <button class="newair-admin-btn danger" data-admin-logout>Déconnexion</button>
        </div>
      </header>
      <div class="newair-admin-grid">
        <aside class="newair-admin-list">
          ${rows.length ? rows.map((row) => `<button class="newair-admin-item ${selected && row.id === selected.id ? "active" : ""}" data-admin-select="${escapeHtml(row.id)}">
            <strong>${escapeHtml(`${row.rp_firstname || "Sans"} ${row.rp_lastname || "nom"}`)}</strong>
            <small>${escapeHtml(row.discord_tag || "Discord vide")} - ${new Date(row.created_at || Date.now()).toLocaleString("fr-FR")}</small>
            <em class="${escapeHtml(row.status || "pending")}">${escapeHtml(row.status || "pending")}</em>
          </button>`).join("") : '<div class="newair-admin-empty">Aucune candidature pour l’instant.</div>'}
        </aside>
        <article class="newair-admin-card">${adminDetails(selected)}</article>
      </div>
    </section>`;

    target.querySelectorAll("[data-admin-select]").forEach((button) => {
      button.addEventListener("click", () => {
        sessionStorage.setItem("newair-admin-selected", button.getAttribute("data-admin-select"));
        renderAdminPanel(target);
      });
    });
    target.querySelectorAll("[data-admin-status]").forEach((button) => {
      button.addEventListener("click", () => {
        const rows = readCandidatures();
        const row = rows.find((item) => item.id === button.getAttribute("data-admin-id"));
        if (row) {
          row.status = button.getAttribute("data-admin-status");
          row.reviewed_at = new Date().toISOString();
          writeCandidatures(rows);
          renderAdminPanel(target);
        }
      });
    });
    const logout = target.querySelector("[data-admin-logout]");
    if (logout) logout.addEventListener("click", () => {
      sessionStorage.removeItem("newair-admin");
      location.href = "/login/";
    });
  }

  function addAdminNav() {
    document.querySelectorAll('a[href="/compte"], a[href="/compte/"]').forEach((link) => {
      if (!isAdmin()) {
        link.setAttribute("href", "/login/");
        return;
      }
      link.textContent = "COMPTE";
      const parent = link.closest("li") || link.parentElement;
      if (!parent || parent.parentElement?.querySelector("[data-newair-admin-nav]")) return;
      const wrapper = parent.tagName === "LI" ? document.createElement("li") : document.createElement("div");
      wrapper.setAttribute("data-newair-admin-nav", "1");
      wrapper.innerHTML = '<a href="/compte/?admin=1" class="text-[11px] xl:text-xs font-bold tracking-[0.25em] xl:tracking-[0.3em] whitespace-nowrap transition-colors text-white/70 hover:text-white">ADMIN</a>';
      parent.insertAdjacentElement("afterend", wrapper);
    });
  }

  function enhanceLogin() {
    if (!location.pathname.startsWith("/login")) return;
    const emailInput = document.querySelector('input[type="email"], input[placeholder*="email" i]');
    const passInput = document.querySelector('input[type="password"]');
    const form = emailInput?.closest("form") || passInput?.closest("form");
    if (!emailInput || !passInput || !form || form.dataset.newairAdminLogin === "1") return;
    form.dataset.newairAdminLogin = "1";
    emailInput.setAttribute("placeholder", adminEmail);
    passInput.setAttribute("placeholder", adminPass);
    const helper = document.createElement("div");
    helper.className = "newair-admin-login-helper";
    helper.innerHTML = `<strong>Accès admin</strong><span>${adminEmail} / ${adminPass}</span>`;
    form.insertAdjacentElement("beforebegin", helper);
    if (!emailInput.value) emailInput.value = adminEmail;
    if (!passInput.value) passInput.value = adminPass;
    emailInput.dispatchEvent(new Event("input", { bubbles: true }));
    passInput.dispatchEvent(new Event("input", { bubbles: true }));
    form.addEventListener("submit", (event) => {
      if (emailInput.value.trim().toLowerCase() === adminEmail && passInput.value === adminPass) {
        event.preventDefault();
        event.stopImmediatePropagation();
        sessionStorage.setItem("newair-admin", "1");
        location.href = "/compte/?admin=1";
      }
    }, true);
  }

  function enhanceCompte() {
    if (!location.pathname.startsWith("/compte")) return;
    if (!isAdmin()) {
      location.replace("/login/");
      return;
    }
    const main = document.querySelector("main");
    if (!main || main.dataset.newairAdminPanel === "1") return;
    main.dataset.newairAdminPanel = "1";
    renderAdminPanel(main);
  }

  function parseIllegalRules(text) {
    const lines = text.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
    const rules = [];
    let section = "Général";
    for (let index = 0; index < lines.length; index += 1) {
      const line = lines[index];
      if (/^(?:[A-Z]{1,3}-[A-Za-z0-9]+|R-[A-Za-z0-9]+)$/.test(line)) {
        const code = line;
        const body = lines[index + 1] || "";
        const sanction = lines[index + 2] || "";
        rules.push({ section, code, body, sanction });
        index += 2;
      } else {
        section = line;
      }
    }
    return rules;
  }

  function renderIllegalRules(rules) {
    const sections = [...new Set(rules.map((rule) => rule.section))];
    return `<section class="newair-illegal-rules">
      <div class="newair-illegal-head">
        <span>Règlement illégal</span>
        <h2>ILLÉGAL</h2>
        <p>${rules.length} règles organisées par catégorie.</p>
      </div>
      ${sections.map((section) => `<div class="newair-illegal-section">
        <h3>${escapeHtml(section)}</h3>
        <div class="newair-illegal-grid">
          ${rules.filter((rule) => rule.section === section).map((rule) => `<article class="newair-rule-card">
            <div class="newair-rule-code">${escapeHtml(rule.code)}</div>
            <p>${escapeHtml(rule.body)}</p>
            <strong>${escapeHtml(rule.sanction)}</strong>
          </article>`).join("")}
        </div>
      </div>`).join("")}
    </section>`;
  }

  async function loadIllegalRules() {
    if (illegalRulesCache) return illegalRulesCache;
    const response = await fetch("/assets/newair-illegal-rules.txt", { cache: "no-store" });
    illegalRulesCache = parseIllegalRules(await response.text());
    return illegalRulesCache;
  }

  function findReglementContent() {
    const main = document.querySelector("main");
    if (!main) return null;
    const buttons = Array.from(main.querySelectorAll("button"));
    const illegalButton = buttons.find((button) => /règlement illégal/i.test(button.textContent || ""));
    if (!illegalButton) return null;
    return { main, illegalButton };
  }

  async function showIllegalRules() {
    const found = findReglementContent();
    if (!found) return;
    const { main, illegalButton } = found;
    const rules = await loadIllegalRules();
    const contentBlocks = Array.from(main.querySelectorAll("section > div, section article, section .space-y-4, section .space-y-6"));
    const existing = main.querySelector(".newair-illegal-rules");
    if (existing) existing.remove();
    const wrapper = document.createElement("div");
    wrapper.innerHTML = renderIllegalRules(rules);
    const section = main.querySelector("section");
    const host = section?.querySelector(".max-w-6xl, .max-w-7xl") || section || main;
    const tabBar = illegalButton.closest(".grid") || illegalButton.parentElement;
    const oldDynamic = Array.from(host.children).filter((child) => child !== tabBar && !child.contains(tabBar) && !child.matches(":first-child"));
    oldDynamic.forEach((child) => {
      if (!child.querySelector?.("button") && child.textContent.length > 40) child.style.display = "none";
    });
    host.appendChild(wrapper.firstElementChild);
  }

  function enhanceReglement() {
    if (!location.pathname.startsWith("/reglement")) return;
    const found = findReglementContent();
    if (!found || found.illegalButton.dataset.newairIllegal === "1") return;
    found.illegalButton.dataset.newairIllegal = "1";
    found.illegalButton.addEventListener("click", () => {
      setTimeout(showIllegalRules, 50);
    });
    if (/illegal|illégal/i.test(location.hash)) showIllegalRules();
  }

  function installFormSafety() {
    document.querySelectorAll("form").forEach((form) => {
      if (form.dataset.newairPostSafe === "1") return;
      form.dataset.newairPostSafe = "1";
      form.addEventListener("submit", (event) => {
        const action = form.getAttribute("action") || location.pathname;
        const method = (form.getAttribute("method") || "GET").toUpperCase();
        if (method !== "POST" && !location.pathname.startsWith("/whitelist")) return;
        if (!location.pathname.startsWith("/whitelist") && !/whitelist|candidature/i.test(action)) return;
        event.preventDefault();
        event.stopImmediatePropagation();
        const data = {};
        Array.from(form.elements || []).forEach((field) => {
          if (field.name) data[field.name] = field.value;
        });
        saveLocalCandidature(data);
        alert("Candidature enregistrée localement. Le staff peut la voir dans le panel admin.");
      }, true);
    });
  }

  function findCandidate(value) {
    if (!value || typeof value !== "object") return null;
    if (value.discord_tag || value.rp_firstname || value.rp_lastname || value.rp_project) return value;
    for (const key of Object.keys(value)) {
      const found = findCandidate(value[key]);
      if (found) return found;
    }
    return null;
  }

  const nativeFetch = window.fetch;
  window.fetch = async function (input, init) {
    const request = input instanceof Request ? input : null;
    const url = request ? request.url : String(input);
    const method = (init?.method || request?.method || "GET").toUpperCase();
    if (method === "POST" && url.startsWith(location.origin)) {
      try {
        const body = init?.body || (request ? await request.clone().text() : "");
        const json = typeof body === "string" && body ? JSON.parse(body) : body;
        const candidate = findCandidate(json);
        if (candidate) {
          const row = saveLocalCandidature(candidate);
          return new Response(JSON.stringify({ ok: true, id: row.id }), { status: 200, headers: { "content-type": "application/json" } });
        }
      } catch {}
    }
    return nativeFetch.apply(this, arguments);
  };

  if (blockedPaths.some((path) => location.pathname === path || location.pathname === `${path}/`)) {
    location.replace("/");
    return;
  }

  function runOnce() {
    fixNode(document.documentElement);
    installSocials();
    addAdminNav();
    enhanceLogin();
    enhanceCompte();
    enhanceReglement();
    installFormSafety();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", runOnce, { once: true });
  else runOnce();
  setInterval(runOnce, 900);
  new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.type === "attributes") fixNode(mutation.target);
      mutation.addedNodes.forEach((node) => fixNode(node));
    });
  }).observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ["style", "href", "src", "alt", "placeholder", "title", "aria-label"] });
})();
