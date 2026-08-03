/** @odoo-module **/

import { Model } from "@web/model/model";
import { KeepLast } from "@web/core/utils/concurrency";

export class MapModel extends Model {
    setup(params, services) {
        this.keepLast = new KeepLast();
        this.resModel = params.resModel;
        this.fields = params.fields;
        this.config = params.config || {}; // Capture custom config
        this.metaData = {};
        this.records = [];  // Will hold the data
    }

    async load(params) {
        this.metaData = {
            ...this.metaData,
            ...params,
        };

        // Use configured fields from props (archInfo) if available, or defaults
        const baseLatField = this.config.latField || "partner_latitude";
        const baseLngField = this.config.lngField || "partner_longitude";
        const baseAddressField = this.config.addressField || "contact_address";
        const partnerField = this.config.partnerField;

        const domain = params.domain || this.metaData.domain || [];
        const limit = params.limit || this.metaData.limit || 80;
        const offset = params.offset || this.metaData.offset || 0;

        try {
            let result;

            if (partnerField) {
                // When partner_field is specified, we need to fetch partner data separately
                // because searchRead doesn't support dotted notation like "partner_id.partner_latitude"

                // First, fetch the main records with partner_id
                result = await this.keepLast.add(
                    this.orm.searchRead(this.resModel, domain, [partnerField, "display_name"], {
                        limit: limit,
                        offset: offset,
                    })
                );

                // Extract unique partner IDs
                const partnerIds = [...new Set(
                    result
                        .map(r => r[partnerField] && r[partnerField][0])
                        .filter(id => id)
                )];

                if (partnerIds.length > 0) {
                    // Fetch partner data with coordinates
                    const partners = await this.orm.searchRead(
                        "res.partner",
                        [["id", "in", partnerIds]],
                        [baseLatField, baseLngField, baseAddressField, "id"]
                    );

                    // Create a map of partner data
                    const partnerMap = {};
                    partners.forEach(p => {
                        partnerMap[p.id] = p;
                    });

                    // Merge partner data into records
                    result.forEach(record => {
                        const partnerId = record[partnerField] && record[partnerField][0];
                        if (partnerId && partnerMap[partnerId]) {
                            const partner = partnerMap[partnerId];
                            // Store coordinates directly on the record for easy access
                            record[`${partnerField}.${baseLatField}`] = partner[baseLatField];
                            record[`${partnerField}.${baseLngField}`] = partner[baseLngField];
                            record[`${partnerField}.${baseAddressField}`] = partner[baseAddressField];
                        }
                    });
                }

                // Store the constructed field paths
                this.metaData.latField = `${partnerField}.${baseLatField}`;
                this.metaData.lngField = `${partnerField}.${baseLngField}`;
                this.metaData.addressField = `${partnerField}.${baseAddressField}`;
            } else {
                // Direct fields - fetch normally
                result = await this.keepLast.add(
                    this.orm.searchRead(this.resModel, domain, [baseLatField, baseLngField, baseAddressField, "display_name"], {
                        limit: limit,
                        offset: offset,
                    })
                );

                this.metaData.latField = baseLatField;
                this.metaData.lngField = baseLngField;
                this.metaData.addressField = baseAddressField;
            }

            // Fetch Count separately
            const count = await this.orm.searchCount(this.resModel, domain);

            this.metaData.count = count;
            this.metaData.limit = limit;
            this.metaData.offset = offset;
            this.records = result;
        } catch (error) {
            console.error("Map view: Error fetching records with coordinates", error);
            // If field fetch fails, try with just display_name
            const result = await this.keepLast.add(
                this.orm.searchRead(this.resModel, domain, ["display_name"], {
                    limit: limit,
                    offset: offset,
                })
            );

            const count = await this.orm.searchCount(this.resModel, domain);

            this.metaData.count = count;
            this.metaData.limit = limit;
            this.metaData.offset = offset;
            this.metaData.latField = partnerField ? `${partnerField}.${baseLatField}` : baseLatField;
            this.metaData.lngField = partnerField ? `${partnerField}.${baseLngField}` : baseLngField;
            this.metaData.addressField = partnerField ? `${partnerField}.${baseAddressField}` : baseAddressField;
            this.records = result;
        }
    }
}
