/** @odoo-module **/
import { Component, proxy } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import {PersonalOrganizer} from "@personal_organiser/webclient/personalorganiser/personal_organiser";
import {OrgContacts} from "@personal_organiser/webclient/contacts/contacts";
import {NoteMaker} from "@personal_organiser/webclient/notemaker/notemaker";
import {MiniCalendar} from "@personal_organiser/webclient/calender/calender";

export class Sidebar extends Component {
    static template = 'personal_organiser.sidebar';
    static components={PersonalOrganizer,NoteMaker,OrgContacts,MiniCalendar};
    setup() {
        this.state = proxy({
            todaysTasks: [],
            activePanel: null,  // 'task', 'note', 'contacts' or 'calender'
        });
        this.orm = useService('orm');
        this.checkTodaysTasks();
    }
    async checkTodaysTasks() {
        // Local date (toISOString would give the UTC date).
        const now = new Date();
        const today = [
            now.getFullYear(),
            String(now.getMonth() + 1).padStart(2, '0'),
            String(now.getDate()).padStart(2, '0'),
        ].join('-');
        this.state.todaysTasks = await this.orm.search("calendar.event", [
                ["start_date", "=", today],
            ]);
    }
    showNewSidebar(contentType) {
        // Clicking the open panel's icon again closes it.
        this.state.activePanel = this.state.activePanel === contentType ? null : contentType;
    }

    closePanel(content) {
        if (this.state.activePanel === content) {
            this.state.activePanel = null;
        }
    }
}
