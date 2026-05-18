gsap.set(".rotating-image", { rotationY: -180 });

gsap.to(".rotating-image", {
  scrollTrigger: {
    trigger: ".rotating-image",
    start: "top center",
    end: "bottom center",
    scrub: true, // Controls the smoothness of the scroll-triggered animation
  },
  rotationY: 180, // Rotates the image 180 degrees
  ease: "none", // Ensures smooth continuous rotation without easing
});

// Parallax scrolling effect
document.addEventListener("scroll", function () {
  const elements = document.querySelectorAll(".split-text");
  const scrollY = window.scrollY;

  elements.forEach((el) => {
    const speed = el.getAttribute("data-speed");
    const offset = Math.min(scrollY * speed, 50 * speed); // Limit to 100px of scroll
    el.style.transform = `translateY(${offset}px)`;
  });
});
