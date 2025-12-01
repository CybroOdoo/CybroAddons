/** @odoo-module */
import { Component } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { useRef, onMounted,onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";


export class RechargeScreen extends Component {
    static template = "pos_customer_wallet_management.RechargeScreen";

    static props = {
        confirmText: { type: String, optional: true },
        cancelText: { type: String, optional: true },
        title: { type: String, optional: true },
        partner: { type: Object },
        data: { type: Array },
        close: { type: Function }
    };

    static components = {
        Dialog
    }

    static defaultProps = {
        confirmText: 'Add',
        cancelText: 'Cancel',
        title: 'Wallet Recharge'
    };

    setup() {
        this.amount_input = useRef("amountInput");
        this.journalInput = useRef("journalInput");
        this.orm = useService('orm');
        this.notification = useService('notification');

        // Ensure journals is always an array
        this.journals = [];

        onWillStart(async () => {
            this.journals = await this.orm.searchRead(
            "account.journal",
            [],["id", "name"])
        });

        onMounted(() => {
            if (this.amount_input.el) {
                this.amount_input.el.focus();
            }
        });
    }

    async confirm() {
        const journalId = parseInt(this.journalInput.el.value);

        if (!this.amount_input.el || !this.journalInput.el) {
            return;
        }

        const partner = this.props.partner;
        const amount_input = this.amount_input.el.value;
        const journalInput = this.journalInput.el.value;

        if (amount_input.trim() === '' || journalInput.trim() === '') {
            this._showErrorMsg(_t("Please fill all fields"));
            return;
        }

        try {
            const pos = this.env.services.pos;
            const currency = this.env.services.pos.currency.name;
            const session = this.env.services.pos.config.current_session_id.id;

            const rpc = await this.orm.call("recharge.wallet", "frontend_recharge", [
                partner.id,
                parseFloat(amount_input),
                currency,
                session,
                journalId
            ]);

            this.notification.add(_t('Successfully Recharged Your Wallet'), {
                type: 'success',
            });
            this.props.close();
            browser.location.reload();
        } catch (error) {
            this._showErrorMsg(_t("Failed to recharge wallet"));
        }
    }

    cancel() {
        this.props.close();
    }

    _showErrorMsg(msg) {
        this.notification.add(msg, {
            type: 'danger',
        });
    }
}
