document.addEventListener("DOMContentLoaded", () => {
  const counters = document.querySelectorAll(".counter");
  const speed = 200; // lower = faster

  counters.forEach(counter => {
    const animate = () => {
      const target = +counter.getAttribute("data-target");
      const count = +counter.innerText;
      const increment = Math.ceil(target / speed);

      if (count < target) {
        counter.innerText = count + increment;
        requestAnimationFrame(animate);
      } else {
        counter.innerText = target;
      }
    };

    // only start when the counter scrolls into view
    const observer = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) {
        animate();
        observer.disconnect();
      }
    }, { threshold: 0.6 });

    observer.observe(counter);
  });
});
