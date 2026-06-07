/** @odoo-module **/

export class MapArchParser {
    parse(arch, relatedModels, resModel) {
        // Default fields if not specified in XML.
        // Note: `enterprise/web_map` RelaxNG doesn't allow custom `lat_field` / `lng_field` /
        // `address_field` attributes. Instead we encode these values using `<field>` children.
        const defaultLatField = "partner_latitude";
        const defaultLngField = "partner_longitude";
        const defaultAddressField = "contact_address";
        const fields = arch.getElementsByTagName("field");
        const byString = {};
        for (const field of fields) {
            const label = (field.getAttribute("string") || "").toLowerCase();
            const name = field.getAttribute("name");
            if (label && name) {
                byString[label] = name;
            }
        }
        const latField = byString["latitude"] || defaultLatField;
        const lngField = byString["longitude"] || defaultLngField;
        const addressField = byString["address"] || defaultAddressField;
        // Schema-allowed attribute:
        // - `res_partner="<m2o_field_name>"` for related partners
        // - `res_partner="id"` for direct partners
        const resPartner = arch.getAttribute("res_partner");
        const partnerField = resPartner && resPartner !== "id" ? resPartner : null;
        return {
            latField,
            lngField,
            addressField,
            partnerField,
        };
    }
}
