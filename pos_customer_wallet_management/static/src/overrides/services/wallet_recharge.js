import { Component, signal, onMounted, onWillStart, useProps, t } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";


export class RechargeScreen extends Component {
    static template = "pos_customer_wallet_management.RechargeScreen";

    props = useProps({
        confirmText: t.string().optional("Add"),
        cancelText: t.string().optional("Cancel"),
        title: t.string().optional("Wallet Recharge"),
        partner: t.object(),
        close: t.function(),
    });

    static components = {
        Dialog
    }

    amountInput = signal.ref();
    journalInput = signal.ref();

    setup() {
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
            if (this.amountInput()) {
                this.amountInput().focus();
            }
            if (this.journalInput()) {
                const defaultJournal = this.journals.find(j => j.is_wallet_journal);
                if (defaultJournal) {
                    this.journalInput().value = defaultJournal.id;
                }
            }
        });
    }

    async confirm() {
        const journalId = parseInt(this.journalInput().value);
        if (!this.amountInput() || !this.journalInput()) {
            return;
        }
        const partner = this.props.partner;
        const amountInput = this.amountInput().value;
        const journalInput = this.journalInput().value;
        if (amountInput.trim() === '' || journalInput.trim() === '') {
            this._showErrorMsg(_t("Please fill all fields"));
            return;
        }
        try {
            const currency = this.pos.currency.name;
            const session = this.pos.pos_session ? this.pos.pos_session.id : (this.pos.config.current_session_id ? (Array.isArray(this.pos.config.current_session_id) ? this.pos.config.current_session_id[0] : this.pos.config.current_session_id.id) : null);
            const result = await this.orm.call("recharge.wallet", "frontend_recharge", [
                partner.id,
                parseFloat(amountInput),
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
