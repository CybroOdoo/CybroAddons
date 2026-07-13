/** @odoo-module **/
import { registry } from '@web/core/registry';
import { Component, onWillStart, useState, useRef, onMounted } from '@odoo/owl';
import { useService } from '@web/core/utils/hooks';
import { DashboardCardButtons } from './dashboard_card_buttons';
import { user } from "@web/core/user";
export class DashboardTile extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService('orm');
    }
}
DashboardTile.template = 'DashboardTileTemplate';
DashboardTile.components = { DashboardCardButtons };