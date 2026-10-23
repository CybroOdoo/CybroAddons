/** @odoo-module **/
import { ImageField } from '@web/views/fields/image/image_field';
import { patch } from "@web/core/utils/patch";
import { onMounted, onWillUnmount } from "@odoo/owl";

function onKeyDown(ev) {
    if (ev.key === "Escape") {
        removeEnlargedImage();
    }
}

function removeEnlargedImage() {
    const enlargedImg = document.querySelector(".enlarged-image");
    if (enlargedImg) {
        enlargedImg.remove();
    }
    const blurredBg = document.querySelector(".blurred-bg");
    if (blurredBg) {
        blurredBg.remove();
    }
    const closeButton = document.querySelector(".close-button");
    if (closeButton) {
        closeButton.remove();
    }
    document.body.classList.remove("enlarged-image-body");
    document.removeEventListener("keydown", onKeyDown);
}

patch(ImageField.prototype, {
    setup() {
        super.setup();

        // Store a bound reference so we can cleanly remove it on unmount
        this._imgPreviewHandler = (ev) => this.img_click(ev);

        onMounted(() => {
            const rootEl = this.__owl__?.bdom?.el;
            if (rootEl) {
                rootEl.addEventListener("click", this._imgPreviewHandler);
            }
        });

        onWillUnmount(() => {
            // Clean up to avoid memory leaks
            const rootEl = this.__owl__?.bdom?.el;
            if (rootEl) {
                rootEl.removeEventListener("click", this._imgPreviewHandler);
            }
        });
    },

    img_click(ev) {
        // Only act when an <img> is the actual click target
        const clickedImg = ev.target;
        if (!(clickedImg instanceof HTMLImageElement)) {
            return;
        }

        // If an enlarged image is already showing, close it instead
        if (document.body.classList.contains("enlarged-image-body")) {
            removeEnlargedImage();
            return;
        }

        // Build the high-res URL by substituting the thumbnail field name
        const newImg = document.createElement("img");
        if (clickedImg.src.includes("avatar_128") && clickedImg.name !== "avatar_128") {
            newImg.src = clickedImg.src.replace("avatar_128", "image_1920");
        } else if (clickedImg.src.includes("image_128") && clickedImg.name !== "image_128") {
            newImg.src = clickedImg.src.replace("image_128", "image_1920");
        } else {
            newImg.src = clickedImg.src;
        }
        newImg.classList.add("enlarged-image");
        Object.assign(newImg.style, {
            position: "fixed",
            top: "0",
            bottom: "0",
            left: "0",
            right: "0",
            margin: "auto",
            maxWidth: "95%",
            maxHeight: "95%",
            zIndex: "9999",
            cursor: "pointer",
        });
        newImg.addEventListener("click", removeEnlargedImage);

        // Semi-transparent blurred backdrop
        const blurredBg = document.createElement("div");
        blurredBg.classList.add("blurred-bg");
        Object.assign(blurredBg.style, {
            position: "fixed",
            top: "0",
            bottom: "0",
            left: "0",
            right: "0",
            background: "rgba(0, 0, 0, 0.5)",
            backdropFilter: "blur(10px)",
            zIndex: "9998",
            cursor: "pointer",
        });
        blurredBg.addEventListener("click", removeEnlargedImage);

        // Close button
        const closeButton = document.createElement("button");
        closeButton.classList.add("close-button");
        closeButton.innerHTML = "&times;";
        closeButton.setAttribute("aria-label", "Close image preview");
        Object.assign(closeButton.style, {
            position: "fixed",
            top: "15px",
            right: "20px",
            padding: "5px 12px",
            background: "rgba(0, 0, 0, 0.5)",
            border: "1px solid rgba(255, 255, 255, 0.3)",
            borderRadius: "50%",
            color: "#fff",
            fontSize: "24px",
            lineHeight: "1",
            cursor: "pointer",
            zIndex: "9999",
        });
        closeButton.addEventListener("click", removeEnlargedImage);

        // Mount overlay
        document.body.appendChild(blurredBg);
        document.body.appendChild(newImg);
        document.body.appendChild(closeButton);
        document.body.classList.add("enlarged-image-body");
        document.addEventListener("keydown", onKeyDown);
    },
});
