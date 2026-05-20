/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { DuplicatedKeyError, Registry } from "@web/core/registry";

// Patching the Registry to suppress DuplicatedKeyError for file_viewer keys
// registered by the TUI Image Editor on every open.
patch(Registry.prototype, {
    add(key, value, {
        force,
        sequence
    } = {}) {
        try {
            return super.add(key, value, { force, sequence });
        } catch (error) {
            if (
                error instanceof DuplicatedKeyError &&
                (key === "web.file_viewer1" || key === "web.file_viewer2" || key === "web.file_viewer3")
            ) {
                return this;
            }
            throw error;
        }
    }
})
