import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class ProjectLayout extends Interaction {
    static selector = ".js_portfolio_project";
    start() {
        const layoutEl = this.el.offsetParent.querySelector(".s_project_layout");
        const nameEl = this.el.querySelector("input[name='project_name']");
        const imageEl = this.el.querySelector("input[name='project_image']");
        const descriptionEl = this.el.querySelector("input[name='project_description']");

        if (layoutEl && nameEl) {
            const nameLEl = layoutEl.querySelector(".js_project_layout_name");
            if (nameLEl) {
                nameLEl.textContent = nameEl.value;
            }
        }

        if (layoutEl && imageEl) {
            const imageLEl = layoutEl.querySelector(".js_project_layout_image");
            if (imageLEl) {
                imageLEl.src = `data:image/png;base64, ${imageEl.value.replace("b'", '').replace("'", '')}`
            }
        }

        if (layoutEl && descriptionEl) {
            const descriptionLEl = layoutEl.querySelector(".js_project_layout_description");
            if (descriptionLEl) {
                descriptionLEl.textContent = descriptionEl.value;
            }
        }
    }
}

registry.category("public.interactions").add("theme_modern_portfolio.project_layout", ProjectLayout);
