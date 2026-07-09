// PitchNote — small progressive enhancements (no framework needed).

document.addEventListener("DOMContentLoaded", () => {
  // Auto-scroll the active league pill into view on league pages.
  const active = document.querySelector(".league-pill.active");
  if (active) active.scrollIntoView({ inline: "center", block: "nearest" });

  // Submit search on Enter (native form already does this — this just
  // trims whitespace so empty queries don't navigate).
  const searchForm = document.querySelector(".search-form");
  if (searchForm) {
    searchForm.addEventListener("submit", (e) => {
      const input = searchForm.querySelector("input[name='q']");
      if (input && !input.value.trim()) e.preventDefault();
    });
  }
});
