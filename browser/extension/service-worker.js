chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === "PT_STATUS") {
    chrome.runtime.sendNativeMessage(
      "cloud.thepolka.prompt_trace",
      {type: "status"},
      response => sendResponse(response || {ok: false, error: chrome.runtime.lastError?.message || "Native host unavailable"})
    );
    return true;
  }
  if (message?.type !== "PROMPT_SUBMITTED" || typeof message.text !== "string") return false;
  chrome.runtime.sendNativeMessage(
    "cloud.thepolka.prompt_trace",
    {type: "record", text: message.text, source: message.source || "browser", pageOrigin: sender.origin || ""},
    response => sendResponse(response || {ok: false, error: chrome.runtime.lastError?.message || "No response"})
  );
  return true;
});
