/** @odoo-module **/

/**
 * Extracts the font name from a Google Fonts URL.
 * @param {string} url - a fonts.google.com specimen URL or a css/css2 URL.
 * @returns {string|null} the font name, or null when none is found.
 */
export function getFontNameFromUrl(url) {
    const match = url.match(/[?&]family=([^&:]+)/) || url.match(/specimen\/([^/?#]+)/);
    return match ? decodeURIComponent(match[1].replace(/\+/g, " ")) : null;
}