import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { PartnerList } from "@point_of_sale/app/screens/partner_list/partner_list";
import { _t } from "@web/core/l10n/translation";

export class SalonNewCustomerDialog extends Component {
    static template = "pos_salon.SalonNewCustomerDialog";
    static components = { Dialog };
    static props = { getPayload: Function, close: Function };

    setup() {
        this.pos = usePos();
        this.orm = useService("orm");
        this.state = useState({ name: "", phone: "", email: "", error: "", saving: false });
    }

    async save() {
        const name = this.state.name.trim();
        const phone = this.state.phone.trim();
        const email = this.state.email.trim();
        if (!name) { this.state.error = _t("Please enter the customer name."); return; }
        if (!phone) { this.state.error = _t("Please enter the phone number."); return; }
        if (email && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
            this.state.error = _t("Please enter a valid email address.");
            return;
        }
        this.state.saving = true;
        try {
            const [id] = await this.orm.create("res.partner", [{ name, phone, email: email || false }]);
            const [partner] = await this.pos.data.read("res.partner", [id]); // loads it into POS
            this.props.getPayload(partner);
            this.props.close();
        } catch (err) {
            this.state.error = err.data?.message || err.message || _t("Could not create the customer.");
            this.state.saving = false;
        }
    }
}

export class SalonCustomerField extends Component {
    static template = "pos_salon.SalonCustomerField";
    static props = { state: Object };   // the parent screen's useState object

    setup() {
        this.pos = usePos();
        this.dialog = useService("dialog");
    }
    get currentPartner() {
        const id = this.props.state.partnerId;
        return id ? this.pos.models["res.partner"].get(id) : null;
    }
    applyPartner(partner) {
        const s = this.props.state;
        s.partnerId = partner.id;
        s.customerName = partner.name || "";
        s.customerPhone = partner.phone || "";
        s.customerEmail = partner.email || "";
        s.partnerHadPhone = Boolean(partner.phone);
    }
    async selectCustomer() {
        const partner = await makeAwaitable(this.dialog, PartnerList, { partner: this.currentPartner });
        if (partner) this.applyPartner(partner);
    }
    async createCustomer() {
        const partner = await makeAwaitable(this.dialog, SalonNewCustomerDialog, {});
        if (partner) this.applyPartner(partner);
    }
    clearCustomer() {
        const s = this.props.state;
        s.partnerId = false; s.customerName = ""; s.customerPhone = "";
        s.customerEmail = ""; s.partnerHadPhone = false;
    }
}