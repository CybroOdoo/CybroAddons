/** @odoo-module **/
import { Component } from "@odoo/owl";
import { ThemeStudioWidget } from "./ThemeStudioWidget";
export class Tool extends ThemeStudioWidget {
    constructor() {
        super(...arguments);
        this.options = ['color', 'font-family', 'font-size', 'font-style', 'width', 'height', 'border', 'padding', 'shadow', 'align'];
        this.remove = ['--'];
        this.object = this.props.object;
        this.tool = null;
    }

    async willStart() {
        await super.willStart();
        this.render();
    }
    /**
     * Renders the tool component.
     * @returns {Array} The generated style options.
     */
    render() {
        if (this.object && !this.tool) {
            const style = this.getStyle(this.object[0].dataset.class, this.options, this.remove);
            this.tool = style;
            return style;
        } else {
            return this.tool;
        }
    }
    /**
     * Gets the CSS style of a given class name, filtering out unwanted rules.
     * @param {string} className - The CSS class name.
     * @param {string[]} allowed - The allowed CSS properties.
     * @param {string[]} remove - The CSS properties to be removed.
     * @returns {Array} The filtered style options.
     */
    getStyle(className, allowed, remove) {
        const rules = window.getComputedStyle($(`.${className}`)[0]);
        const rules_list = [];
        const rules_value = [];
        for (const rule of rules) {
            const alw = allowed.some(w => rule.includes(w));
            const rmv = remove.some(w => rule.includes(w));
            const exist = rules_list.some(w => w === rule);
            if (!exist && !rmv) {
                rules_list.push(rule);
                rules_value.push(rules[rule]);
            }
        }
        return rules_list.map(function (rule, index) {
            if (rule.includes('color')) {
                const color = rules_value[index] != undefined ? rules_value[index] : '#000000';
                if (color.includes('rgb') && color.match(/\d+/g) !== null) {
                    const rgb = color.match(/\d+/g);
                    const hex = rgbToHex(rgb[0], rgb[1], rgb[2]);
                    const value = hex;
                } else {
                    const value = color;
                }
                return [rule, 'color', value];
            } else if (rules_value[index].includes('px')) {
                return [rule, 'range', rules_value[index]];
            } else {
                return [rule, 'text', rules_value[index]];
            }
        });
    }
}

function componentToHex(c) {
    c = parseInt(c);
    const hex = c.toString(16);
    return hex.length == 1 ? "0" + hex : hex;
}

function rgbToHex(r, g, b) {
    return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
}
