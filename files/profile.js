const modal = document.getElementById('modal');
const openModalButton = document.getElementById('open-modal');
const closeModalButton = document.getElementById('close-modal');

openModalButton.addEventListener('click', () => {
  modal.classList.add('visible');
  window.scrollTo(0, 0);
  document.body.classList.add('non-scrollable');
});

closeModalButton.addEventListener('click', () => {
  modal.classList.remove('visible');
  document.body.classList.remove('non-scrollable');
});
