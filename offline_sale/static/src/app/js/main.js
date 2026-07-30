/** @odoo-module **/

import { whenReady } from "@odoo/owl";
import { mountComponent } from "@web/env";
import { OfflineSalesApp } from "@offline_sale/app/js/offline_sale_app";
import { registry, Registry } from "@web/core/registry";

/**
 * Override the registry add method to suppress duplicate registration warnings.
 *
 * Some Odoo modules attempt to register the same key multiple times,
 * which generates repetitive console warnings. This override silently
 * ignores duplicate registrations unless the `force` option is specified.
 */
const originalAdd = Registry.prototype.add;
Registry.prototype.add = function (key, value, options) {
    if (this.contains(key) && !options?.force) {
        return this;
    }
    return originalAdd.call(this, key, value, options);
};

/**
 * Remove standard Odoo backend components from the main component registry.
 *
 * Since Offline Sales runs as a standalone application, backend UI components
 * such as the WebClient, navbar, and related services are not required and
 * may cause rendering issues due to missing session or company data.
 */
const mainComponents = registry.category("main_components");
mainComponents.getEntries().forEach(([key]) => mainComponents.remove(key));

/**
 * Remove standard Odoo backend chrome elements from the page.
 *
 * This function cleans up UI elements that may be rendered by the WebClient,
 * such as navigation bars, home menus, action managers, and expiration panels,
 * ensuring that only the Offline Sales interface remains visible.
 */
function _stripStandardOdooChrome() {
    const selectors = [
        "body > .o_navbar",
        "body > header.o_navbar",
        "body > nav.o_main_navbar",
        "body > .o_main_navbar",
        "body > .o_action_manager",
        "body > .o_home_menu_background",
        "body > .o_home_menu",
        "body > .database_expiration_panel",
    ];
    document.querySelectorAll(selectors.join(",")).forEach((el) => {
        if (el.id !== "offline_sale_root" && !el.contains(document.getElementById("offline_sale_root"))) {
            el.remove();
        }
    });
    document.body.classList.remove("o_home_menu_background");
}

/**
 * Initialize and mount the Offline Sales application.
 *
 * Waits for the DOM and Owl framework to be ready, mounts the root
 * Offline Sales component, removes the loading spinner, and continuously
 * strips any backend UI elements that may appear while the Odoo WebClient
 * is still booting.
 *
 * @async
 * @returns {Promise<void>}
 */
async function startApp() {
    await whenReady();
    try {
        const rootElement = document.getElementById('offline_sale_root');
        if (rootElement) {
            const app = await mountComponent(OfflineSalesApp, rootElement, {
                name: "Offline Sales"
            });
            // Remove the Initializing spinner if it exists
            const loadingSpinner = rootElement.querySelector('.fa-circle-o-notch');
            if (loadingSpinner) loadingSpinner.parentElement.parentElement.remove();

            // Strip any standard Odoo backend chrome that may have rendered alongside our app.
            _stripStandardOdooChrome();
            // Re-strip on subsequent mutations (the WebClient sometimes finishes mounting later).
            const observer = new MutationObserver(() => _stripStandardOdooChrome());
            observer.observe(document.body, { childList: true, subtree: false });
            // Stop observing after a few seconds — by then the WebClient has finished booting.
            setTimeout(() => observer.disconnect(), 8000);
        }
    } catch (error) {
        console.error("Offline Sales: Failed to start", error);
    }
}

startApp();
