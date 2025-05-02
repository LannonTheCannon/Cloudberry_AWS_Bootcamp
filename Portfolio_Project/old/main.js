// main.js

// Wait until DOM is loaded before running scripts
window.addEventListener('DOMContentLoaded', () => {
  // STICKY NAVBAR SHADOW
  const navbar = document.querySelector('#navbar');
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('shadow-lg', window.scrollY > 10);
  });

  // DARK MODE TOGGLE
  const toggle = document.getElementById('darkToggle');
  const root   = document.documentElement;
  if (localStorage.getItem('darkMode') === 'true') {
    root.classList.add('dark');
  }
  toggle.addEventListener('click', () => {
    const isDark = root.classList.toggle('dark');
    localStorage.setItem('darkMode', isDark);
  });

  // THREE.js HERO BACKGROUND
  (function initThree() {
    const canvas   = document.getElementById('three-bg');
    if (!canvas) return;

    const scene    = new THREE.Scene();
    const camera   = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    camera.position.z = 5;

    // Particle geometry
    const count     = 500;
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < positions.length; i++) {
      positions[i] = (Math.random() - 0.5) * 20;
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute(
      'position',
      new THREE.BufferAttribute(positions, 3)
    );

    // Particle material (white on dark bg)
    const material = new THREE.PointsMaterial({
      size: 0.05,
      color: 0xffffff,
    });

    const points = new THREE.Points(geometry, material);
    scene.add(points);

    // Respond to resize
    window.addEventListener('resize', () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    });

    // Animation loop
    function animate() {
      requestAnimationFrame(animate);
      points.rotation.y += 0.0005;
      renderer.render(scene, camera);
    }
    animate();
  })();

  // MINI-PLOT WITH PLOTLY
  if (document.getElementById('mini-plot-dataforge')) {
    Plotly.newPlot(
      'mini-plot-dataforge',
      [
        {
          x: [1, 2, 3, 4],
          y: [10, 15, 13, 17],
          type: 'scatter',
          mode: 'lines+markers',
        },
      ],
      {
        margin: { t: 0, l: 0, r: 0, b: 0 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        xaxis: { visible: false },
        yaxis: { visible: false },
      },
      { displayModeBar: false }
    );
  }

  // SPARKLINES WITH D3
  const sparkIds = ['sparkline-1', 'sparkline-2', 'sparkline-3'];
  sparkIds.forEach((id) => {
    const container = document.getElementById(id);
    if (!container) return;

    const data = [5, 8, 6, 9, 7, 10];
    const width = 200;
    const height = 40;
    const svg = d3
      .select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height);

    const x = d3.scaleLinear().domain([0, data.length - 1]).range([0, width]);
    const y = d3.scaleLinear().domain([0, d3.max(data)]).range([height, 0]);

    const line = d3
      .line()
      .x((d, i) => x(i))
      .y((d) => y(d));

    svg
      .append('path')
      .datum(data)
      .attr('d', line)
      .attr('fill', 'none')
      .attr('stroke', '#4f46e5')
      .attr('stroke-width', 2);
  });
});
