/** @odoo-module **/
import { mount } from "./mount";
import { registry } from "@web/core/registry";

export const EditorService = {
    dependencies: ["action"],
    start(env, { action }) {
        return {
            open() {
                return action.doAction({
                    type: "ir.actions.client",
                    tag: "backend_theme_infinito.editor_client_action",
                    target: "current",
                });
            },
        };
    },
};

registry.category("services").add("editor", EditorService);

// Own auxiliary Owl roots here so navigation and repeated clicks share teardown.
registry.category("services").add("infinito_advanced_panel", {
    start(env) {
        let pending = null;
        let mounted = null;
        let generation = 0;
        const clearLayout = () => {
            document.body.classList.remove('infinito-advanced-sidebar-open');
            document.body.style.removeProperty('--infinito-advanced-sidebar-width');
        };
        return {
            close() {
                generation++;
                mounted?.destroy();
                mounted = null;
                pending = null;
                clearLayout();
            },
            open(Component) {
                if (mounted || pending) return pending;
                const current = ++generation;
                pending = mount(Component, document.body, { env }).then(app => {
                    if (generation !== current) {
                        app.destroy();
                        return;
                    }
                    mounted = app;
                    const panel = app.component.panelRef?.();
                    const width = Math.ceil(panel?.getBoundingClientRect().width || 343);
                    document.body.style.setProperty('--infinito-advanced-sidebar-width', `${width}px`);
                    document.body.classList.add('infinito-advanced-sidebar-open');
                }).finally(() => {
                    if (generation === current) pending = null;
                });
                return pending;
            },
        };
    },
});
