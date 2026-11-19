/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ActionMenus } from "@web/search/action_menus/action_menus";
import { user } from "@web/core/user";
import { onMounted } from "@odoo/owl";

patch(ActionMenus.prototype, {
    setup() {
        super.setup(...arguments);
        if (!this.state) {
            this.state = {};
        }
        this.state.restrictedReportIds = [];
        this.state.restrictedActionIds = [];
        this.fetchRestrictedReports = this.fetchRestrictedReports.bind(this);
        onMounted(async () => {
            await this.fetchRestrictedReports();
        });
    },
    async fetchRestrictedReports() {
        if (this.state.restrictedReportIds?.length || this.state.restrictedActionIds?.length) {
            return;
        }
        try {
            const userId = user.userId;
            const restrictions = await this.orm.call(
                "role.management",
                "get_export_restrictions",
                [userId]
            );
            this.state.restrictedReportIds = [
                ...new Set(restrictions
                    .filter(r => r.model === this.props.resModel)
                    .flatMap(r => r.report_id)
                )
            ];
            this.state.restrictedActionIds = [
                ...new Set(restrictions
                    .filter(r => r.model === this.props.resModel)
                    .flatMap(r => r.action_id)
                )
            ];
        } catch {
            // Fail gracefully when fetching restrictions
        }
    },
    async getActionItems(props) {
        const originalActionItems = await super.getActionItems(props);
        if (!this.state?.restrictedActionIds?.length) {
            await this.fetchRestrictedReports();
        }
        return originalActionItems.filter(item => {
            const isRestricted = this.state?.restrictedActionIds?.includes(parseInt(item.key, 10));
            return !isRestricted;
        });
    },
    async loadAvailablePrintItems() {
        if (!this.state?.restrictedReportIds?.length) {
            await this.fetchRestrictedReports();
        }
        const printActions = await super.loadAvailablePrintItems();
        return printActions.filter(action => {
            return !this.state?.restrictedReportIds?.includes(parseInt(action.key, 10));
        });
    }
});
