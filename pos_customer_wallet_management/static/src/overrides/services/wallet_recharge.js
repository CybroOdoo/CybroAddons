/** @odoo-module */
import { Component } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { useRef, onMounted, onWillStart } from "@odoo/owl";
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
        this.pos = useService("pos");
        // Ensure journals is always an array
        this.journals = [];
        onWillStart(async () => {
            this.journals = await this.orm.searchRead(
                "account.journal",
                [['type', 'in', ['cash', 'bank']]],
                ["id", "name", "is_wallet_journal"]
            );
        });
        onMounted(() => {
            if (this.amount_input.el) {
                this.amount_input.el.focus();
            }
            if (this.journalInput.el) {
                const defaultJournal = this.journals.find(j => j.is_wallet_journal);
                if (defaultJournal) {
                    this.journalInput.el.value = defaultJournal.id;
                }
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
            const currency = this.pos.currency.name;
            const session = this.pos.pos_session ? this.pos.pos_session.id : (this.pos.config.current_session_id ? (Array.isArray(this.pos.config.current_session_id) ? this.pos.config.current_session_id[0] : this.pos.config.current_session_id.id) : null);
            const result = await this.orm.call("recharge.wallet", "frontend_recharge", [
                partner.id,
                parseFloat(amount_input),
                currency,
                session,
                journalId
            ]);
            if (result === false) {
                this._showErrorMsg(_t("Failed to recharge wallet - Backend error"));
                return;
            }
            // Update the partner balance in the POS store directly for immediate UI update
            this.props.partner.wallet_balance = result;

            this.notification.add(_t('Successfully Recharged Your Wallet'), {
                type: 'success',
            });
            this.props.close();
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
