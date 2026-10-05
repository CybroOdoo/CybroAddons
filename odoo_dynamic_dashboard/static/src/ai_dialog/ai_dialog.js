import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { RPCError } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";
import { Component, proxy, t, useProps } from "@odoo/owl";

export const BLOCK_COUNT_CHOICES = [3, 6, 9, 12];
export const MAX_BLOCK_COUNT = 20;

export const AI_EXAMPLES = [
    _t("Sales overview: revenue per month, top customers and salespeople, quotations to follow up"),
    _t("CRM pipeline: opportunities by stage, expected revenue, won deals over time"),
    _t("Invoicing: amounts invoiced per month, unpaid invoices, top customers"),
    _t("Inventory: products, stock moves per month, transfers to process"),
    _t("Contacts: companies and individuals by country and salesperson"),
];

/**
 * Ask Odoo's AI service to design a dashboard from a description, out of the
 * existing building blocks. The blocks it designs are added to the builder, where
 * the user reviews them before saving.
 */
export class DashboardAiDialog extends Component {
    static template = "odoo_dynamic_dashboard.DashboardAiDialog";
    static components = { Dialog };
    props = useProps({
        close: t.function(),
        hasBlocks: t.boolean(),
        onGenerated: t.function(),
    });

    examples = AI_EXAMPLES;
    blockCountChoices = BLOCK_COUNT_CHOICES;
    maxBlockCount = MAX_BLOCK_COUNT;
    title = _t("Generate a Dashboard with AI");
    placeholder = _t("e.g. Sales overview for managers: revenue per month, top customers, best salespeople");

    setup() {
        this.orm = useService("orm");
        this.state = proxy({
            description: "",
            replace: !this.props.hasBlocks,
            // false: the AI decides how many blocks fit the request
            blockCount: false,
            isGenerating: false,
            error: false,
        });
    }

    onDescriptionInput(ev) {
        this.state.description = ev.target.value;
    }

    onDescriptionKeydown(ev) {
        if (ev.key === "Enter" && (ev.ctrlKey || ev.metaKey)) {
            this.generate();
        }
    }

    setBlockCount(blockCount) {
        this.state.blockCount = blockCount;
    }

    onCustomBlockCountInput(ev) {
        const value = parseInt(ev.target.value, 10);
        this.state.blockCount = Number.isNaN(value) ? false : Math.max(1, Math.min(value, MAX_BLOCK_COUNT));
    }

    isCustomBlockCount() {
        return Boolean(this.state.blockCount) && !BLOCK_COUNT_CHOICES.includes(this.state.blockCount);
    }

    setReplace(replace) {
        this.state.replace = replace;
    }

    useExample(example) {
        this.state.description = example;
    }

    async generate() {
        const description = this.state.description.trim();
        if (!description || this.state.isGenerating) {
            return;
        }
        this.state.isGenerating = true;
        this.state.error = false;
        let design;
        try {
            design = await this.orm.silent.call("dynamic.dashboard", "generate_with_ai", [description], {
                block_count: this.state.blockCount || null,
            });
        } catch (error) {
            if (!(error instanceof RPCError)) {
                throw error;
            }
            this.state.error = error.data?.message || _t("Sorry, the dashboard could not be generated.");
            return;
        } finally {
            this.state.isGenerating = false;
        }
        this.props.onGenerated(design, { replace: this.state.replace, blockCount: this.state.blockCount });
        this.props.close();
    }
}
