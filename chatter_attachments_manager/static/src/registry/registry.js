/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { EventBus } from "@odoo/owl";
import { Registry } from "@web/core/registry";

// Patching the Registry to check duplicating 'file_viewer1'
patch(Registry.prototype, {
    setup() {
        super.setup();
    },
    add(key, value, {
        force,
        sequence
    } = {}) {
        try {
            if (!force && key in this.content) {
                if (key == 'web.file_viewer1') {
                    // Handle the case when key is 'web.file_viewer1'
                    return; // Skip adding the key
                }
                throw new DuplicatedKeyError(`Cannot add '${key}' in this registry: it already exists`);
            }
        } catch (error) {
            return;
        }
        let previousSequence;
        if (force) {
            const elem = this.content[key];
            previousSequence = elem && elem[0];
        }
        sequence = sequence === undefined ? previousSequence || 50 : sequence;
        this.content[key] = [sequence, value];
        const payload = {
            operation: "add",
            key,
            value
        };
        this.trigger("UPDATE", payload);
        return this;
    }
})