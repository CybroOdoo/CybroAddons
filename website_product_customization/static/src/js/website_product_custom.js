/** @odoo-module **/
import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';

export class CanvasWidget extends Interaction {
    static selector = '#product_detail';

    dynamicContent = {
        '#product-design': { 't-on-change': this.onChangeSelect },
        '.design_save': { 't-on-click': this.onSave },
        '#product_customize_btn': { 't-on-click': this.addProductDesign },
    };

    setup() {
        this.canvas = null;
        // Fix blank dropdown option labels: if a design record has no name,
        // show "Design <id>" using the option's value attribute as fallback.
        const select = this.el.querySelector('#product-design');
        if (select) {
            select.querySelectorAll('option').forEach((opt) => {
                if (!opt.value) return; // skip the placeholder option
                if (!opt.textContent.trim()) {
                    opt.textContent = 'Design ' + opt.value;
                }
            });
        }
    }

    start() {
        this.addListener(document, "keydown", (event) => this.onKeyDown(event));
    }

    destroy() {
        super.destroy();
        if (this.canvas) {
            this.canvas.dispose();
            this.canvas = null;
        }
    }

    onKeyDown(event) {
        if (event.key === "Delete" && this.canvas) {
            const activeObject = this.canvas.getActiveObject();
            if (activeObject) {
                this.canvas.remove(activeObject);
            }
        }
    }

    onChangeSelect() {
        if (typeof fabric === "undefined") {
            return;
        }
        const select = this.el.querySelector('#product-design');
        const selectedOption = select ? select.value.toString() : '';
        if (!selectedOption) return;

        const designImage = new Image();
        designImage.crossOrigin = 'anonymous';
        designImage.src = '/web/image/product.design/' + selectedOption + '/product_design';
        designImage.onload = () => {
            if (!this.canvas) {
                this.canvas = new fabric.Canvas('tshirt-canvas');
            } else {
                this.canvas.clear();
            }
            const image = new fabric.Image(designImage);
            image.scaleToHeight(100);
            image.scaleToWidth(100);
            this.canvas.centerObject(image);
            this.canvas.add(image);
            this.canvas.renderAll();
        };
    }

    onSave() {
        const node = this.el.querySelector('#tshirt-div') || document.querySelector('#tshirt-div');
        if (!node) {
            return;
        }

        const capture = () => {
            domtoimage.toPng(node).then((dataUrl) => {
                // Remove any previously saved image to avoid duplicates
                document.querySelectorAll('.design_image_doc').forEach(el => el.remove());

                const img = new Image();
                img.classList.add("design_image_doc", "d-none");
                img.src = dataUrl;
                document.body.appendChild(img);

                const designInput = this.el.querySelector('#design_image_input') || document.querySelector('#design_image_input');
                if (designInput) {
                    designInput.value = dataUrl;
                }

                this.services.notification.add(
                    'Saved your customized Image! Now you can add it to the cart.',
                    { type: 'success', sticky: false }
                );
            }).catch(() => {
                this.services.notification.add('Could not save design. Please try again.', {
                    type: 'danger',
                });
            });
        };

        if (this.canvas) {
            // Deselect all objects — requestRenderAll() uses requestAnimationFrame,
            // so we wait 100ms via setTimeout before capturing the screenshot.
            this.canvas.discardActiveObject();
            this.canvas.requestRenderAll();
            setTimeout(capture, 100);
        } else {
            capture();
        }
    }

    addProductDesign() {
        const designBody = this.el.querySelector('.product_design_body');
        if (!designBody) {
            return;
        }

        const isHidden = designBody.classList.toggle('d-none');
        if (!isHidden) {
            designBody.scrollIntoView({ behavior: 'smooth' });
        }
    }
}

registry.category('public.interactions').add(
    'website_product_customization.canvas_widget',
    CanvasWidget
);
