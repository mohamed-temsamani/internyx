document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.querySelector('.search-input');
  if (searchInput && searchInput.value) {
    searchInput.focus();
    searchInput.setSelectionRange(searchInput.value.length, searchInput.value.length);
  }
});
