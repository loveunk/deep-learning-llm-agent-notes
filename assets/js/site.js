(function () {
  "use strict";

  const navigation = document.querySelector(".section-navigation");
  const mobile = window.matchMedia("(max-width: 880px)");
  if (navigation && mobile.matches) navigation.open = false;

  const article = document.querySelector("[data-article]");
  const toc = document.querySelector("[data-toc]");
  if (!article || !toc) return;
  const headings = article.querySelectorAll("h2, h3");
  if (headings.length < 2) return;

  const list = toc.querySelector("[data-toc-list]");
  headings.forEach(function (heading, index) {
    if (!heading.id) {
      let id = "section-" + (index + 1);
      while (document.getElementById(id)) id += "-section";
      heading.id = id;
    }
    const item = document.createElement("li");
    if (heading.tagName === "H3") item.className = "toc-subheading";
    const link = document.createElement("a");
    link.href = "#" + encodeURIComponent(heading.id);
    link.textContent = heading.textContent;
    item.appendChild(link);
    list.appendChild(item);
  });
  toc.hidden = false;
})();
