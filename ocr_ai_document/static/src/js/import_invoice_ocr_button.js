/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { useService } from "@web/core/utils/hooks";
import { useState, onWillStart } from "@odoo/owl";

/**
 * Generic OCR list controller — shared by invoice, purchase, sale,
 * and stock picking list views.
 *
 * The "Import via OCR" button is only rendered if an active OCR
 * configuration exists for the current model. This is checked once
 * when the list component mounts (onWillStart), so the button never
 * appears when no configuration has been set up.
 */
export class OcrListController extends ListController {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.notification = useService("notification");

        // Reactive state — button hidden by default until config check completes
        this.ocrState = useState({ hasConfig: false });

        const context = this.props.context || {};
        const activeModel = this.props.resModel;
        const moveType = context.default_move_type || null;
        const methodName = activeModel === "account.move"
            ? "check_active_boolean_invoice"
            : "check_active_ocr_config";

        // Check if active OCR config exists when the list loads
        onWillStart(async () => {
            try {
                const result = await this.orm.call(
                    activeModel,
                    methodName,
                    [activeModel, moveType],
                );
                this.ocrState.hasConfig = result.active === true;
            } catch {
                this.ocrState.hasConfig = false;
            }
        });
    }

    async onClickOcrImport() {
        const context = this.props.context || {};
        const activeModel = this.props.resModel;
        const moveType = context.default_move_type || null;
        const pickingTypeCode = context.default_picking_type_code || null;
        const restrictedPickingTypeCode = context.restricted_picking_type_code || null;
        const methodName = activeModel === "account.move"
            ? "check_active_boolean_invoice"
            : "check_active_ocr_config";

        try {
            const result = await this.orm.call(
                activeModel,
                methodName,
                [activeModel, moveType],
            );
            if (result.active) {
                await this.actionService.doAction({
                    type: "ir.actions.act_window",
                    res_model: "import.via.ocr",
                    name: "Import via OCR",
                    view_mode: "form",
                    views: [[false, "form"]],
                    target: "new",
                    context: {
                        active_model: activeModel,
                        record_id: result.record_id,
                        default_move_type: moveType,
                        default_picking_type_code: pickingTypeCode,
                        restricted_picking_type_code: restrictedPickingTypeCode,
                    },
                });
            } else {
                this.ocrState.hasConfig = false;
                this.notification.add(
                    "No active OCR configuration found for this model. " +
                    "Go to Settings → OCR AI Integration → Model Configuration.",
                    { type: "danger" }
                );
            }
        } catch (error) {
            this.notification.add("OCR error: " + error.message, { type: "danger" });
        }
    }
}

// ── Invoice / Vendor Bill list view ──────────────────────────────────────────
registry.category("views").add("ocr_button_invoice", {
    ...listView,
    Controller: OcrListController,
    buttonTemplate: "ocr_ai_invoice.ListView.Buttons.Invoice",
});

// ── Purchase Order list view ──────────────────────────────────────────────────
registry.category("views").add("ocr_button_purchase", {
    ...listView,
    Controller: OcrListController,
    buttonTemplate: "ocr_ai_invoice.ListView.Buttons.Purchase",
});

// ── Sale Order list view ──────────────────────────────────────────────────────
registry.category("views").add("ocr_button_sale", {
    ...listView,
    Controller: OcrListController,
    buttonTemplate: "ocr_ai_invoice.ListView.Buttons.Sale",
});

// ── Stock Picking list view (Receipts, Deliveries, Internal Transfers) ────────
registry.category("views").add("ocr_button_stock", {
    ...listView,
    Controller: OcrListController,
    buttonTemplate: "ocr_ai_invoice.ListView.Buttons.Stock",
});