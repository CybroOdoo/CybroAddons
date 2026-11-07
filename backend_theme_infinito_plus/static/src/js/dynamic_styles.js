/** @odoo-module **/
const LINK_ID = "infinito-plus-dynamic-styles";

export function loadDynamicStyles() {
    let link = document.getElementById(LINK_ID);
    if (!link) {
        link = document.createElement("link");
        link.id = LINK_ID;
        link.rel = "stylesheet";
        document.head.appendChild(link);
    }
    link.href = `/backend_theme_infinito_plus/dynamic_styles.css?t=${Date.now()}`;
}

loadDynamicStyles();