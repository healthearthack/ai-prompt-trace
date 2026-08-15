(() => {
  "use strict";
  const seen = new Map();
  const resubmittingForms = new WeakSet();
  const replayingEditors = new WeakSet();
  let traceStatus = {connected: false, label: "[PT:…]", title: "Prompt Trace is connecting", actor: null};
  let scanScheduled = false;

  function composerElements() {
    return [...document.querySelectorAll("textarea, [contenteditable='true']")]
      .filter(element => element instanceof HTMLElement && element.offsetParent !== null && !element.matches("[aria-hidden='true'], input[type='password']"));
  }

  function updateBadges() {
    document.querySelectorAll("[data-prompt-trace-prefix]").forEach(badge => {
      badge.textContent = traceStatus.label;
      badge.title = traceStatus.title;
      badge.style.background = traceStatus.connected ? "#2a1021" : "#2a1717";
      badge.style.color = traceStatus.connected ? "#ff2da1" : "#ff9b9b";
      badge.style.borderColor = traceStatus.connected ? "rgba(255,45,161,.55)" : "rgba(255,155,155,.45)";
      badge.style.boxShadow = traceStatus.connected ? "0 0 0 2px rgba(255,45,161,.09)" : "none";
      if (badge.promptTraceComposer) {
        const requiredPadding = Math.max(badge.promptTraceOriginalPadding || 0, 22 + traceStatus.label.length * 7);
        badge.promptTraceComposer.style.paddingLeft = `${requiredPadding}px`;
      }
    });
  }

  function ensureComposerPrefix() {
    for (const composer of composerElements()) {
      if (composer.dataset.promptTracePrefixed === "true") continue;
      const container = composer.parentElement;
      if (!container) continue;
      composer.dataset.promptTracePrefixed = "true";
      if (getComputedStyle(container).position === "static") container.style.position = "relative";
      const currentPadding = Number.parseFloat(getComputedStyle(composer).paddingLeft) || 0;
      composer.style.paddingLeft = `${Math.max(currentPadding, 82)}px`;
      composer.style.boxSizing = "border-box";
      const badge = document.createElement("span");
      badge.promptTraceComposer = composer;
      badge.promptTraceOriginalPadding = currentPadding;
      badge.dataset.promptTracePrefix = "true";
      badge.setAttribute("role", "status");
      badge.setAttribute("aria-label", "Prompt Trace author signature");
      Object.assign(badge.style, {
        position: "absolute",
        left: "10px",
        top: "50%",
        transform: "translateY(-50%)",
        zIndex: "3",
        padding: "3px 6px",
        border: "1px solid rgba(128,128,128,.35)",
        borderRadius: "5px",
        font: "700 10px/1.2 ui-monospace, SFMono-Regular, Consolas, monospace",
        letterSpacing: ".03em",
        pointerEvents: "none",
        whiteSpace: "nowrap"
      });
      container.appendChild(badge);
    }
    updateBadges();
  }

  function scheduleComposerScan() {
    if (scanScheduled) return;
    scanScheduled = true;
    window.setTimeout(() => {
      scanScheduled = false;
      ensureComposerPrefix();
    }, 250);
  }

  function connectStatus() {
    ensureComposerPrefix();
    chrome.runtime.sendMessage({type: "PT_STATUS"}, response => {
      if (response?.ok) {
        const suffix = String(response.codeSignatureId || "").split(":")[1]?.slice(0, 6) || "SIGNED";
        const organization = response.organization ? ` · ${response.organization}` : "";
        traceStatus = {
          connected: true,
          label: `[PT:${response.actor}${organization}]`,
          title: `Signed as ${response.codeSignatureId} (${suffix}) · sensitive-value redaction active`,
          actor: response.actor
        };
      } else {
        traceStatus = {connected: false, label: "[PT:OFF]", title: response?.error || "Native signing host is not connected", actor: null};
      }
      updateBadges();
    });
    new MutationObserver(scheduleComposerScan).observe(document.documentElement, {childList: true, subtree: true});
  }

  function textFromComposer(form) {
    const candidates = [
      ...form.querySelectorAll("textarea, [contenteditable='true']"),
      ...document.querySelectorAll("textarea, [contenteditable='true']")
    ];
    for (const element of candidates) {
      if (element.matches("input[type='password'], [aria-hidden='true']")) continue;
      const text = ("value" in element ? element.value : element.innerText || "").trim();
      if (text) return persistAuthorshipTitle(element, text);
    }
    return "";
  }

  function authoredText(text) {
    if (!traceStatus.connected || !traceStatus.actor) return text;
    return globalThis.PromptTraceSubmission.stamp(text, traceStatus.label);
  }

  function persistAuthorshipTitle(element, text) {
    const titled = authoredText(text);
    if (titled === text) return text;

    if ("value" in element) {
      const prototype = element instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
      const setter = Object.getOwnPropertyDescriptor(prototype, "value")?.set;
      if (setter) setter.call(element, titled);
      else element.value = titled;
      element.dispatchEvent(new InputEvent("input", {bubbles: true, inputType: "insertText", data: `[PT:${traceStatus.actor}] `}));
      return titled;
    }

    // Gemini and other rich editors maintain their own model. Replacing the
    // selected editor contents through the browser editing command generates
    // the input event those models consume, unlike assigning textContent.
    element.focus();
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(element);
    selection.removeAllRanges();
    selection.addRange(range);
    const inserted = document.execCommand("insertText", false, titled);
    if (!inserted) {
      element.textContent = titled;
      element.dispatchEvent(new InputEvent("input", {bubbles: true, inputType: "insertText", data: titled}));
    }
    const caret = document.createRange();
    caret.selectNodeContents(element);
    caret.collapse(false);
    selection.removeAllRanges();
    selection.addRange(caret);
    return titled;
  }

  function submitPrompt(text) {
    if (!text || text.length > 200000) return;
    const digestKey = `${location.hostname}:${text}`;
    const previous = seen.get(digestKey) || 0;
    if (Date.now() - previous < 3000) return;
    seen.set(digestKey, Date.now());
    chrome.runtime.sendMessage({type: "PROMPT_SUBMITTED", text, source: `browser:${location.hostname}`});
  }

  document.addEventListener("submit", event => {
    if (resubmittingForms.has(event.target)) {
      resubmittingForms.delete(event.target);
      submitPrompt(textFromComposer(event.target));
      return;
    }
    const composer = event.target.querySelector("textarea, [contenteditable='true']");
    const before = composer ? ("value" in composer ? composer.value : composer.innerText || "").trim() : "";
    const text = textFromComposer(event.target);
    submitPrompt(text);
    if (composer && text !== before) {
      event.preventDefault();
      resubmittingForms.add(event.target);
      window.setTimeout(() => event.target.requestSubmit(), 60);
    }
  }, true);

  document.addEventListener("pointerdown", event => {
    const button = event.target instanceof Element ? event.target.closest("button") : null;
    if (!button?.matches("[aria-label*='send' i], [title*='send' i], [data-testid*='send' i]")) return;
    const scope = button.closest("form") || document.body;
    const text = textFromComposer(scope);
    if (text) submitPrompt(text);
  }, true);

  document.addEventListener("keydown", event => {
    if (event.key !== "Enter" || event.shiftKey || event.isComposing) return;
    const target = event.target instanceof Element ? event.target.closest("textarea, [contenteditable='true']") : null;
    if (!(target instanceof HTMLElement)) return;
    if (replayingEditors.has(target)) {
      replayingEditors.delete(target);
      return;
    }
    const form = target.closest("form") || document.body;
    const before = ("value" in target ? target.value : target.innerText || "").trim();
    const text = textFromComposer(form);
    submitPrompt(text);
    if (text === before) return;

    // React and similar editors may submit their previous internal value when
    // text is changed during the same Enter event. Cancel this event, allow
    // the input update to settle, and then use the site's own send control.
    event.preventDefault();
    event.stopImmediatePropagation();
    window.setTimeout(() => {
      const send = [...document.querySelectorAll(
        "button[aria-label*='send' i], button[title*='send' i], button[data-testid*='send' i]"
      )].find(button => button instanceof HTMLElement && button.offsetParent !== null && !button.disabled);
      if (send instanceof HTMLElement) {
        send.click();
        return;
      }
      replayingEditors.add(target);
      target.dispatchEvent(new KeyboardEvent("keydown", {
        key: "Enter", code: "Enter", bubbles: true, cancelable: true
      }));
    }, 60);
  }, true);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", connectStatus, {once: true});
  } else {
    connectStatus();
  }
})();
