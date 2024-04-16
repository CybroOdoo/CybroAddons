/** @odoo-module **/
import { BurnupChartModel } from "./burnup_chart_model";
import { graphView } from "@web/views/graph/graph_view";
import { registry } from "@web/core/registry";
import { BurnupChartSearchModel } from "./burnup_chart_search_model";

const viewRegistry = registry.category("views");

// Define a Burnup Chart graph view
const burnupChartGraphView = {
  ...graphView,
  buttonTemplate: "project.BurnupChartView.Buttons",
  hideCustomGroupBy: true,
  Model: BurnupChartModel,
  searchMenuTypes: graphView.searchMenuTypes.filter(menuType => menuType !== "comparison"),
  SearchModel: BurnupChartSearchModel,
};

// Register the Burnup Chart view in the viewRegistry
viewRegistry.add("burnup_chart", burnupChartGraphView);
