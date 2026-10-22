import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { Component, useProps, signal, t } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { WarningDialog } from "@web/core/errors/error_dialogs";
import { TransferRefPopup } from "@stock_transfer_in_pos/app/utils/input_popups/transfer_ref_popup";

export class TransferPopup extends Component {
    static template = "stock_transfer_in_pos.TransferPopup";
    static components = { Dialog };
    props = useProps({
        title: t.string().optional(_t("Confirm?")),
        data: t.object().optional({}),
        configId: t.number().optional(),
        confirmButtonLabel: t.string().optional("Confirm"),
        close: t.function(),
    });

    dest_tr = signal.ref();
    source_tr = signal.ref();
    picking = signal.ref();
    source_loc = signal.ref();
    dest_loc = signal.ref();
    stage = signal.ref();

    setup() {
        this.dialog = useService("dialog");
        this.pos = usePos();
        this.orm = useService("orm");
    }

    _clickPicking(ev) {
        // Adjust destination and source location options based on selected picking type
        const pickId = ev.target.value;
        const pickingTypes = this.props.data?.picking_type || [];
        const pickingType = pickingTypes.find((p) => String(p.id) === String(pickId));
        const type = pickingType ? pickingType.code : ev.target.selectedOptions[0]?.dataset?.type;
        const sourceTr = this.source_tr();
        const destTr = this.dest_tr();
        const sourceLocEl = this.source_loc();
        const destLocEl = this.dest_loc();
        const whStock = this.props.data?.wh_stock;

        if (sourceTr) {
            sourceTr.classList.remove("d-none");
        }
        if (destTr) {
            destTr.classList.remove("d-none");
        }

        if (type === "incoming") {
            // Incoming (Receipt): Source is vendor (omitted to use picking type default), destination is stock
            if (sourceTr) {
                sourceTr.classList.add("d-none");
            }
            if (destLocEl && whStock) {
                destLocEl.value = pickingType?.default_location_dest_id?.[0] || whStock;
            }
        } else if (type === "outgoing") {
            // Outgoing (Delivery): Source is stock, destination is customer (omitted to use picking type default)
            if (sourceLocEl && whStock) {
                sourceLocEl.value = pickingType?.default_location_src_id?.[0] || whStock;
            }
            if (destTr) {
                destTr.classList.add("d-none");
            }
        } else {
            // Internal transfer: both are internal/transit locations
            if (sourceLocEl && whStock) {
                sourceLocEl.value = pickingType?.default_location_src_id?.[0] || whStock;
            }
            if (destLocEl && whStock) {
                destLocEl.value = pickingType?.default_location_dest_id?.[0] || whStock;
            }
        }
    }

    // Confirm button to create the transfer in backend
    async confirm() {
        const pickingEl = this.picking();
        const sourceTr = this.source_tr();
        const destTr = this.dest_tr();
        const sourceLocEl = this.source_loc();
        const destLocEl = this.dest_loc();
        const stageEl = this.stage();

        const pickId = pickingEl ? pickingEl.value : "";
        // Do not read hidden select values so receipts and deliveries use picking type defaults
        const sourceId = (sourceTr && !sourceTr.classList.contains("d-none") && sourceLocEl) ? sourceLocEl.value : "";
        const destId = (destTr && !destTr.classList.contains("d-none") && destLocEl) ? destLocEl.value : "";
        const state = stageEl ? stageEl.value : "draft";
        const configId = this.props.configId || this.pos?.config?.id;

        if (!pickId) {
            this.dialog.add(WarningDialog, {
                title: _t("Select Picking Type"),
                message: _t("Please select a picking type for transferring"),
            });
            return;
        }

        const order = this.pos.getOrder();
        const lines = order ? (order.getOrderlines ? order.getOrderlines() : order.lines) : [];
        const product = { pro_id: [], qty: [] };

        for (const line of lines) {
            if (line.product_id) {
                product.pro_id.push(line.product_id.id);
                product.qty.push(line.qty);
            }
        }

        try {
            const result = await this.orm.call(
                "pos.config",
                "create_transfer",
                [configId, pickId, sourceId, destId, state, product],
                {}
            );
            this.dialog.add(TransferRefPopup, {
                title: _t("Success"),
                data: result,
            });
        } catch (error) {
            this.dialog.add(WarningDialog, {
                title: _t("Transfer Failed"),
                message: error.message || _t("Failed to create stock transfer."),
            });
        }
        this.cancel();
    }

    cancel() {
        this.props.close();
    }
}