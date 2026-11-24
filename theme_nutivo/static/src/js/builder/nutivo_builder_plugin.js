/**
 * Nutivo in the website builder: the cards and items of the Nutivo grids can
 * be moved inside their grid, as any other column.
 */
import { registry } from "@web/core/registry";
import { Plugin } from "@html_editor/plugin";

export class NutivoBuilderPlugin extends Plugin {
    static id = "nutivoBuilder";
    resources = {
        is_movable_selectors: [
            {
                selector:
                    ".nv-cat-row > *, .nv-festive-grid > *, .nv-stats-band > *, " +
                    ".nv-testi-track > *, .nv-process-grid > *, .nv-origin-grid > *, " +
                    ".nv-help-grid > *, .nv-perks__row > *",
                direction: "horizontal",
            },
            {
                selector: ".nv-timeline > *, .nv-faq__list > *",
                direction: "vertical",
            },
        ],
    };
}

registry.category("website-plugins").add(NutivoBuilderPlugin.id, NutivoBuilderPlugin);
