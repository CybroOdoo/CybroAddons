/** @odoo-module **/
/**
 * UI tours for the collection maps. Run by wm_collection/tests/test_ui_tours.py
 * (the tests seed the data). They cover:
 *  - XSS: names/addresses with HTML are shown as text in map popups;
 *  - popup buttons fire once, however often the popup was opened;
 *  - the route map redraws after "Add to Route" without reloading the page;
 *  - the collection point map (wm_map view type) opens and renders markers.
 */
import { registry } from "@web/core/registry";

const MAP_FIELD = ".o_field_widget[name=route_map_data]";

function assertNoInjectedMarkup() {
    const popup = document.querySelector(".leaflet-popup-content");
    if (!popup) {
        throw new Error("No map popup is open");
    }
    if (popup.querySelector("img[src='x']") || window.__wm_xss) {
        throw new Error("Unescaped HTML was rendered in the map popup");
    }
}

async function openPopupsRepeatedly(selector, times) {
    const marker = document.querySelector(selector);
    for (let i = 0; i < times; i++) {
        marker.click();
        await new Promise((resolve) => setTimeout(resolve, 150));
        document.querySelector(".leaflet-popup-close-button")?.click();
        await new Promise((resolve) => setTimeout(resolve, 100));
    }
    marker.click();
}

registry.category("web_tour.tours").add("wm_route_map_tour", {
    steps: () => [
        {
            content: "Open the Map tab of the route",
            trigger: ".o_notebook .nav-link:contains(Map)",
            run: "click",
        },
        {
            content: "The route's three stops are drawn",
            trigger: `${MAP_FIELD}:contains(3 Stops) .leaflet-marker-icon.wm-route-marker-container`,
        },
        {
            content: "Open the popup of the stop whose name contains HTML",
            trigger: `${MAP_FIELD} .leaflet-marker-icon.wm-route-marker-container`,
            run: "click",
        },
        {
            content: "The HTML in the name is shown as text, not rendered",
            trigger: ".leaflet-popup-content:contains(onerror)",
            run: assertNoInjectedMarkup,
        },
        {
            content: "Open the other point's popup several times, then keep it open",
            trigger: `${MAP_FIELD} .leaflet-marker-icon.wm-other-marker-container`,
            run: () => openPopupsRepeatedly(`${MAP_FIELD} .leaflet-marker-icon.wm-other-marker-container`, 3),
        },
        {
            content: "Add the point to the route",
            trigger: ".leaflet-popup-content .js_add_to_route",
            run: "click",
        },
        {
            content: "The map redraws with four stops, without a page reload",
            trigger: `${MAP_FIELD}:contains(4 Stops)`,
        },
    ],
});

registry.category("web_tour.tours").add("wm_collection_point_map_tour", {
    steps: () => [
        {
            content: "Switch the collection points to the map view",
            trigger: ".o_switch_view.o_wm_map",
            run: "click",
        },
        {
            content: "Markers are rendered",
            trigger: ".o_wm_map_view .leaflet-marker-icon, .leaflet-container .leaflet-marker-icon",
        },
        {
            content: "Open the popup of the point whose name contains HTML",
            trigger: ".leaflet-container .leaflet-marker-icon",
            run: () => {
                // The HTML-named point is the only one at its coordinates
                for (const marker of document.querySelectorAll(".leaflet-container .leaflet-marker-icon")) {
                    marker.click();
                    const popup = document.querySelector(".leaflet-popup-content");
                    if (popup && popup.textContent.includes("onerror")) {
                        return;
                    }
                }
                throw new Error("No popup shows the HTML-named point");
            },
        },
        {
            content: "The HTML in the name is shown as text, not rendered",
            trigger: ".leaflet-popup-content:contains(onerror)",
            run: assertNoInjectedMarkup,
        },
    ],
});
