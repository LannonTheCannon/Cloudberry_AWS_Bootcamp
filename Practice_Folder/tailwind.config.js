const plugin = require("tailwindcss/plugin");

module.exports = {
  content: ["./src/**/*.html"],
  theme: {
    extend: {
      boxShadow: {
        DEFAULT: "0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24)",
        thick: "0px 13px 40px rgb(0 0 0 / 30%), 0px 4px 4px rgb(0 0 0 / 20%)"
      },
      fontSize: {
        xs: "0.75rem",
        sm: "0.875rem",
        base: "1rem",
        lg: "1.125rem",
        xl: "1.25rem",
        "2xl": "1.5rem",
        "3xl": "1.875rem",
        "4xl": "2.25rem",
        "5xl": "3rem",
        "6xl": "4rem",
        "7xl": "5rem",
        "8xl": "6rem",
        "9xl": "7rem",
        "10xl": "8rem",
        "11xl": "9rem",
        "12xl": "10rem",
        "13xl": "11rem",
        "14xl": "12rem",
        "15xl": "13rem",
        "16xl": "14rem",
        "17xl": "15rem",
        "18xl": "16rem",
        "19xl": "17rem",
        "20xl": "18rem"
      },
      colors: {
        black: "#16171b",
        transparent: "transparent",
        current: "currentColor",
        // Primary
        moody: "#7c74da",
        slate: "#6860d5",
        iris: "#564ccf",
        majorelly: "#4338ca",
        gov: "#3b31b8",
        bay: "#362ca3",
        jackson: "#2e268f",
        //brave
        flamingo: "#fb542b",
        fandango: "#a3278f",
        //new dark
        smoke: "#f0f0f0",
        santa: "#a0a1b2",
        river: "#464a5d",
        bright: "#3c3e4e",
        tuna: "#313340",
        haiti: "#2c2c35",
        cinder: "#252731",
        pearl: "#1e2028",
        mirage: "#1a1c23",
        //system
        fadedred: "#ff8080",
        carnation: "#ff5c5c",
        coral: "#fe3c3b",
        herbs: "#55eba1",
        shamrock: "#38d989",
        jade: "#00c26f",
        baby: "#9cbff9",
        nation: "#5b8def",
        cryon: "#0063f7",
        grandis: "#fccc74",
        pumpikin: "#fdad41",
        carrot: "#ff8800",
        crayon: "#fdec72",
        energy: "#fcdd48",
        tangerine: "#fecc00",
        glass: "#a8eff2",
        fluor: "#72e0e7",
        ice: "#00cfde",
        plum: "#dda5e8",
        lilac: "#ab5dd9",
        heart: "#6600cc"
      },
      fontFamily: {
        sans: [
          '"Inter"',
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          '"Segoe UI"',
          "Roboto",
          '"Helvetica Neue"',
          "Arial",
          '"Noto Sans"',
          "sans-serif",
          '"Apple Color Emoji"',
          '"Segoe UI Emoji"',
          '"Segoe UI Symbol"'
        ] // Ensure fonts with spaces have " " surrounding it.
      }
    }
  },
  variants: {
    extend: {}
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/typography"),
    require("@tailwindcss/line-clamp"),
    require("@tailwindcss/aspect-ratio"),
    plugin(function ({ addVariant, e, postcss }) {
      addVariant("firefox", ({ container, separator }) => {
        const isFirefoxRule = postcss.atRule({
          name: "-moz-document",
          params: "url-prefix()"
        });
        isFirefoxRule.append(container.nodes);
        container.append(isFirefoxRule);
        isFirefoxRule.walkRules((rule) => {
          rule.selector = `.${e(`firefox${separator}${rule.selector.slice(1)}`)}`;
        });
      });
    })
  ]
};