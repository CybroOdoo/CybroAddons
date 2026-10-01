/** @odoo-module **/
import { registry } from '@web/core/registry';
import { Component, onWillStart, useState, useRef, onMounted, onWillUpdateProps } from '@odoo/owl';
import { useService, useBus } from '@web/core/utils/hooks';
import { DashboardChart } from './dashboard_chart';
import { DashboardTable } from './dashboard_table';
import { DashboardTile } from './dashboard_tile';
import { DashboardTodo } from './dashboard_todo';
import { DashboardList } from './dashboard_list';
import { DashboardView } from './dashboard_view';
import { DashboardActivity } from './dashboard_activity';


export class DynamicDashboardCard extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService('orm');
        this.state = useState({
            card: this.props.card,
            dateFilter: this.props.activeFilter || 'all',
        })
        useBus(this.env.bus, "dashboard_card_updated", async (ev) => {
            if (ev.detail.id == this.props.card.id) {
                var card = await this.orm.searchRead('dashboard.card', [['id', '=', this.props.card.id]], [
                    'id', 'name', 'description', 'type', 'gs_x', 'gs_y', 'gs_w', 'gs_h',
                    'background_color', 'chart_type', 'chart_x_axis_data', 'chart_y_axis_data',
                    'chart_color', 'semi_circular', 'index_axis', 'color_group_id',
                    'table_headers', 'table_rows', 'table_type', 'table_limit',
                    'record_limit', 'table_order', 'show_record_count', 'model_id',
                    'model_name', 'domain', 'view_type', 'activity_type', 'enable_click',
                    'todo_type', 'dashboard_menu_id', 'todo_ids', 'view_records', 
                    'group_by_field_id', 'measure_field_id', 'table_field_line_ids',
                    'legend', 'legend_position', 'legend_alignment', 'legend_label_pointstyle',
                    'aggregation_method', 'group_by_2', 'size', 'block_value', 'block_aggregation_method',
                    'icon_class', 'icon_layout', 'icon_color', 'icon_size'
                ])
                this.state.card = card[0]
            }
        })
        onWillUpdateProps((nextProps) => {
            this.state.card = nextProps.card;
            this.state.dateFilter = nextProps.activeFilter || 'all';
        });
    }
}
DynamicDashboardCard.template = 'DynamicDashboardCardTemplate';
DynamicDashboardCard.components = { DashboardChart, DashboardTile, DashboardTable, DashboardTodo, DashboardList, DashboardView, DashboardActivity };