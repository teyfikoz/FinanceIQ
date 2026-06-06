document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-filterable='true']").forEach((table) => {
    const inputId = table.getAttribute("data-filter-input");
    const input = inputId ? document.getElementById(inputId) : null;
    if (!input) {
      return;
    }

    const rows = Array.from(table.querySelectorAll("tbody tr"));
    input.addEventListener("input", () => {
      const query = input.value.trim().toLowerCase();
      rows.forEach((row) => {
        const text = row.textContent.toLowerCase();
        row.hidden = query !== "" && !text.includes(query);
      });
    });
  });
});
