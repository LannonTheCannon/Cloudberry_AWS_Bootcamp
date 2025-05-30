document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll('.tilt-card').forEach(card => {
    card.addEventListener('mousemove', handleMove);
    card.addEventListener('mouseleave', handleLeave);
  });

  function handleMove(e) {
    const card = e.currentTarget;
    const rect = card.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width  - 0.5;
    const y = (e.clientY - rect.top)  / rect.height - 0.5;
    const tiltX =  y * 15;
    const tiltY = -x * 15;
    card.style.transform = `perspective(600px) rotateX(${tiltX}deg) rotateY(${tiltY}deg) scale3d(1.05,1.05,1.05)`;
  }

  function handleLeave(e) {
    e.currentTarget.style.transform = 'perspective(600px) rotateX(0) rotateY(0) scale3d(1,1,1)';
  }
});