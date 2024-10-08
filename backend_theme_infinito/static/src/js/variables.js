/** @odoo-module **/
import { useState } from "@odoo/owl";
/**
 * Object containing CSS variable names and their corresponding ranges for generating color variations.
 * @type {Object.<string, number[]>}
 */
const variables = {
    "--bg_white": [1, 1],
    "--bg_black": [5, 1],
    "--bg_grey": [1, 20],
    "--bg_grey_white": [1, 10],
    "--dark_bg_grey": [1, 30],
    "--light_bg_color": [1, 12],
    "--nav_bar_color": [5, 20],
    "--nav_font_color": [1, 1],
    "--primary_accent": [2, 20],
    "--primary_hover": [2, 10],
    "--primary_btn_hover": [2, 10],
    "--primary_btn_hover_border": [2, 1],
    "--dark_primary_accent": [2, 10],
    "--darker_primary_accent": [2, 1],
    "--light_primary_accent": [2, 30],
    "--lighter_primary_accent": [1, 15],
    "--secondary_accent": [3, 1],
    "--secondary_color": [3, 10],
    "--secondary_btn": [3, 15],
    "--secondary_btn_hover": [3, 20],
    "--secondary_btn_hover_border": [3, 25],
    "--dark_secondary_btn_hover_border": [3, 30],
    "--light_secondary_btn": [1, 15],
    "--custom_green": [2, 30],
    "--success-color": [2, 5],
    "--dark_success-color": [1, 35],
    "--success-bg-color": [1, 30],
    "--light_custom_green": [2, 40],
    "--custom_red": [4, 10],
    "--custom_red_hover": [4, 20],
    "--custom_red_hover_border": [4, 18],
    "--dark_custom_red_hover_border": [4, 13],
    "--danger-bg-color": [1, 5],
    "--danger-color": [4, 1],
    "--dark_danger-color": [1, 5],
    "--custom_rose": [4, 25],
    "--bg_blue": [2, 40],
    "--bg_blue_hover": [2, 45],
    "--dark_bg_blue_hover": [2, 50],
    "--info_color": [2, 55],
    "--info-color": [2, 35],
    "--info-bg-color": [1, 25],
    "--dark_info-color": [1, 20],
    "--warning-bg-color": [1, 5],
    "--warning-color": [5, 1],
    "--bg_yellow": [5, 10],
    "--bg_yellow_hover": [5, 80],
    "--dark_bg_yellow_hover": [5, 80],
    "--dark_warning-color": [1, 5],
};
/**
 * Array of arrays containing color codes for different color themes.
 * @type {string[][]}
 */
const colors = [
    ['F9F9F8', 'E29E51', '94B1B3', '9A6B59', '2A373D'],
    ['F4F6F6', '7D807E', '9DACC2', '738093', '34383A'],
    ['EEF1F0', 'AFA378', '82AAAE', '937D54', '3D604C'],
    ['FBF9F8', 'A9A3C0', '7BB3D5', '31A7DD', '242E4D'],
    ['fefefe', 'EEE2DC', 'BAB2B5', '123C69', 'AC3B61'],
    ['fefefe', '116466', 'D9B08C', 'FFCB9A', 'D1E8E2'],
    ['EFE9E7', '997C55', 'C39247', '93391E', '121213'],
    ['EDECE7', '98A1AD', 'F35256', 'C69182', '252029'],
    ['fefefe', 'D1D2CD', '9D8FB9', 'BEBFE8', '385EA9'],
    ['F3F0F0', '797075', '986351', '7B4E46', '2C2B30'],
    ['F9F8F8', '93BBB8', '2BA699', 'A59D4E', '335A43'],
];
/**
 * Function to generate a color based on the given base color and variation.
 * @param {string} cwith2 - The base color code (6 digits hex).
 * @param {number} aaa - The variation percentage.
 * @returns {string} The generated color code.
 */
function to_color(cwith2, aaa) {
    const p1_x = Math.round(aaa * 255 / 100);
    const p2_x = Math.round(aaa * 255 / 100);
    const p3_x = Math.round(aaa * 255 / 100);
    const r = parseInt(cwith2.substring(0,2), 16);
    const g = parseInt(cwith2.substring(2,4), 16);
    const b = parseInt(cwith2.substring(4,6), 16);
    const r_r = Math.abs(r - p1_x);
    const r_g = Math.abs(g - p2_x);
    const r_b = Math.abs(b - p3_x);
    const result = rgbToHex(r_r, r_g, r_b);
    return result;
}
/**
 * Function to convert a component value to hexadecimal.
 * @param {number} c - The component value.
 * @returns {string} The hexadecimal representation.
 */
function componentToHex(c) {
    const hex = c.toString(16);
    return hex.length == 1 ? "0" + hex : hex;
}
/**
 * Function to convert RGB components to hexadecimal color code.
 * @param {number} r - The red component.
 * @param {number} g - The green component.
 * @param {number} b - The blue component.
 * @returns {string} The hexadecimal color code.
 */
function rgbToHex(r, g, b) {
    return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
}

export { variables, colors, to_color };
