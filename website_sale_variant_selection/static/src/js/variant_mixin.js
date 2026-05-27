/** @odoo-module */
import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.AttributeSelection = publicWidget.Widget.extend({
    selector: '.attr_container',
    events: {
        'change .js_variant_change': '_onVariantChange',
        'click .js_variant_change': '_onVariantChange'
    },

    start() {
        this._setupInitialState();
        return this._super(...arguments);
    },

    /**
     * Sets up initial state and handles hidden attributes
     * @private
     */
    _setupInitialState() {
        const variants = Array.from(this.el.querySelectorAll('li.variant_attribute'));

        // Handle hidden attributes first
        variants.filter(variant => variant.classList.contains('d-none'))
            .forEach(hiddenVariant => {
                // Auto-select values for hidden attributes
                hiddenVariant.querySelectorAll('input[type="radio"], select option').forEach(input => {
                    if (input.tagName === 'OPTION') {
                        input.selected = true;
                    } else {
                        input.checked = true;
                    }
                });
            });

        // Handle visible variants
        const visibleVariants = variants.filter(v => !v.classList.contains('d-none'));

        // Disable all visible variants except the first one
        visibleVariants.forEach((variant, index) => {
            index === 0 ? this._enableVariant(variant) : this._disableVariant(variant);
        });
    },

    /**
     * Handles variant selection changes
     * @private
     * @param {Event} ev
     */
    _onVariantChange(ev) {
        const input = ev.target;
        if (!input.classList.contains('js_variant_change')) {
            return;
        }

        const currentVariant = input.closest('li.variant_attribute');
        if (!currentVariant) {
            return;
        }

        this._updateHighlight(input);

        // Find and enable next visible variant
        const nextVariant = this._getNextVisibleVariant(currentVariant);
        if (nextVariant) {
            this._enableVariant(nextVariant);
        } else {
            // If last variant, enable all for editing
            this.el.querySelectorAll('li.variant_attribute:not(.d-none)')
                .forEach(variant => this._enableVariant(variant));
        }

        ev.stopPropagation();
    },

    /**
     * Finds the next visible variant
     * @private
     * @param {Element} currentVariant
     * @returns {Element|null}
     */
    _getNextVisibleVariant(currentVariant) {
        let next = currentVariant.nextElementSibling;
        while (next && next.classList.contains('d-none')) {
            next = next.nextElementSibling;
        }
        return next;
    },

    /**
     * Updates highlight state for selected variant
     * @private
     * @param {Element} input
     */
    _updateHighlight(input) {
        const container = input.closest('li.variant_attribute');

        if (input.closest('.css_attribute_color')) {
            container.querySelectorAll('.css_attribute_color').forEach(el => {
                el.classList.toggle('active', el === input.closest('.css_attribute_color'));
            });
        } else if (input.type === 'radio') {
            container.querySelectorAll('label').forEach(label => {
                label.classList.toggle('active', label === input.closest('label'));
            });
        }
    },

    /**
     * Enables a variant
     * @private
     * @param {Element} variant
     */
    _enableVariant(variant) {
        variant.classList.remove('disabled');
        variant.querySelectorAll('input, select').forEach(input => {
            input.disabled = false;
            if (input.checked || input.selected) {
                this._updateHighlight(input);
            }
        });
    },

    /**
     * Disables a variant
     * @private
     * @param {Element} variant
     */
    _disableVariant(variant) {
        variant.classList.add('disabled');
        variant.querySelectorAll('input, select').forEach(input => {
            input.disabled = true;
        });
    }
});
