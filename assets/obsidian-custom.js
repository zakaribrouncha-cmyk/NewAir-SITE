(function () {
  const discordUrl = "https://discord.gg/UyzapQ2zap";
  const tiktokUrl = "https://www.tiktok.com/@nhc0023";
  const tiktokSvg = '<svg viewBox="0 0 24 24" fill="currentColor" class="w-5 h-5" aria-hidden="true"><path d="M16.6 3c.31 2.16 1.52 3.73 3.58 4.43v3.31a7.77 7.77 0 0 1-3.55-.98v5.46c0 3.53-2.35 5.78-5.64 5.78-3.1 0-5.17-2.02-5.17-4.9 0-3.25 2.55-5.26 6.03-4.83v3.4c-1.32-.25-2.26.29-2.26 1.34 0 .86.68 1.45 1.64 1.45 1.1 0 1.82-.66 1.82-2.18V3h3.55Z"></path></svg>';
  const tcgPaths = ["/cartes", "/jeu", "/combat", "/marche", "/classement"];
  const purpleToBeige = [
    [/rgba?\(\s*139\s*,\s*92\s*,\s*246\s*(?:,\s*([^)]+))?\)/gi, "rgba(11,42,91,$1)"],
    [/rgba?\(\s*167\s*,\s*139\s*,\s*250\s*(?:,\s*([^)]+))?\)/gi, "rgba(30,79,143,$1)"],
    [/rgba?\(\s*168\s*,\s*85\s*,\s*247\s*(?:,\s*([^)]+))?\)/gi, "rgba(11,42,91,$1)"],
    [/rgba?\(\s*126\s*,\s*34\s*,\s*206\s*(?:,\s*([^)]+))?\)/gi, "rgba(7,26,61,$1)"],
    [/rgba?\(\s*124\s*,\s*58\s*,\s*237\s*(?:,\s*([^)]+))?\)/gi, "rgba(7,26,61,$1)"],
    [/rgba?\(\s*192\s*,\s*132\s*,\s*252\s*(?:,\s*([^)]+))?\)/gi, "rgba(18,58,122,$1)"],
    [/rgba?\(\s*217\s*,\s*70\s*,\s*239\s*(?:,\s*([^)]+))?\)/gi, "rgba(11,42,91,$1)"],
    [/rgba?\(\s*216\s*,\s*39\s*,\s*255\s*(?:,\s*([^)]+))?\)/gi, "rgba(11,42,91,$1)"],
    [/#8b5cf6/gi, "#0b2a5b"],
    [/#a78bfa/gi, "#1e4f8f"],
    [/#7c3aed/gi, "#071a3d"],
    [/#6d28d9/gi, "#06152f"],
    [/#9333ea/gi, "#0b2a5b"],
    [/#c084fc/gi, "#123a7a"],
    [/#d946ef/gi, "#0b2a5b"],
    [/#d216ff/gi, "#0b2a5b"],
  ];

  function beigeCssText(cssText) {
    return purpleToBeige.reduce((text, rule) => {
      return text.replace(rule[0], (match, alpha) => {
        if (!rule[1].includes("$1")) return rule[1];
        return rule[1].replace("$1", alpha || "0.65");
      });
    }, cssText);
  }

  function beigeInlineStyles(root) {
    const styled = root.querySelectorAll ? Array.from(root.querySelectorAll("[style]")) : [];
    const nodes = [root, ...styled].filter(Boolean);
    nodes.forEach((node) => {
      if (!node.getAttribute) return;
      const current = node.getAttribute("style") || "";
      const next = beigeCssText(current);
      if (next !== current) node.setAttribute("style", next);
    });
  }

  if (tcgPaths.some((path) => location.pathname === path || location.pathname === `${path}/`)) {
    location.replace("/");
    return;
  }

  function runOnce() {
    beigeInlineStyles(document.documentElement);

    document.querySelectorAll('a[href*="discord.gg"]').forEach((link) => {
      link.href = discordUrl;
    });

    const oldSocials = Array.from(document.querySelectorAll('a[href*="instagram.com"], a[href*="youtube.com"]'));
    const socialContainers = new Set(oldSocials.map((link) => link.parentElement).filter(Boolean));
    document.querySelectorAll('a[href*="discord.gg"]').forEach((link) => {
      if (link.parentElement && link.parentElement.querySelector("svg")) {
        socialContainers.add(link.parentElement);
      }
    });
    oldSocials.forEach((link) => link.remove());

    socialContainers.forEach((container) => {
      if (container.querySelector('a[href*="tiktok.com/@nhc0023"]')) return;
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

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", runOnce, { once: true });
  } else {
    runOnce();
  }
  setTimeout(runOnce, 1200);
  new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.type === "attributes") {
        beigeInlineStyles(mutation.target);
      } else {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === 1) beigeInlineStyles(node);
        });
      }
    });
  }).observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ["style"] });
})();
