const body = document.body;
const progressBar = document.querySelector('.progress-bar');

function stretch() {
  const pixelScrolled = window.scrollY;
  const viewportHeight = window.innerHeight;
  const totalContentHeight = body.scrollHeight;

  // convert pixel to percentage
  const pixelToPerc = (pixelScrolled / (totalContentHeight - viewportHeight)) * 100;

  // set width to the progress bar
  progressBar.style.width = Math.round(pixelToPerc) + '%';
}

// scroll event
window.addEventListener('scroll', stretch);

