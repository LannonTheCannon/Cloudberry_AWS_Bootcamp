document.addEventListener("DOMContentLoaded", () => {
  const rotator = document.getElementById("rotator");
  const words   = ["workflows", "solutions", "interfaces"];
  let   i       = 0;

  const rotate = () => {
    // fade out
    rotator.classList.remove("opacity-100");
    rotator.classList.add("opacity-0");

    setTimeout(() => {
      // switch word
      rotator.textContent = words[i];
      i = (i + 1) % words.length;

      // fade in
      rotator.classList.remove("opacity-0");
      rotator.classList.add("opacity-100");
    }, 500);
  };

  // first word in
  rotator.classList.add("opacity-100");
  // rotate every 3s
  setInterval(rotate, 3000);
});
