import { rpc } from "@web/core/network/rpc";
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

/**
 * Search and group the tickets of the customer portal.
 */
export class TicketSearch extends Interaction {
    static selector = "#ticket";
    dynamicContent = {
        "#group_select": { "t-on-change": this.onGroupSelectChange },
        "#search_ticket": { "t-on-click": this.onSearch },
        "#search_box": { "t-on-keydown": this.onSearchKeydown },
    };

    async onGroupSelectChange() {
        const value = this.el.querySelector("#group_select").value;
        const result = await this.waitFor(rpc("/ticketgroupby", { search_value: value }));
        this.renderResult(result);
    }

    async onSearch() {
        const value = this.el.querySelector("#search_box").value;
        const result = await this.waitFor(rpc("/ticketsearch", { search_value: value }));
        this.renderResult(result);
    }

    onSearchKeydown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.onSearch();
        }
    }

    renderResult(html) {
        const target = document.querySelector(".search_ticket");
        if (target) {
            target.innerHTML = html;
        }
    }
}

registry.category("public.interactions").add("odoo_website_helpdesk.ticket_search", TicketSearch);
