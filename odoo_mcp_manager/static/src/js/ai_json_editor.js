/** @odoo-module **/
import { registry } from "@web/core/registry";
import { TextField, textField } from "@web/views/fields/text/text_field";
import { useService } from "@web/core/utils/hooks";

/**
 * Code-style JSON/config editor widget with copy button.
 * Used for displaying platform configuration snippets.
 */
export class AiJsonEditor extends TextField {
    static template = "odoo_mcp_manager.AiJsonEditor";
    // Inherits TextField.props — includes placeholder, rowCount, lineBreaks, etc.

    setup() {
        super.setup();
        this.notification = useService("notification");
    }

    get value() {
        return this.props.record.data[this.props.name] || "";
    }

    async onCopyClick() {
        const value = this.value;
        if (value) {
            try {
                await navigator.clipboard.writeText(value);
                this.notification.add("Config copied to clipboard!", {
                    type: "success",
                    sticky: false,
                });
            } catch (err) {
                this.notification.add("Failed to copy: " + err, {
                    type: "danger",
                });
            }
        }
    }
}

export const aiJsonEditor = {
    ...textField,
    component: AiJsonEditor,
};

registry.category("fields").add("ai_json_editor", aiJsonEditor);

/**
 * Instruction display widget — read-only styled info box, no copy button.
 * Used for platform-specific setup guidance text.
 */
export class AiInstruction extends TextField {
    static template = "odoo_mcp_manager.AiInstruction";
    // Inherits TextField.props — no override needed.
}

export const aiInstruction = {
    ...textField,
    component: AiInstruction,
};

registry.category("fields").add("ai_instruction", aiInstruction);
