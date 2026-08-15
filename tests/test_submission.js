const test = require("node:test");
const assert = require("node:assert/strict");
const submission = require("../browser/extension/submission.js");

test("adds the author stamp before submitted text", () => {
  assert.equal(
    submission.stamp("Review the release", "[PT:AC]"),
    "[PT:AC] Review the release"
  );
});

test("does not duplicate an existing personal or organization stamp", () => {
  assert.equal(
    submission.stamp("[PT:AC] Review the release", "[PT:AC]"),
    "[PT:AC] Review the release"
  );
  assert.equal(
    submission.stamp("[PT:AC · OPENAI] Review the release", "[PT:AC · OPENAI]"),
    "[PT:AC · OPENAI] Review the release"
  );
});

test("does not stamp empty input", () => {
  assert.equal(submission.stamp("  ", "[PT:AC]"), "");
});
