import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useChart } from "@web/core/utils/chart_hook";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";

/**
 * Storage dashboard: server, Odoo configuration and database information,
 * and a chart of the models using the most storage
 */
export class StorageDashboard extends Component {
    static template = "storage_dashboard.StorageDashboard";
    props = useProps(standardActionServiceProps);

    chart = useChart(() => this.getChartConfig());

    setup() {
        this.orm = useService("orm");
        this.state = proxy({ info: {}, chartData: { x_data: [], y_data: [] } });
        onWillStart(() => this.loadData());
    }

    async loadData() {
        const [info, chartData] = await Promise.all([
            this.orm.call("storage.usage", "get_info", []),
            this.orm.call("storage.usage", "get_data", []),
        ]);
        this.state.info = info;
        this.state.chartData = chartData;
    }

    getChartConfig() {
        return {
            type: "bar",
            data: {
                labels: this.state.chartData.x_data,
                datasets: [
                    {
                        label: _t("Size Used In MB"),
                        data: this.state.chartData.y_data,
                        borderRadius: 10,
                        backgroundColor: "rgba(39, 232, 232, 0.5)",
                        borderColor: "rgba(39, 232, 232, 1)",
                    },
                ],
            },
            options: { maintainAspectRatio: false },
        };
    }

    get systemRows() {
        const info = this.state.info;
        return [
            [_t("Total Memory"), info.total_memory],
            [_t("Used Memory"), info.used_memory],
            [_t("Available Memory"), info.available_memory],
            [_t("CPU Usage"), info.cpu_usage],
            [_t("Odoo RAM Usage"), info.ram_usage],
            [_t("Operating System"), info.os],
            [_t("Database User"), info.db_user],
        ];
    }

    get limitRows() {
        const info = this.state.info;
        return [
            [_t("Soft Memory Limit"), info.soft_limit],
            [_t("Hard Memory Limit"), info.hard_limit],
            [_t("Transient Age Limit"), info.transient_age_limit],
            [_t("CPU Limit Time"), info.limit_time_cpu],
            [_t("Limit Request"), info.limit_request],
            [_t("Real Limit Time"), info.limit_time_real],
            [_t("HTTP Port"), info.http_port],
        ];
    }

    get databaseRows() {
        const info = this.state.info;
        return [
            [_t("Database Name"), info.db_name],
            [_t("Database Version"), info.db_version],
            [_t("Database Created on"), info.db_date],
            [_t("Database Size"), info.db_size],
            [_t("Total Tables"), info.db_tables],
        ];
    }
}

registry.category("actions").add("storage_dashboard_tag", StorageDashboard);
