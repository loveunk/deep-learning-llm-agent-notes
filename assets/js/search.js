(function (root) {
  "use strict";

  function normalize(value) {
    return String(value || "").normalize("NFKC").toLocaleLowerCase("zh-CN").replace(/\s+/g, " ").trim();
  }

  function rank(pages, query) {
    const phrase = normalize(query).slice(0, 120);
    const terms = Array.from(new Set(phrase.split(/\s+/).filter(Boolean)));
    if (!terms.length) return [];
    return pages.map(function (page) {
      const title = normalize(page.title);
      const body = normalize(page.text);
      const combined = title + " " + body;
      if (!terms.every(function (term) { return combined.includes(term); })) return null;
      let score = title.includes(phrase) ? 20 : 0;
      terms.forEach(function (term) {
        if (title.includes(term)) score += 10;
        if (body.includes(term)) score += 1;
      });
      return { page: page, score: score };
    }).filter(Boolean).sort(function (a, b) {
      return b.score - a.score || a.page.title.localeCompare(b.page.title, "zh-CN");
    });
  }

  function excerpt(text, query) {
    const source = String(text || "").replace(/\s+/g, " ").trim();
    const terms = normalize(query).split(/\s+/).filter(Boolean);
    const haystack = normalize(source);
    const positions = terms.map(function (term) { return haystack.indexOf(term); }).filter(function (index) { return index >= 0; });
    const start = positions.length ? Math.max(0, Math.min.apply(null, positions) - 35) : 0;
    return (start ? "…" : "") + source.slice(start, start + 180) + (source.length > start + 180 ? "…" : "");
  }

  // The same pure functions are exercised by Node's built-in test runner.
  if (typeof module !== "undefined" && module.exports) module.exports = { normalize: normalize, rank: rank, excerpt: excerpt };
  if (!root.document) return;
  const document = root.document;
  const form = document.getElementById("site-search");
  if (!form) return;
  const input = document.getElementById("search-query");
  const status = document.getElementById("search-status");
  const results = document.getElementById("search-results");
  let indexPromise;
  let requestNumber = 0;
  let timer;

  function loadIndex() {
    if (!indexPromise) {
      indexPromise = fetch(form.dataset.indexUrl).then(function (response) {
        if (!response.ok) throw new Error("Search index unavailable");
        return response.json();
      }).then(function (pages) {
        if (!Array.isArray(pages)) throw new Error("Invalid search index");
        const decoder = document.createElement("textarea");
        return pages.filter(function (page) {
          return typeof page.title === "string" && typeof page.text === "string" && typeof page.url === "string" && page.url.startsWith("/") && !page.url.startsWith("//");
        }).map(function (page) {
          decoder.innerHTML = page.text;
          return { title: page.title, url: page.url, text: decoder.value };
        });
      }).catch(function (error) {
        indexPromise = null;
        throw error;
      });
    }
    return indexPromise;
  }

  async function search() {
    const currentRequest = ++requestNumber;
    const query = input.value.trim().slice(0, 120);
    const url = new URL(root.location.href);
    if (query) url.searchParams.set("q", query);
    else url.searchParams.delete("q");
    root.history.replaceState(null, "", url);
    results.replaceChildren();
    if (!query) {
      status.textContent = "输入关键词开始搜索。";
      return;
    }
    status.textContent = "正在加载笔记索引…";
    try {
      const pages = await loadIndex();
      if (currentRequest !== requestNumber) return;
      const matches = rank(pages, query);
      status.textContent = matches.length ? "找到 " + matches.length + " 篇笔记" + (matches.length > 20 ? "，显示前 20 篇。" : "。") : "没有找到匹配笔记。试试更短的关键词，或用空格拆开关键词。";
      matches.slice(0, 20).forEach(function (match) {
        const item = document.createElement("li");
        const heading = document.createElement("h2");
        const link = document.createElement("a");
        link.href = match.page.url;
        link.textContent = match.page.title;
        heading.appendChild(link);
        const summary = document.createElement("p");
        summary.textContent = excerpt(match.page.text, query);
        item.append(heading, summary);
        results.appendChild(item);
      });
    } catch (error) {
      if (currentRequest === requestNumber) status.textContent = "暂时无法加载搜索索引。请稍后重试，或使用页面上的学习目录。";
    }
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    clearTimeout(timer);
    search();
  });
  input.addEventListener("input", function () {
    clearTimeout(timer);
    // Invalidate pending results immediately, before the debounce expires.
    requestNumber += 1;
    timer = setTimeout(search, 180);
  });
  input.value = (new URLSearchParams(root.location.search).get("q") || "").slice(0, 120);
  if (input.value) search();
})(typeof window === "undefined" ? globalThis : window);
