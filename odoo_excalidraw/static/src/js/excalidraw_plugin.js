/** @odoo-module **/

import { Plugin } from "@html_editor/plugin"; // Correct import path based on Odoo 19 structure
import { ExcalidrawDialog } from "./excalidraw_dialog";
import { isHtmlContentSupported } from "@html_editor/core/selection_plugin";
import { _t } from "@web/core/l10n/translation";

export class ExcalidrawPlugin extends Plugin {
    static id = "excalidraw";
    static dependencies = ["history", "dom", "dialog"]; // Added dialog dependency relative to the editor system if needed, but we use useService usually. Plugin system might not inject 'dialog' service directly, so we use env.

    resources = {
        user_commands: [
            {
                id: "insertExcalidraw",
                title: _t("Draw"),
                description: _t("Insert a drawing"),
                icon: "fa-pencil", // or fa-paint-brush
                run: this.insertExcalidraw.bind(this),
                isAvailable: isHtmlContentSupported,
            },
        ],
        toolbar_groups: [
            {
                id: "excalidraw_group",
                sequence: 30, // Adjust sequence to place it appropriately
            },
        ],
        toolbar_items: [
            {
                id: "excalidraw",
                groupId: "media",
                commandId: "insertExcalidraw",
            },
        ],
        powerbox_items: [
            {
                categoryId: "media",
                commandId: "insertExcalidraw",
            },
        ],
    };

    insertExcalidraw() {
        this.dependencies.dialog.addDialog(ExcalidrawDialog, {
            onSave: (base64Image) => {
                this.insertImage(base64Image);
            },
        });
    }

    insertImage(base64Image) {
        const img = this.document.createElement("img");
        img.src = base64Image;
        img.alt = "Drawing";
        img.style.maxWidth = "100%";

        this.dependencies.dom.insert(img);
        this.dependencies.history.addStep();
    }
}
