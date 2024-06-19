/** @odoo-module **/
import { GraphModel } from "@web/views/graph/graph_model";
import { registry } from "@web/core/registry";
export class BurnupChartModel extends GraphModel {
    constructor() {
        super(...arguments);
        this.modelName = "project.task.burnup.chart.report";
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
        metaData.measures.__completed.string = this.env._t('Completed Tasks');
        return super._loadDataPoints(metaData);
    }
}
// Register the model with the Odoo registry
registry.category("models").add("burnup_chart_model", BurnupChartModel);
