import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class Product360View extends Interaction {
    // The image column of the product page, only when it contains the 360 block
    static selector = ".o_wsale_product_images";
    static selectorHas = "#image_360";

    dynamicContent = {
        ".view_360": {
            "t-on-click": this.onStart360,
            "t-att-class": () => ({ "d-none": this.is360 }),
        },
        ".stop_view": {
            "t-on-click": this.onStop360,
            "t-att-class": () => ({ "d-none": !this.is360 }),
        },
        "#image_360": {
            "t-att-class": () => ({ "d-none": !this.is360 }),
        },
        // the normal product images are hidden while the 360 view is active
        _root: {
            "t-att-class": () => ({ "o_360_active": this.is360 }),
        },
        "#image_360 .list": {
            "t-on-mousemove.noUpdate": this.onMouseMove,
        },
    };

    setup() {
        this.is360 = false;
        this.frames = [];
    }

    start() {
        this.frames = [...this.el.querySelectorAll("#image_360 .list li")];
        this.showFrame(0);
    }

    onStart360() {
        this.is360 = true;
    }

    onStop360() {
        this.is360 = false;
    }

    // Moving the mouse across the image rotates the product
    onMouseMove(ev) {
        if (!this.frames.length) {
            return;
        }
        const rect = ev.currentTarget.getBoundingClientRect();
        if (!rect.width) {
            return;
        }
        const ratio = Math.min(Math.max((ev.clientX - rect.left) / rect.width, 0), 1);
        const index = Math.min(Math.floor(ratio * this.frames.length), this.frames.length - 1);
        this.showFrame(index);
    }

    showFrame(index) {
        this.frames.forEach((li, i) => li.classList.toggle("d-none", i !== index));
    }
}

registry
    .category("public.interactions")
    .add("product_360_degree_view_in_website.product_360_view", Product360View);
