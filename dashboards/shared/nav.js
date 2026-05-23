(function () {
  const pages = [
    { id: "hub", label: "Hub", href: "index.html" },
    { id: "ambulance", label: "Ambulance", href: "ambulance.html" },
    { id: "guardian", label: "Guardian", href: "guardian.html" },
    { id: "er", label: "ER Command", href: "er-command.html" },
  ];

  const active = document.body.dataset.dashboard;
  const nav = document.createElement("nav");
  nav.className = "ehodr-dash-switcher";
  nav.setAttribute("aria-label", "Dashboard switcher");

  pages.forEach((page) => {
    const link = document.createElement("a");
    link.href = page.href;
    link.textContent = page.label;
    if (page.id === active) {
      link.classList.add("is-active");
      link.setAttribute("aria-current", "page");
    }
    nav.appendChild(link);
  });

  document.body.classList.add("has-dash-switcher");
  document.body.prepend(nav);

  document.querySelectorAll('a[href="#"]').forEach((link) => {
    link.addEventListener("click", (event) => event.preventDefault());
  });
})();
