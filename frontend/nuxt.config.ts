import tailwindcss from "@tailwindcss/vite"

export default defineNuxtConfig({
	css: ["~/assets/css/tailwind.css"],
	app: {
		head: {
			script: [
				{
					src: "https://telegram.org/js/telegram-web-app.js",
					defer: false,
				},
			],
		},
	},
	vite: {
		plugins: [tailwindcss()],
	},

	compatibilityDate: "2025-07-15",
	devtools: { enabled: true },
	modules: ["shadcn-nuxt"],
	runtimeConfig: {
		public: {
			apiBase: process.env.NUXT_PUBLIC_API_BASE || "http://localhost:8000",
		},
	},
	shadcn: {
		/**
		 * Prefix for all the imported component.
		 * @default "Ui"
		 */
		prefix: "",
		/**
		 * Directory that the component lives in.
		 * Will respect the Nuxt aliases.
		 * @link https://nuxt.com/docs/api/nuxt-config#alias
		 * @default "@/components/ui"
		 */
		componentDir: "@/components/ui",
	},
})
