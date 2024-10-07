/** @odoo-module **/
import { Dialog } from "@web/core/dialog/dialog";
const { useRef, onWillStart, xml ,onMounted} = owl;
/**
 * VisualEditor class for creating a visual editor dialog.
 * @extends Dialog
 */
export class VisualEditor extends Dialog{
    setup(element) {
        this.element = element;
        var options = {};
        options.title = 'Visual Editor';
        options.size = 'medium';
        var self = this;
        options.buttons = [];
        options.buttons.push({text: "Apply", classes: "btn-primary", click: function (e) {
            self._applyStyle();
        }});
        options.buttons.push({text: "Cancel", close: true});
        options.buttons.push({text: "Advanced", classes: "btn-primary", click: function (e) {
            self._openAdvanced();
        }});
        this._super(element, options);
    }
    async onWillStart() {
        this.$el[0].append(this.element[0].cloneNode(true));
        this.preview = this.$(this.$el[0].firstChild);
        this.tools = this.$el[2];
        for (var child of this.tools.children) {
            if (child.tagName in ['INPUT', 'SELECT']) {
                var val = this.element.css(child.id);
                if (val && val.includes('rgb') && val.match(/\d+/g) !== null) {
                    var rgb = val.match(/\d+/g);
                    var hex = rgbToHex(rgb[0], rgb[1], rgb[2]);
                    val = hex;
                } else if (val && val.includes('px')) {
                    val = val.replace('px', '');
                    if (val.includes(' ')) {
                        val = val.split(' ')[0];
                    }
                }
                if ($(child).data('unit') == '%') {
                    val = getPercentage(val);
                }
                $(child).val(val);
            }
        }
    }
    /**
     * Handles input change event to update preview style.
     * @param {Event} e - The input change event.
     */
    _onChangeInput(e) {
        var input = e.target;
        var value = input.value;
        if (input.dataset.unit) {
            value += input.dataset.unit;
        }
        var name = input.id;
        var add = true;
        var style = this.preview.attr('style') ? this.preview.attr('style').split(';') : [];
        if (style) {
            for (var i = 0; i < style.length; i++) {
                var s = style[i].split(':');
                if (s[0] == name) {
                    style[i] = `${name}: ${value}`;
                    add = false;
                    break;
                }
            }
        }
        if(add) {
            style.push(`${name}: ${value}`);
        }
        style = style.join(';');
        this.preview.attr('style', style);
    }
    /**
     * Applies the style from preview to the target element.
     */
     _applyStyle() {
        var style = this.preview.attr('style');
        this.element.attr('style', style);
    }
}
/**
 * Converts a component value to hexadecimal representation.
 * @param {number} c - The component value.
 * @returns {string} The hexadecimal representation.
 */
function componentToHex(c) {
       c = parseInt(c);
      var hex = c.toString(16);
      return hex.length == 1 ? "0" + hex : hex;
    }
    /**
     * Converts RGB components to hexadecimal color code.
     * @param {number} r - The red component.
     * @param {number} g - The green component.
     * @param {number} b - The blue component.
     * @returns {string} The hexadecimal color code.
     */
    function rgbToHex(r, g, b) {
      return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
    }
    /**
     * Calculates percentage value relative to screen width.
     * @param {number} value - The value to convert to percentage.
     * @returns {number} The calculated percentage value.
     */
     function getPercentage(value) {
        var screenWidth = window.screen.width;
        var perc = ( screenWidth - value ) / screenWidth;
        return perc;
    }

    return VisualEditor;
