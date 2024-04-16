/** @odoo-module */
import { useService } from "@web/core/utils/hooks";
import { SearchModel } from "@web/search/search_model";
import { _t } from "@web/core/l10n/translation";

// Define a custom search model 'VelocityChartSearchModel' that extends 'SearchModel'
export class VelocityChartSearchModel extends SearchModel {
    /**
     * @override
     */
    setup(services) {
        this.notificationService = useService("notification");
        super.setup(...arguments);
    }
    /**
     * @override
     */
    async load(config) {
        await super.load(...arguments);
        // Store date searchItemId in the SearchModel for reuse in other functions.
        for (const searchItem of Object.values(this.searchItems)) {
            if (searchItem.type === 'dateGroupBy') {
                if (this.dateSearchItemId) {
                    return;
                }
                if (searchItem.fieldName === 'date') {
                    this.dateSearchItemId = searchItem.id;
                }
            }
        }
    }
    /**
     * @override
     */
    toggleDateGroupBy(searchItemId, intervalId) {
        // Ensure that there is always one and only one date group by selected.
        if (searchItemId === this.dateSearchItemId) {
            let filtered_query = [];
            let triggerNotification = false;
            for (const queryElem of this.query) {
                if (queryElem.searchItemId !== searchItemId) {
                    filtered_query.push(queryElem);
                } else if (queryElem.intervalId === intervalId) {
                    triggerNotification = true;
                }
            }
            if (filtered_query.length !== this.query.length) {
                this.query = filtered_query;
                if (triggerNotification) {
                    this._addGroupByNotification(_t("Date"));
                }
            }
        }
        super.toggleDateGroupBy(...arguments);
    }
    /**
     * Adds a notification relative to the group by constraint of the Velocity Chart.
     * @param fieldName The field name(s) the notification has to be related to.
     * @private
     */
    _addGroupByNotification(fieldName) {
        const notif = _t("The Velocity Chart must be grouped by");
        this.notificationService.add(
            `${notif} ${fieldName}`,
            { type: "danger" }
        );
    }
    /**
     * @override
     */
    async _notify() {
        // Ensure that we always group by date
        let dateIndex = -1;
        for (const [index, queryElem] of this.query.entries()) {
            if (dateIndex !== -1) {
                break;
            }
            if (queryElem.searchItemId === this.dateSearchItemId) {
                dateIndex = index;
            }
        }
        if (dateIndex > 0) {
            this.query.splice(0, 0, this.query.splice(dateIndex, 1)[0]);
        }
        await super._notify(...arguments);
    }
}
