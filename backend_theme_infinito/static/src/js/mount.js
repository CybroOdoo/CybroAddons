/** @odoo-module **/
import { App } from "@odoo/owl";
import { getTemplate } from "@web/core/templates";
import { customDirectives, globalValues } from "@web/env";
import { appTranslateFn } from "@web/core/l10n/translation";

/** Mount an auxiliary theme root with Odoo templates and deterministic teardown. */
export async function mount(Component, target, config = {}) {
    const app = new App({
        getTemplate, customDirectives, globalValues,
        translateFn: appTranslateFn,
        ...config,
    });
    try {
        const component = await app.createRoot(Component, config).mount(target);
        return { component, destroy: () => app.destroy() };
    } catch (error) {
        app.destroy();
        throw error;
    }
}
