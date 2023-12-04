const menuButton = document.getElementById('menu-button');
const navMobile = document.getElementById('nav-mobile');

menuButton.addEventListener('click', () => {
  navMobile.classList.toggle('visible');
});