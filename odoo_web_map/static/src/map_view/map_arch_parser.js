/** @odoo-module **/

export class MapArchParser {
    parse(arch, relatedModels, resModel) {
        // Default fields if not specified in XML
        const defaultLatField = "partner_latitude";
        const defaultLngField = "partner_longitude";

        return {
            latField: arch.getAttribute("lat_field") || defaultLatField,
            lngField: arch.getAttribute("lng_field") || defaultLngField,
            addressField: arch.getAttribute("address_field") || "contact_address",
            partnerField: arch.getAttribute("partner_field") || null, // e.g., "partner_id"

        };
    }
}
