/** @odoo-module **/

import { describe, expect, test } from "@odoo/hoot";
import { click, queryFirst } from "@odoo/hoot-dom";
import { animationFrame } from "@odoo/hoot-mock";
import {
    defineModels,
    fields,
    findComponent,
    models,
    mountView,
    patchWithCleanup,
} from "@web/../tests/web_test_helpers";

class Partner extends models.Model {
    _name = "res.partner";

    name = fields.Char();
    address = fields.Char();

    _records = [
        { id: 1, name: "Test Partner", address: "Paris, France" },
        { id: 2, name: "Empty Partner", address: "" },
    ];
}

defineModels([Partner]);

/**
 * Safely mocks external Nominatim geocoding requests while preserving
 * Odoo's internal RPC/fetch routing through HOOT and MockServer.
 */
function mockNominatimFetch(customHandlers = {}) {
    const originalFetch = window.fetch;
    patchWithCleanup(window, {
        fetch: async function (input, init) {
            const urlStr = typeof input === "string" ? input : input?.url || String(input);
            if (urlStr.includes("nominatim.openstreetmap.org/search")) {
                const searchResults = customHandlers.search
                    ? customHandlers.search(urlStr)
                    : [{ lat: "48.8566", lon: "2.3522", display_name: "Paris, France" }];
                return new Response(JSON.stringify(searchResults), {
                    status: 200,
                    headers: { "Content-Type": "application/json" },
                });
            }
            if (urlStr.includes("nominatim.openstreetmap.org/reverse")) {
                if (customHandlers.onReverse) {
                    customHandlers.onReverse(urlStr);
                }
                const reverseResult = customHandlers.reverse
                    ? customHandlers.reverse(urlStr)
                    : {
                          display_name: "Rue de la Loi, Belgium",
                          address: {
                              road: "Rue de la Loi",
                              country: "Belgium",
                          },
                      };
                return new Response(JSON.stringify(reverseResult), {
                    status: 200,
                    headers: { "Content-Type": "application/json" },
                });
            }
            return originalFetch.call(this, input, init);
        },
    });
}

describe("geolocation_map_widget", () => {
    describe.current.tags("desktop");

    test("GeoLocationMap renders correctly in edit mode with input, button, and map preview", async () => {
        mockNominatimFetch();

        const view = await mountView({
            type: "form",
            resModel: "res.partner",
            resId: 1,
            arch: `
                <form>
                    <field name="address" widget="geolocation_map"/>
                </form>
            `,
        });

        expect(".o_input_map").toHaveCount(1, {
            message: "Input group container should be rendered",
        });
        expect(".o_input_map input").toHaveCount(1, {
            message: "Input element should be rendered",
        });
        expect(".o_open_map").toHaveCount(1, {
            message: "Open map button with class .o_open_map should be rendered",
        });
        expect("#open_map").toHaveCount(0, {
            message: "Hard-coded id #open_map should not exist in DOM",
        });
        expect(".map-preview").toHaveCount(1, {
            message: "Map preview container should be rendered",
        });

        const comp = findComponent(view, (c) => c.constructor.name === "GeoLocationMap");
        expect(comp).not.toBe(null, {
            message: "GeoLocationMap component instance should be found",
        });
    });

    test("Clicking .o_open_map button opens Google Maps in a new tab", async () => {
        let openedUrl = null;
        patchWithCleanup(window, {
            open: (url) => {
                openedUrl = url;
            },
        });
        mockNominatimFetch();

        await mountView({
            type: "form",
            resModel: "res.partner",
            resId: 1,
            arch: `
                <form>
                    <field name="address" widget="geolocation_map"/>
                </form>
            `,
        });

        await click(".o_open_map");
        expect(openedUrl).not.toBe(null, {
            message: "window.open should be called when open map button is clicked",
        });
        expect(openedUrl).toInclude("google.com/maps/search", {
            message: "Opened URL should target Google Maps search",
        });
    });

    test("Map click in edit mode triggers reverse geocoding and updates record", async () => {
        mockNominatimFetch({
            reverse: () => ({
                display_name: "Rue de la Loi, Belgium",
                address: {
                    road: "Rue de la Loi",
                    country: "Belgium",
                },
            }),
        });

        const view = await mountView({
            type: "form",
            resModel: "res.partner",
            resId: 1,
            arch: `
                <form>
                    <field name="address" widget="geolocation_map"/>
                </form>
            `,
        });

        const comp = findComponent(view, (c) => c.constructor.name === "GeoLocationMap");
        expect(comp).not.toBe(null);

        // Simulate click event on Leaflet map
        if (comp.leafletMap) {
            await comp.leafletMap.fire("click", {
                latlng: { lat: 50.8503, lng: 4.3517 },
            });
            await animationFrame();

            expect(comp.props.record.data.address).toBe(
                "Rue de la Loi, Belgium",
                { message: "Record address field should be updated after map click" }
            );
        }
    });

    test("Map click in readonly mode does NOT update the record", async () => {
        let reverseFetchCalled = false;
        mockNominatimFetch({
            onReverse: () => {
                reverseFetchCalled = true;
            },
        });

        const view = await mountView({
            type: "form",
            resModel: "res.partner",
            resId: 1,
            mode: "readonly",
            arch: `
                <form>
                    <field name="address" widget="geolocation_map" readonly="1"/>
                </form>
            `,
        });

        const comp = findComponent(view, (c) => c.constructor.name === "GeoLocationMap");
        expect(comp).not.toBe(null);
        expect(comp.props.readonly).toBe(true, {
            message: "Widget should have props.readonly = true",
        });

        const initialAddress = comp.props.record.data.address;
        expect(initialAddress).toBe("Paris, France");

        if (comp.leafletMap) {
            await comp.leafletMap.fire("click", {
                latlng: { lat: 50.8503, lng: 4.3517 },
            });
            await animationFrame();

            expect(reverseFetchCalled).toBe(false, {
                message: "Reverse geocoding fetch should NOT be called in readonly mode",
            });
            expect(comp.props.record.data.address).toBe("Paris, France", {
                message: "Record data must remain unchanged when clicking map in readonly mode",
            });
        }
    });

    test("Readonly mode renders formatted address text, open map button, and map container", async () => {
        mockNominatimFetch();

        await mountView({
            type: "form",
            resModel: "res.partner",
            resId: 1,
            mode: "readonly",
            arch: `
                <form>
                    <field name="address" widget="geolocation_map" readonly="1"/>
                </form>
            `,
        });

        expect(".o_input_map").toHaveCount(1, {
            message: "Input group container should be rendered in readonly mode",
        });
        expect(".o_open_map").toHaveCount(1, {
            message: "Open map button should be rendered in readonly mode",
        });
        expect(".map-preview").toHaveCount(1, {
            message: "Map preview container should be rendered in readonly mode",
        });
        expect(".o_input_map input").toHaveCount(0, {
            message: "Input field should not be rendered in readonly mode",
        });
    });
});
