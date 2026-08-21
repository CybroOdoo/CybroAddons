/** @odoo-module **/

import { Plugin } from "@html_editor/plugin";
import { _t } from "@web/core/l10n/translation";
import { isHtmlContentSupported } from "@html_editor/core/selection_plugin";
import { closestElement } from "@html_editor/utils/dom_traversal";

/**
 * Editor plugin that makes heading elements collapsible/foldable in Information articles.
 * Clicking a heading toggle hides or shows the content below it until the next same-level heading.
 */
export class FoldableSectionPlugin extends Plugin {
    static id = "foldableSectionCommunity";
    static dependencies = ["dom", "selection", "history", "baseContainer"];

    resources = {
        user_commands: [
            {
                id: "insertFoldableSection",
                title: _t("Foldable Section"),
                description: _t("Add a foldable section"),
                icon: "fa-outdent",
                isAvailable: (selection) =>
                    isHtmlContentSupported(selection) &&
                    !closestElement(selection.anchorNode, "[data-embedded='foldableSection'] .o_foldable_header"),
                run: () => {
                    this.insertFoldableSection();
                },
            },
        ],
        powerbox_items: [
            {
                commandId: "insertFoldableSection",
                categoryId: "structure",
            },
        ],
    };

    setup() {
        this.addDomListener(this.editable, "click", this.onClick.bind(this));
    }

    insertFoldableSection() {
        const section = this.document.createElement("div");
        section.classList.add("o_foldable_section");
        section.setAttribute("data-embedded", "foldableSection");

        const header = this.document.createElement("div");
        header.classList.add("o_foldable_header");
        header.contentEditable = "false";

        const icon = this.document.createElement("i");
        icon.classList.add("fa", "fa-fw", "fa-caret-down", "o_foldable_icon");

        const title = this.document.createElement("span");
        title.classList.add("o_foldable_title");
        title.setAttribute("data-embedded-editable", "title");
        title.contentEditable = "true";

        header.appendChild(icon);
        header.appendChild(title);

        const content = this.document.createElement("div");
        content.classList.add("o_foldable_content");
        content.setAttribute("data-embedded-editable", "content");

        const baseContainer = this.dependencies.baseContainer.createBaseContainer();
        const br = this.document.createElement("br");
        baseContainer.appendChild(br);
        content.appendChild(baseContainer);

        section.appendChild(header);
        section.appendChild(content);

        this.dependencies.dom.insert(section);

        this.dependencies.selection.setCursorStart(title);
        this.dependencies.history.addStep();
    }

    onClick(ev) {
        const header = ev.target.closest(".o_foldable_header");
        if (header && !ev.target.closest(".o_foldable_title")) {
            const section = header.closest(".o_foldable_section");
            if (section) {
                section.classList.toggle("o_foldable_collapsed");
            }
        }
    }
}
