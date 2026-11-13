const test = require("node:test");
const assert = require("node:assert/strict");
const { rank, excerpt } = require("../assets/js/search.js");

const pages = [
  { title: "Embedding 与向量检索", url: "/llm/embeddings.html", text: "理解中文向量检索和相似度。" },
  { title: "Agent 生产化", url: "/llm/agent-production.html", text: "为 Agent 设置权限，并按任务评估工具调用。" },
  { title: "RAG 评估", url: "/llm/rag-evaluation.html", text: "评估检索召回率；也可与 Agent 工作流结合。" }
];

test("Chinese phrases match without requiring a word tokenizer", function () {
  assert.equal(rank(pages, "向量检索")[0].page.url, "/llm/embeddings.html");
});

test("all space-separated terms must be present", function () {
  assert.deepEqual(rank(pages, "Agent 权限").map(result => result.page.url), ["/llm/agent-production.html"]);
  assert.equal(rank(pages, "Agent 梯度下降").length, 0);
});

test("title matches rank ahead of incidental body mentions", function () {
  assert.equal(rank(pages, "agent")[0].page.title, "Agent 生产化");
});

test("full-width input and capitalization do not hide matching notes", function () {
  assert.equal(rank(pages, "ＡＧＥＮＴ")[0].page.title, "Agent 生产化");
});

test("empty queries return no results", function () {
  assert.deepEqual(rank(pages, "   "), []);
});

test("long excerpts retain the matching Chinese phrase and stay compact", function () {
  const text = "基础内容。".repeat(100) + "向量检索的失败案例" + "后续说明。".repeat(100);
  const result = excerpt(text, "向量检索");
  assert.ok(result.includes("向量检索的失败案例"));
  assert.ok(result.length <= 182);
});
