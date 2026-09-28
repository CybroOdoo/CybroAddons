/** @odoo-module **/

import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";

export class InvitePeopleDialog extends Component {
    static template = "info_hub.InvitePeopleDialog";
    static components = { Dialog };
    static props = {
        close: { type: Function },
        article: { type: Object },
        onInviteSent: { type: Function },
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");

        this.state = useState({
            searchQuery: "",
            searchResults: [],
            selectedPartners: [],
            permission: "read",
            comment: "",
            searching: false,
        });

        this.onDocumentClick = (ev) => {
            const container = document.querySelector(".o_info_hub_recipients_input_container");
            if (container && !container.contains(ev.target)) {
                this.state.searchResults = [];
            }
        };

        onMounted(() => {
            document.addEventListener("click", this.onDocumentClick);
        });

        onWillUnmount(() => {
            document.removeEventListener("click", this.onDocumentClick);
        });
    }

    async searchPartners(query) {
        this.state.searching = true;
        try {
            const domain = query.trim().length >= 2 ? ["|", ["name", "ilike", query], ["email", "ilike", query]] : [];
            const results = await this.orm.searchRead(
                "res.partner",
                domain,
                ["id", "name", "email"],
                { limit: 8 }
            );

            const selectedIds = this.state.selectedPartners.map(p => p.id);
            this.state.searchResults = results.filter(r => !selectedIds.includes(r.id));
        } catch (error) {
            console.error("Partner search failed:", error);
        } finally {
            this.state.searching = false;
        }
    }

    async onSearchInput(ev) {
        const query = ev.target.value;
        this.state.searchQuery = query;
        await this.searchPartners(query);
    }

    async onInputFocus() {
        await this.searchPartners(this.state.searchQuery);
    }

    selectPartner(partner) {
        this.state.selectedPartners.push(partner);
        this.state.searchQuery = "";
        this.state.searchResults = [];
    }

    removePartner(partnerId) {
        this.state.selectedPartners = this.state.selectedPartners.filter(p => p.id !== partnerId);
    }

    async onInvite() {
        if (this.state.selectedPartners.length === 0) {
            this.notification.add("Please select at least one recipient.", { type: "warning" });
            return;
        }

        try {
            const partnerIds = this.state.selectedPartners.map(p => p.id);
            await this.orm.call(
                "info.hub.article",
                "invite_members",
                [this.props.article.id, partnerIds, this.state.permission]
            );

            await this.props.onInviteSent();
            this.props.close();
        } catch (error) {
            this.notification.add("Failed to invite members.", { type: "danger" });
        }
    }
}
