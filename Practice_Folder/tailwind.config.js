/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/js/**/*.js"   // if you add any JS files
  ],
  theme: {
    extend: {
      colors: {
        brand: "#4f46e5", // your primary accent
        fun:   "#f472b6", // your playful secondary
      }
    }
  },
  darkMode: "class",
  plugins: []
}
