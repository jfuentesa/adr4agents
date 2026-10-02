document.querySelectorAll('form[data-confirm]').forEach((form) => {
  form.addEventListener('submit', (event) => {
    if (!window.confirm(form.dataset.confirm)) event.preventDefault();
  });
});

document.querySelectorAll('form[data-relation-form]').forEach((form) => {
  form.addEventListener('submit', (event) => {
    const type = form.elements.namedItem('type').value;
    if (type === 'supersedes' && !window.confirm('Save this supersedes relation? A new effective relation replaces the target ADR.')) {
      event.preventDefault();
    }
  });
});
