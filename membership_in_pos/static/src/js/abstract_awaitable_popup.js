/** @odoo-module */
import { Dialog } from "@web/core/dialog/dialog";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, useRef } from "@odoo/owl";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { accountTaxHelpers } from "@account/helpers/account_tax";

export class MembershipPopup extends Component {
    static template = "membership_in_pos.MembershipPopup";
    static components = { Dialog };
    static defaultProps = {
        confirmText: 'Confirm',
        cancelText: 'Cancel',
        title: 'Membership Card',
        body: '',
    };
    setup() {
        super.setup();
        this.pos = usePos();
        this.orm = useService('orm');
        this.dialog = useService("dialog");
        this.state = useState({
            card: false,
            productId: false
        })
        this.cardCodeRef = useRef("cardCode");
    }
    async Membership_check() {
        var customer_details = []
        const customerInput = this.cardCodeRef.el.value; // Access input value via ref
        this.partner = this.pos.getOrder().getPartner()
        const customer = this.partner.id
        customer_details.push({
            'customerInput': customerInput,
            'customer': customer
        })

        //This is used to retrieve the customers membership details
        var card = await this.orm.call("membership.card", "membership_card_check", [[]], { customer_input: customer_details }).then((card) => {
            this.state.card = card
            if (this.state.card == 0) {
                this.dialog.add(AlertDialog, {
                    title: _t('Membership'),
                    body: _t("Your Card is Expired / Please check you have membership. \n The discount product seems misconfigured. Make sure it is flagged as 'Can be Sold' and 'Available in Point of Sale'.")
                });
            }
        })
    }
    async confirm() {
        await this.Membership_check()
        var order = this.pos.getOrder();
        var lines = order.getOrderlines();
        if (this.state.card) {
            const product = this.pos.models["product.product"].get(this.state.card.product_id);
            if (!product) {
                this.dialog.add(AlertDialog, {
                    title: _t("No discount product found"),
                    body: _t(
                        "Membership discount product not loaded in POS session."
                    ),
                });
                return;
            }

            // Remove existing discount lines (only lines matching the discount product)
            lines.filter(line => {
                const lineProduct = line.getProduct?.();
                return lineProduct && lineProduct.id === product.id;
            }).forEach(line => {
                line.delete();
            });


            // Prepare new discount lines using accountTaxHelpers

            const discountableLines = order.getOrderlines().filter((line) => line.isGlobalDiscountApplicable());
            const baseLines = discountableLines.map((line) =>
                accountTaxHelpers.prepare_base_line_for_taxes_computation(
                    line,
                    line.prepareBaseLineForTaxesComputationExtraValues()
                )
            );

            accountTaxHelpers.add_tax_details_in_base_lines(baseLines, order.company_id);
            accountTaxHelpers.round_base_lines_tax_details(baseLines, order.company_id);

            const groupingFunction = (base_line) => ({
                grouping_key: { product_id: product },
                raw_grouping_key: { product_id: product.id },
            });

            // Parse discount percentage
            const percent = parseFloat(this.state.card.discount);

            const globalDiscountBaseLines = accountTaxHelpers.prepare_global_discount_lines(
                baseLines,
                order.company_id,
                "percent",
                percent,
                {
                    computation_key: "global_discount",
                    grouping_function: groupingFunction,
                }
            );

            for (const baseLine of globalDiscountBaseLines) {
                const discountProduct = baseLine.product_id;
                if (!discountProduct) {
                    continue;
                }
                const discountProductTmpl = discountProduct.product_tmpl_id;

                const extra_tax_data = accountTaxHelpers.export_base_line_extra_tax_data(baseLine);
                extra_tax_data.discount_percentage = percent;

                await this.pos.addLineToOrder(
                    {
                        product_id: discountProduct,
                        price_unit: baseLine.price_unit,
                        qty: baseLine.quantity,
                        tax_ids: [["link", ...baseLine.tax_ids]],
                        product_tmpl_id: discountProductTmpl,
                        extra_tax_data: extra_tax_data,
                    },
                    order,
                    { force: true },
                    false  // configure=false: skip variant configurator popup for discount lines
                );
            }

        }
        this.props.close();
    }
    async cancel() {
        this.props.close();
    }
}
