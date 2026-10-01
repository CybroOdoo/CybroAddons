/** @odoo-module **/
import { registry } from '@web/core/registry';
import { Component, onWillStart, useState, useRef, onMounted } from '@odoo/owl';
import { useService } from '@web/core/utils/hooks';
import { user } from "@web/core/user";
export class AdvancedDashboardMenuCard extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService('orm');
    }
}
AdvancedDashboardMenuCard.template = 'AdvancedDashboardMenuCardTemplate';
