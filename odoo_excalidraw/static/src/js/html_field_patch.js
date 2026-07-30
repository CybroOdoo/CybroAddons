/** @odoo-module **/

import { HtmlField } from "@web_editor/js/backend/html_field";
import { Wysiwyg } from "@web_editor/js/wysiwyg/wysiwyg";

import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

import { ExcalidrawDialog } from "./excalidraw_dialog";
import { _t } from "@web/core/l10n/translation";


patch(Wysiwyg.prototype, {
    setup() {
        super.setup(...arguments);

        this.excalidrawDialogService =
            useService("dialog");
    },
});

patch(Wysiwyg.prototype, {
    _getPowerboxOptions() {
        const options =
            super._getPowerboxOptions(...arguments);

        options.categories = [
            ...(options.categories || []),
            {
                name: _t("Drawing"),
                priority: 25,
            },
        ];

        options.commands = [
            ...(options.commands || []),
            {
                category: _t("Drawing"),
                name: _t("Draw"),
                priority: 10,
                description: _t(
                    "Insert Excalidraw drawing"
                ),
                fontawesome: "fa-pencil",

                callback: () => {
                    const savedSelection =
                        this.odooEditor.editable.ownerDocument.getSelection();

                    const range =
                        savedSelection.rangeCount > 0
                            ? savedSelection.getRangeAt(0).cloneRange()
                            : null;

                    this.excalidrawDialogService.add(
                        ExcalidrawDialog,
                        {
                            onSave: (base64Image) => {
                                if (range) {
                                    const selection =
                                        this.odooEditor.editable.ownerDocument.getSelection();

                                    selection.removeAllRanges();
                                    selection.addRange(range);
                                }

                                const img =
                                    this.odooEditor.document.createElement("img");

                                img.src = base64Image;
                                img.alt = "Drawing";
                                img.style.maxWidth = "100%";

                                range.insertNode(img);

                                range.setStartAfter(img);
                                range.setEndAfter(img);

                                this.odooEditor.historyStep();
                            },
                        }
                    );
                },
            },
        ];

        return options;
    },
});