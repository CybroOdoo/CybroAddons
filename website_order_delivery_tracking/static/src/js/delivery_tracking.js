import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";

export class OrderTrackingWidget extends Interaction {
    static selector = ".tracking_templates";

    dynamicContent = {
        "#trackingInputBtn": {
            "t-on-click": this._onDeliveryTracking,
        },
        "#TrackingUpdate": {
            "t-on-click": this._onDeliveryTrackingUpdate,
        },
        "#trackingNumberInput": {
            "t-on-input": this._onTrackingNumberInput,
        },
    };

    _showModal(selector) {
        const modal = this.el.querySelector(selector);
        if (modal) {
            window.Modal.getOrCreateInstance(modal).show();
        }
    }

    _onTrackingNumberInput() {
        const input = this.el.querySelector("#trackingNumberInput");
        const table = this.el.querySelector("#trackedTableDetails");

        if (!input?.value) {
            table?.style.setProperty("display", "none");
        }
    }

    async _onDeliveryTracking(ev) {
        ev.preventDefault();
        const trackingNumber =
            this.el.querySelector("#trackingNumberInput")?.value;

        const data = await rpc("/tracking/details/update", {
            input_data: trackingNumber,
        });

        const trackedTableDetails =
            this.el.querySelector("#trackedTableDetails");
        const noRecordsMsg = this.el.querySelector("#noRecordsMsg");

        if (data.length > 0) {
            trackedTableDetails.replaceChildren(this._buildTable(data));
            trackedTableDetails.style.display = "";
            noRecordsMsg?.style.setProperty("display", "none");
        } else {
            this._showModal("#NoRecordsApiKey");
            trackedTableDetails?.style.setProperty("display", "none");
        }
    }

    /**
     * Build the table of the tracked deliveries. The values are set as
     * text, so the data sent by the delivery partners is never rendered
     * as HTML.
     */
    _buildTable(data) {
        const table = document.createElement("table");
        table.className = "table";

        const headRow = document.createElement("tr");
        for (const title of [_t("Sale Order"), _t("Delivery Partner"), _t("Status")]) {
            const th = document.createElement("th");
            th.scope = "col";
            th.textContent = title;
            headRow.appendChild(th);
        }
        const thead = document.createElement("thead");
        thead.className = "thead-dark";
        thead.appendChild(headRow);

        const tbody = document.createElement("tbody");
        for (const row of data) {
            const tr = document.createElement("tr");
            for (const value of row.slice(1)) {
                const td = document.createElement("td");
                td.textContent = value;
                tr.appendChild(td);
            }
            tbody.appendChild(tr);
        }

        table.append(thead, tbody);
        return table;
    }

    async _onDeliveryTrackingUpdate(ev) {
        ev.preventDefault();

        const trackingNumber =
            this.el.querySelector("#trackingNumber")?.value;
        const apiKey = this.el.querySelector("#apiKey")?.value;
        const trackingStatus =
            this.el.querySelector("#trackingStatus")?.value;

        const data = await rpc("/tracking/details/edit", {
            api_key: apiKey,
            tracking_number: trackingNumber,
            tracking_status: trackingStatus,
        });

        // The controller returns [] on failure and the status text
        // (possibly empty) on success.
        this._showModal(
            Array.isArray(data) ? "#failedApiKey" : "#successApiKey"
        );
    }
}

registry
    .category("public.interactions")
    .add(
        "website_order_delivery_tracking.OrderTrackingWidget",
        OrderTrackingWidget
    );
