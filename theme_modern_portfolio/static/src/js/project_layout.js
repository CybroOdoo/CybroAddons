/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ProjectLayout = publicWidget.Widget.extend({
    selector: ".js_portfolio_project",

    /**
     * @override
     */
    start: function () {
        const layoutEl = this.el.offsetParent ? this.el.offsetParent.querySelector(".s_project_layout") : document.querySelector(".s_project_layout");
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
        return this._super.apply(this, arguments);
    },
});
