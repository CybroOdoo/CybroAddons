/** @odoo-module */

import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

let globalView3D = null;
let currentBlobUrl = null;

function base64ToBlobUrl(base64Data) {
    try {
        const cleaned = base64Data.trim();
        const byteCharacters = atob(cleaned);
        const byteNumbers = new Uint8Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const file = new File([byteNumbers], "model.glb", { type: "model/gltf-binary" });
        return URL.createObjectURL(file);
    } catch (_e) {
        return `data:model/gltf-binary;base64,${base64Data.trim()}`;
    }
}

function get3DTrigger(target) {
    if (!target || typeof target.closest !== "function") return null;
    return target.closest("[data-type='3d']")
        || target.closest(".o_3d_image")
        || target.closest("#product_3d_image")
        || target.closest("[id='3d_image']");
}

function getCarouselControl(target) {
    if (!target || typeof target.closest !== "function") return null;
    const li = target.closest(".carousel-indicators li");
    if (li && !get3DTrigger(li)) {
        return li;
    }
    return target.closest(".carousel-control-prev") || target.closest(".carousel-control-next");
}

function show3DViewer() {
    const productOuter = document.querySelector(".o_carousel_product_outer");
    const productMain = document.getElementById("product_main");
    const indicator3D = document.getElementById("product_3d_image")
        || document.getElementById("3d_image")
        || document.querySelector("[data-type='3d']")
        || document.querySelector(".o_3d_image");
    const indicators = document.querySelectorAll(".carousel-indicators li");

    if (!productMain) return;

    // Highlight 3D indicator
    indicators.forEach((li) => li.classList.remove("active"));
    if (indicator3D) {
        indicator3D.classList.add("active");
    }

    // Match dimensions to productOuter before hiding it
    if (productOuter) {
        const rect = productOuter.getBoundingClientRect();
        if (rect.height > 100 && rect.width > 100) {
            productMain.style.height = `${rect.height}px`;
            productMain.style.width = `${rect.width}px`;
        }
        productOuter.style.setProperty("display", "none", "important");
    }

    productMain.style.display = "block";
    productMain.classList.remove("d-none");

    // If already initialized, just resize
    if (globalView3D) {
        requestAnimationFrame(() => {
            try {
                globalView3D.resize();
            } catch (e) {}
        });
        return;
    }

    // Get product ID
    let productId = productMain.dataset.productId
        || indicator3D?.dataset.productId
        || document.querySelector("input[name='product_template_id']")?.value
        || document.querySelector("[data-product-template-id]")?.dataset.productTemplateId;

    if (!productId) {
        const match = window.location.pathname.match(/-([0-9]+)(?:$|[?#/])/);
        if (match) {
            productId = match[1];
        }
    }

    if (!productId) {
        return;
    }

    // Ensure canvas exists inside productMain
    let canvas = productMain.querySelector("canvas.view3d-canvas");
    if (!canvas) {
        canvas = document.createElement("canvas");
        canvas.className = "view3d-canvas";
        canvas.style.position = "absolute";
        canvas.style.top = "0";
        canvas.style.left = "0";
        canvas.style.width = "100%";
        canvas.style.height = "100%";
        productMain.appendChild(canvas);
    }

    // Load model from RPC or direct URL
    rpc("/product/3d", {
        product_id: parseInt(productId, 10),
    }).then((data) => {
        let modelUrl = `/product/3d_model/${productId}/model.glb`;
        if (data && data["3D_model"]) {
            if (currentBlobUrl) {
                try { URL.revokeObjectURL(currentBlobUrl); } catch (e) {}
            }
            currentBlobUrl = base64ToBlobUrl(data["3D_model"]);
            modelUrl = currentBlobUrl;
        }

        try {
            if (globalView3D) {
                try { globalView3D.destroy(); } catch (e) {}
            }
            globalView3D = new View3D("#product_main", {
                src: modelUrl,
            });
            globalView3D.on("loadError", (_e) => {
                const fallback = `/product/3d_model/${productId}/model.glb`;
                if (modelUrl !== fallback) {
                    globalView3D.load(fallback);
                }
            });
        } catch (_err) {
            // View3D init fallback
        }
    }).catch((_err) => {
        try {
            globalView3D = new View3D("#product_main", {
                src: `/product/3d_model/${productId}/model.glb`,
            });
        } catch (e) {}
    });
}

function hide3DViewer() {
    const productOuter = document.querySelector(".o_carousel_product_outer");
    const productMain = document.getElementById("product_main");
    const indicator3D = document.getElementById("product_3d_image")
        || document.getElementById("3d_image")
        || document.querySelector("[data-type='3d']")
        || document.querySelector(".o_3d_image");

    if (indicator3D) {
        indicator3D.classList.remove("active");
    }
    if (productMain) {
        productMain.style.display = "none";
    }
    if (productOuter) {
        productOuter.style.removeProperty("display");
    }
}

function handleClick(ev) {
    // Only process clicks if a 3D element exists on current page
    if (!document.getElementById("product_main") &&
        !document.getElementById("product_3d_image") &&
        !document.getElementById("3d_image") &&
        !document.querySelector("[data-type='3d']")) {
        return;
    }

    const trigger3D = get3DTrigger(ev.target);
    if (trigger3D) {
        ev.preventDefault();
        ev.stopPropagation();
        ev.stopImmediatePropagation();
        show3DViewer();
        return;
    }

    const normalControl = getCarouselControl(ev.target);
    if (normalControl) {
        hide3DViewer();
    }
}

function checkAutoInit() {
    const productMain = document.getElementById("product_main");
    if (productMain && productMain.dataset.hasImage === "false") {
        show3DViewer();
    }
}

// Global click listener with useCapture ensures clicks on 360 are captured
if (typeof window !== "undefined") {
    document.addEventListener("click", handleClick, true);
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", checkAutoInit);
    } else {
        setTimeout(checkAutoInit, 100);
    }
}

export class Product3DViewInteraction extends Interaction {
    static selector = "#o-carousel-product, .o_wsale_product_page";

    setup() {
        this.onClick = (ev) => handleClick(ev);
    }

    start() {
        this.el.addEventListener("click", this.onClick, true);
        const productMain = this.el.querySelector("#product_main") || document.getElementById("product_main");
        if (productMain && productMain.dataset.hasImage === "false") {
            show3DViewer();
        }
    }

    destroy() {
        this.el.removeEventListener("click", this.onClick, true);
        if (currentBlobUrl) {
            try { URL.revokeObjectURL(currentBlobUrl); } catch (e) {}
            currentBlobUrl = null;
        }
        if (globalView3D) {
            try { globalView3D.destroy(); } catch (e) {}
            globalView3D = null;
        }
    }
}

registry
    .category("public.interactions")
    .add("website_model_viewer_widget.product_3d_view", Product3DViewInteraction);
