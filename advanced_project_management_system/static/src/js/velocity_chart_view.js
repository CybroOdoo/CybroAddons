/** @odoo-module **/
import { VelocityChartModel } from "./velocity_chart_model";
import { graphView } from "@web/views/graph/graph_view";
import { registry } from "@web/core/registry";
import { VelocityChartSearchModel } from "./velocity_chart_search_model";
const viewRegistry = registry.category("views");
// Define a Velocity Chart graph view
const velocityChartGraphView = {
  ...graphView,
  buttonTemplate: "project.VelocityChartView.Buttons",
  hideCustomGroupBy: true,
  Model: VelocityChartModel,
  searchMenuTypes: graphView.searchMenuTypes.filter(menuType => menuType !== "comparison"),
  SearchModel: VelocityChartSearchModel,
};
viewRegistry.add("velocity_chart", velocityChartGraphView);
