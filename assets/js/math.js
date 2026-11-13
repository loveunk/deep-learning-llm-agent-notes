(function () {
  "use strict";

  const article = document.querySelector("[data-article]");
  if (!article) return;

  // kramdown emits MathJax v2 script nodes. Expose TeX as readable text first,
  // then let MathJax v3 render it; a blocked CDN must not leave formulas empty.
  const formulas = article.querySelectorAll('script[type^="math/tex"]');
  formulas.forEach(function (source) {
    const display = source.type.includes("mode=display");
    const wrapper = document.createElement(display ? "div" : "span");
    wrapper.className = "math-source";
    wrapper.textContent = (display ? "\\[" : "\\(") + source.textContent + (display ? "\\]" : "\\)");
    source.replaceWith(wrapper);
  });

  if (!formulas.length && !/\\\(|\\\[|\$\$/.test(article.textContent)) return;
  window.MathJax = {
    tex: {
      inlineMath: [["\\(", "\\)"]],
      displayMath: [["$$", "$$"], ["\\[", "\\]"]],
      processEscapes: true
    },
    svg: { fontCache: "global" },
    options: { skipHtmlTags: ["script", "noscript", "style", "textarea", "pre", "code"] },
    startup: { elements: [article] }
  };
  const script = document.createElement("script");
  // Pin a stable version; updating the renderer should be a reviewed change.
  script.src = "https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-svg.js";
  script.async = true;
  script.id = "MathJax-script";
  document.head.appendChild(script);
})();
