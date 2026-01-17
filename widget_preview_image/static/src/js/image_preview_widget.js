/** @odoo-module **/
// model for patch the imageField and add function for image preview
import { ImageField } from '@web/views/fields/image/image_field';
import { patch } from "@web/core/utils/patch";

function removeEnlargedImage() {
    // function for close the enlarged image
    const enlargedImg = document.querySelector(".enlarged-image");
    document.body.removeChild(enlargedImg);
    const blurredBg = document.querySelector(".blurred-bg");
    document.body.removeChild(blurredBg);
    const closeButton = document.querySelector(".close-button");
    document.body.removeChild(closeButton);
    document.body.classList.remove("enlarged-image-body");
}

patch(ImageField.prototype, {
    img_click(ev) {
        // image click function for enlarge the imageField
        const clickedImg = ev.target;
        if (document.body.classList.contains("enlarged-image-body")) {
            removeEnlargedImage();
            return;
        }
        const newImg = document.createElement("img");
        if (clickedImg.src.includes("avatar_128") && (clickedImg.name != 'avatar_128')){
            newImg.src = clickedImg.src.replace("avatar_128", "image_1920");
        }
        else if (clickedImg.src.includes("image_128") && (clickedImg.name != 'image_128')){
            newImg.src = clickedImg.src.replace("image_128", "image_1920");
        }
        else {
            newImg.src = clickedImg.src
        }
        newImg.classList.add("enlarged-image");
        newImg.style.position = "fixed";
        newImg.style.top = 0;
        newImg.style.bottom = 0;
        newImg.style.left = 0;
        newImg.style.right = 0;
        newImg.style.margin = "auto";
        newImg.style.maxWidth = "95%";
        newImg.style.maxHeight = "95%";
        newImg.style.zIndex = 9999;

        // Create a div element for the blurred background
        const blurredBg = document.createElement("div");
        blurredBg.classList.add("blurred-bg");
        blurredBg.style.position = "fixed";
        blurredBg.style.top = 0;
        blurredBg.style.bottom = 0;
        blurredBg.style.left = 0;
        blurredBg.style.right = 0;
        blurredBg.style.background = "rgba(0, 0, 0, 0.5)";
        blurredBg.style.backdropFilter = "blur(10px)";
        blurredBg.style.zIndex = 9998;

        // Create a button to close the enlarged image
        const closeButton = document.createElement("button");
        closeButton.classList.add("close-button");
        closeButton.innerHTML = "Close";
        closeButton.style.position = "fixed";
        closeButton.style.top = "10px";
        closeButton.style.right = "10px";
        closeButton.style.padding = "5px";
        closeButton.style.background = "transparent";
        closeButton.style.border = "none";
        closeButton.style.color = "#fff";
        closeButton.style.fontSize = "16px";
        closeButton.style.zIndex = 9999;

        // Add a click event listener to the close button to remove the enlarged image
        closeButton.addEventListener("click", removeEnlargedImage);

        // Add the img, div, and button elements to the body
        document.body.appendChild(blurredBg);
        document.body.appendChild(newImg);
        document.body.appendChild(closeButton);

        // Add a class to the body to indicate that an image is enlarged
        document.body.classList.add("enlarged-image-body");
    },
});
