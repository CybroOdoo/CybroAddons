import { registry } from "@web/core/registry";
import { useBus } from "@web/core/utils/hooks";
import { routerBus } from "@web/core/browser/router";
import { onMounted, onPatched, onWillStart, useListener } from "@odoo/owl";
/** @odoo-module **/

import { WebClient } from "@web/webclient/webclient";
import { patch } from "@web/core/utils/patch";
import InfinitoRecentApps from './recentApps';
import MenuBookmark from './MenuBookmark';
import { session } from "@web/session";



patch(WebClient.prototype, {

    setup() {
        super.setup();
        useListener(document.body, 'mousemove', this.mouseMove.bind(this));
        onWillStart(this.onWillStart);
        useBus(routerBus, "ROUTE_CHANGE", () => this._closeThemeStudioPanels());
        onMounted(() => {
            this._lastPath = location.pathname;
            // Re-run dark mode check now that .o_web_client is in the DOM.
            // onWillStart runs before the element exists so the class cannot be
            // applied there; here it is guaranteed to exist.
            document.querySelector('.o_web_client')?.classList.toggle('infinito-rtl', !!session.infinitoRtl);
            this.darkModeCheck();

        });
        onPatched(() => {
            if (this._lastPath !== location.pathname) {
                this._lastPath = location.pathname;
                this._closeThemeStudioPanels();
            }
        });
    },

    _closeThemeStudioPanels() {
        // Case 1: Counter mounted via systray gear icon — destroy the Owl App so
        // it doesn't re-render and re-insert its root element after DOM removal.
        if (window._infinitoCounterApp) {
            try { window._infinitoCounterApp.destroy(); } catch (e) {}
            window._infinitoCounterApp = null;
        }

        document.body.classList.remove('infinito-advanced-sidebar-open');
        document.body.style.removeProperty('--infinito-advanced-sidebar-width');
        const webClient = document.querySelector('.o_web_client');
        if (webClient) {
            webClient.classList.remove('infinito-advanced-sidebar-open');
            webClient.style.removeProperty('--infinito-advanced-sidebar-width');
        }

        // Case 2: EditorMenu wrapper (hamburger sidebar from editor_client_action)
        const advPanel = document.querySelector('.sidebar_simple_editor');
        if (advPanel) advPanel.remove();

        // Case 3: Preset / element-editor sidebar
        const presetSidebar = document.getElementById('theme_editor_sidebar_preset');
        if (presetSidebar) presetSidebar.remove();

        // Restore action-manager width
        const main = document.querySelector('.o_action_manager');
        if (main) main.classList.remove('infinito-sidebar-open');
    },

    async onWillStart() {
        this.fullScreenEnabled = session.fullscreen;
        this.recentApps = session.recentApps;
        this.is_dark = false;

        const webClient = document.querySelector('.o_web_client');
        if (session.infinitoRtl) {
            if (webClient) webClient.classList.add('infinito-rtl');
        } else {
            if (webClient) webClient.classList.remove('infinito-rtl');
        }

        this.last_check = new Date().getMinutes();
        this.darkModeCheck();
    },

    rerenderMenuBookmark() {
        if (this.menuBookmark && this.menuBookmark.state) {
            this.menuBookmark.state.menus = session.infinitoMenuBookmarks;
        }
    },

    mouseMove(ev) {
        if (document.querySelector('.theme_studio_toggle_sidebar')
            || document.querySelector('.marg_main')
            || document.querySelector('.main_sidebar')) {
            var Menuboook = document.getElementById("menuBookmark");
            if (Menuboook) {
                Menuboook.classList.remove('d-flex');
                Menuboook.style.display = 'none';
            }
            var recentapps = document.getElementById("recentApps");
            if (recentapps) recentapps.classList.add('d-none');
            return;
        }

        if (this.fullScreenEnabled && this.env.services.ui.size >= 4) {
            const nav = document.querySelector('.o_main_navbar.infinito-navbar-hover');
            if (nav) {
                const visible = ev.clientY <= 20 || nav.contains(ev.target)
                    || nav.contains(document.activeElement)
                    || !!nav.querySelector('[aria-expanded="true"]');
                nav.classList.toggle('infinito-navbar-visible', visible);
            }
        }

        if (this.recentApps && this.env.services.ui.size >= 4) {
            var recentapps = document.getElementById("recentApps");
            if (ev.clientY >= (window.innerHeight - 200)) {
                if (recentapps) recentapps.classList.remove('d-none');
            } else {
                if (recentapps) recentapps.classList.add('d-none');
            }
        }

        if ((session.infinitoBookmarks || []).length && session.infinitoBookmark && this.env.services.ui.size >= 4) {
            var Menuboook = document.getElementById("menuBookmark");
            if (ev.clientX >= (window.innerWidth - 160) || ev.target.closest('#menuBookmark')) {
                if (Menuboook) Menuboook.classList.add('d-flex');
            } else {
                if (Menuboook) Menuboook.classList.remove('d-flex');
            }
        }

        let now = new Date();
        if (this.last_check != now.getMinutes()) {
            this.darkModeCheck();
            this.last_check = now.getMinutes();
        }
    },

    darkModeCheck() {
        const webClient = document.querySelector('.o_web_client');

        const enableDark = () => {
            if (webClient) webClient.classList.add('dark-mode');
            // html.dark-mode is the persistent dark canvas background.
            // It carries no filter (filter:none !important in CSS) so there
            // is no double-inversion. Its background-color prevents the white
            // flash during the GPU compositing gap on every SPA navigation.
            document.documentElement.classList.add('dark-mode');
            try {
                localStorage.setItem('infinito_dark_mode', '1');
            } catch (e) {
            }
            this.is_dark = true;
        };

        const disableDark = () => {
            if (webClient) webClient.classList.remove('dark-mode');
            document.body.classList.remove('dark-mode');
            document.documentElement.classList.remove('dark-mode');
            try {
                localStorage.removeItem('infinito_dark_mode');
            } catch (e) {
            }
            this.is_dark = false;
        };

        if (session.infinitoDark) {
            if (session.infinitoDarkMode === 'auto') {
                window.matchMedia('(prefers-color-scheme: dark)').matches ? enableDark() : disableDark();
            } else if (session.infinitoDarkMode == 'all') {
                enableDark();
            } else {
                let now = new Date();
                let hour = now.getHours();
                let min = now.getMinutes();
                let start = session.infinitoDarkStart.split(':');
                let startHour = parseInt(start[0]);
                let startMin = parseInt(start[1]);
                let end = session.infinitoDarkEnd.split(':');
                let endHour = parseInt(end[0]);
                let endMin = parseInt(end[1]);

                if (startHour > endHour) {
                    endHour += 24;
                    if (hour < startHour) {
                        hour += 24;
                    }
                }

                let dark = false;
                if (endHour > hour && hour > startHour) {
                    dark = true;
                } else if (hour == startHour && min >= startMin && hour < endHour) {
                    dark = true;
                } else if (hour == endHour && min <= endMin && hour >= startHour) {
                    dark = true;
                }

                if (dark) {
                    enableDark();
                } else {
                    disableDark();
                }
            }
        } else {
            // Unconditional disableDark() removes html.dark-mode added by the
            // inline guard script, preventing images from appearing inverted in
            // light mode (the dark-mode img filter has no body invert to cancel it).
            disableDark();
        }
    },
});

registry.category("main_components").add("infinito.bookmarks", { Component: MenuBookmark });
registry.category("main_components").add("infinito.recent_apps", { Component: InfinitoRecentApps });
