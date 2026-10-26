import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class VariantSelection extends Interaction {
    static selector = ".o_wsale_product_page_variants";

    dynamicContent = {
        _root: {
            "t-on-change": this._onVariantChange,
            "t-on-click": this._onClick,
        },
    };

    start() {
        this._setupInitialState();
    }

    /**
     * Sets up initial state and handles hidden attributes.
     * Only enables the first visible variant; disables subsequent ones.
     */
    _setupInitialState() {
        const variants = Array.from(
            this.el.querySelectorAll("li.variant_attribute, li[name='variant_attribute']")
        );
        if (!variants.length) {
            return;
        }

        // Handle hidden attributes first (auto-select values)
        variants
            .filter((variant) => variant.classList.contains("d-none"))
            .forEach((hiddenVariant) => {
                hiddenVariant
                    .querySelectorAll('input[type="radio"], select option')
                    .forEach((input) => {
                        if (input.tagName === "OPTION") {
                            input.selected = true;
                        } else {
                            input.checked = true;
                        }
                    });
            });

        // Handle visible variants
        const visibleVariants = variants.filter((v) => !v.classList.contains("d-none"));

        // Enable the first visible variant, disable all subsequent visible variants
        visibleVariants.forEach((variant, index) => {
            if (index === 0) {
                this._enableVariant(variant);
            } else {
                this._disableVariant(variant);
            }
        });
    }

    /**
     * Handles clicks on options/labels to ensure sequential progression
     * even when clicking an already-selected value.
     * @param {MouseEvent} ev
     */
    _onClick(ev) {
        const target = ev.target;
        if (!target) {
            return;
        }

        const optionEl = target.closest(
            "input.js_variant_change, label.css_attribute_color, label[name^='o_wsale_attribute_'], .o_variant_pills, label.radio_input_value, .form-check"
        );
        if (!optionEl) {
            return;
        }

        this._onVariantChange(ev);
    }

    /**
     * Handles variant selection changes sequentially.
     * @param {Event|Object} ev
     */
    _onVariantChange(ev) {
        const target = ev.target;
        if (!target) {
            return;
        }

        const currentVariant = target.closest("li.variant_attribute, li[name='variant_attribute']");
        if (!currentVariant) {
            return;
        }

        // Ignore if current variant is disabled
        if (currentVariant.classList.contains("disabled")) {
            return;
        }

        const input = (target.classList && target.classList.contains("js_variant_change"))
            ? target
            : target.closest(".js_variant_change") || currentVariant.querySelector("input:checked, select");

        if (input) {
            this._updateHighlight(input);
        }

        // Find and enable next visible variant
        const nextVariant = this._getNextVisibleVariant(currentVariant);
        if (nextVariant) {
            this._enableVariant(nextVariant);
        } else {
            // If last variant reached, enable all visible variants for editing
            const allVisible = this.el.querySelectorAll(
                "li.variant_attribute:not(.d-none), li[name='variant_attribute']:not(.d-none)"
            );
            allVisible.forEach((variant) => this._enableVariant(variant));
        }
    }

    /**
     * Finds the next visible variant line in the list.
     * @param {Element} currentVariant
     * @returns {Element|null}
     */
    _getNextVisibleVariant(currentVariant) {
        let next = currentVariant.nextElementSibling;
        while (next && next.classList.contains("d-none")) {
            next = next.nextElementSibling;
        }
        return next;
    }

    /**
     * Updates highlight state for selected variant (colors, images, radio labels).
     * @param {Element} input
     */
    _updateHighlight(input) {
        const container = input.closest("li.variant_attribute, li[name='variant_attribute']");
        if (!container) {
            return;
        }

        if (input.closest(".css_attribute_color")) {
            container.querySelectorAll(".css_attribute_color").forEach((el) => {
                el.classList.toggle("active", el === input.closest(".css_attribute_color"));
            });
        } else if (input.closest(".css_attribute_image, .css_attribute_thumbnail")) {
            container
                .querySelectorAll(".css_attribute_image, .css_attribute_thumbnail")
                .forEach((el) => {
                    el.classList.toggle(
                        "active",
                        el === input.closest(".css_attribute_image, .css_attribute_thumbnail")
                    );
                });
        } else if (input.type === "radio") {
            container.querySelectorAll("label").forEach((label) => {
                label.classList.toggle("active", label === input.closest("label"));
            });
        }
    }

    /**
     * Enables a variant line and its inputs/selects.
     * @param {Element} variant
     */
    _enableVariant(variant) {
        variant.classList.remove("disabled");
        variant.querySelectorAll("input, select").forEach((input) => {
            input.disabled = false;
            if (input.checked || input.selected) {
                this._updateHighlight(input);
            }
        });
    }

    /**
     * Disables a variant line and its inputs/selects.
     * @param {Element} variant
     */
    _disableVariant(variant) {
        variant.classList.add("disabled");
        variant.querySelectorAll("input, select").forEach((input) => {
            input.disabled = true;
        });
    }
}

registry.category("public.interactions").add("website_sale_variant_selection.variant_selection", VariantSelection);
