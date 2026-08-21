/** @odoo-module **/

import { Plugin } from "@html_editor/plugin";
import { _t } from "@web/core/l10n/translation";
import { isHtmlContentSupported } from "@html_editor/core/selection_plugin";
import { closestElement } from "@html_editor/utils/dom_traversal";

/**
 * Editor plugin that adds a clipboard/copy-to-clipboard block command for Information articles.
 * Registers a powerbox command to insert a styled copyable code/text block into the editor.
 */
export class ClipboardPluginCommunity extends Plugin {
    static id = "clipboardCommunity";
    static dependencies = ["dom", "selection", "history", "baseContainer"];

    resources = {
        user_commands: [
            {
                id: "insertClipboard",
                title: _t("Clipboard"),
                description: _t("Add a clipboard section"),
                icon: "fa-pencil-square",
                isAvailable: (selection) =>
                    isHtmlContentSupported(selection) &&
                    !closestElement(selection.anchorNode, ".o_info_clipboard"),
                run: () => {
                    this.insertClipboard();
                },
            },
        ],
        powerbox_items: [
            {
                commandId: "insertClipboard",
                categoryId: "structure",
            },
        ],
    };

    setup() {
        this.addDomListener(this.editable, "click", this.onClick.bind(this));
    }

    insertClipboard() {
        const section = this.document.createElement("div");
        section.classList.add("o_info_clipboard");
        section.setAttribute("data-embedded", "clipboardCommunity");

        const header = this.document.createElement("div");
        header.classList.add("o_clipboard_header");
        header.contentEditable = "false";

        const title = this.document.createElement("span");
        title.classList.add("text-muted");
        title.textContent = _t("Clipboard");

        const btn = this.document.createElement("button");
        btn.classList.add("btn", "btn-sm", "btn-light", "o_clipboard_button");
        btn.title = _t("Copy to clipboard");

        const icon = this.document.createElement("i");
        icon.classList.add("fa", "fa-copy");
        btn.appendChild(icon);

        header.appendChild(title);
        header.appendChild(btn);

        const content = this.document.createElement("div");
        content.classList.add("o_clipboard_content");
        content.setAttribute("data-embedded-editable", "content");
        content.contentEditable = "true";

        const baseContainer = this.dependencies.baseContainer.createBaseContainer();
        const br = this.document.createElement("br");
        baseContainer.appendChild(br);
        content.appendChild(baseContainer);

        section.appendChild(header);
        section.appendChild(content);

        this.dependencies.dom.insert(section);

        this.dependencies.selection.setCursorStart(baseContainer);
        this.dependencies.history.addStep();
    }

    onClick(ev) {
        const btn = ev.target.closest(".o_clipboard_button");
        if (btn) {
            ev.preventDefault();
            const clipboardBlock = btn.closest(".o_info_clipboard");
            if (clipboardBlock) {
                const contentNode = clipboardBlock.querySelector(".o_clipboard_content");
                if (contentNode) {
                    const text = contentNode.innerText;
                    navigator.clipboard.writeText(text).then(() => {
                        const icon = btn.querySelector("i");
                        if (icon) {
                            icon.classList.remove("fa-copy");
                            icon.classList.add("fa-check", "text-success");
                            setTimeout(() => {
                                icon.classList.add("fa-copy");
                                icon.classList.remove("fa-check", "text-success");
                            }, 1500);
                        }
                    });
                }
            }
        }
    }
}
