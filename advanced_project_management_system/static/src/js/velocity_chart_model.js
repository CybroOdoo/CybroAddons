/** @odoo-module **/
import { GraphModel } from "@web/views/graph/graph_model";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

/**
 * Model specifically for handling velocity chart reports.
 */
export class VelocityChartModel extends GraphModel {
    constructor() {
        super(...arguments);
        this.modelName = "project.velocity.chart.report";
    }
    /**
     * @protected
     * @override
     */
    async _loadDataPoints(metaData) {
     if (!metaData.measures) {
            metaData.measures = {};
        }
        if (!metaData.measures.__completed) {
            metaData.measures.__completed = {};
        }
        metaData.measures.__completed.string = _t('Done Tasks');
    return super._loadDataPoints(metaData);
}
}
registry.category("models").add("velocity_chart_model", VelocityChartModel);
