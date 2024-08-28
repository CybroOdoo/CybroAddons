/** @odoo-module */
import publicWidget from '@web/legacy/js/public/public_widget';

    publicWidget.registry.AttributeSelection = publicWidget.Widget.extend({
        selector: '.attr_container',
        events: {
            'click .variant_attribute': '_onClickAttribute'
        },


//        /**
//         * Initializes the widget and enables the first visible attribute.
//         */
          start() {
            this.enableFirstVisibleAttribute();
            return this._super(...arguments);
          },
//        /**
//         * Enables the first visible attribute and selects the only value of each hidden attribute.
//         */
        enableFirstVisibleAttribute: function () {
            const variantAttributes = document.querySelectorAll('.attr_container ul li.variant_attribute');
            var firstVisibleAttribute;
            variantAttributes.forEach(function (varAttr) {
                if (!(firstVisibleAttribute) && !varAttr.classList.contains('d-none')) {
                    firstVisibleAttribute = varAttr;
                }
                if (firstVisibleAttribute) {
                    firstVisibleAttribute.classList.remove('disabled');
                }
                // "checking/selecting" the only value of each of the hidden attributes
                if (varAttr.classList.contains('d-none')) {
                    varAttr.querySelectorAll('input[type="radio"], option').forEach(function (child) {

                        if (child.tagName === 'OPTION') {
                            child.setAttribute('selected', true);
                        } else if (child.tagName === 'INPUT') {
                            child.checked = true;
                        }
                    });
                }
            });
        },

        /**
         * Handles the click event on a variant attribute.
         *
         * @param {Event} ev - The click event.
         */
        _onClickAttribute: function (ev) {
            var clickedElement = ev.target;
            if (clickedElement.classList.contains('js_variant_change')) {
                var variantAttribute = clickedElement.closest('.variant_attribute');
                var nxtSibling = variantAttribute.nextElementSibling;
                var nxtVisibleSibling = this._getNxtVisibleSibling(nxtSibling);
                if (nxtVisibleSibling) {
                    nxtVisibleSibling.classList.remove('disabled');
                }
            }
        },

        /**
         * Gets the next visible sibling of a given element.
         *
         * @param {Element} nextSibling - The next sibling element.
         * @returns {Element|boolean} - The next visible sibling or false if none found.
         */
        _getNxtVisibleSibling: function (nextSibling) {
            if (nextSibling && nextSibling.classList.contains('d-none')) {
                let nxtSib = nextSibling.nextElementSibling;
                if (nxtSib) {
                    return this._getNxtVisibleSibling(nxtSib);
                } else {
                    return false;
                }
            }
            return nextSibling;
        }
    });
//});