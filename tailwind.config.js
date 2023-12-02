/** @type {import('tailwindcss').Config} */
const plugin = require('tailwindcss/plugin')

module.exports = {
	content : [
		"./templates/**/*.{html,js}",
		"./static/**/*.{html,js}",
		"**/*.{html,js}",
	],
	plugins: [
		require("daisyui"),
	],
	daisyui: {
		themes: ["dark", "dark", "dark"],
	},
	darkMode: 'class',
	variants: {
		extend: {
			backgroundColor: ['disabled'],
			textColor: ['disabled'],
		},
	},
}
