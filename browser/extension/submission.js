(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.PromptTraceSubmission = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const STAMP_PATTERN = /^\[PT:[A-Z0-9]{1,8}(?: · [A-Z0-9]{2,12})?\]\s/;

  function hasStamp(text) {
    return STAMP_PATTERN.test(String(text || ""));
  }

  function stamp(text, label) {
    const value = String(text || "").trim();
    if (!value || !label || hasStamp(value)) return value;
    return `${label} ${value}`;
  }

  return {hasStamp, stamp};
});
