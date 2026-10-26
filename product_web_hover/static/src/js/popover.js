/** @odoo-module **/
/******************************************************************************
 *
 *    Cybrosys Technologies Pvt. Ltd.
 *
 *    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
 *    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
 *
 *    You can modify it under the terms of the GNU LESSER
 *    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
 *
 *    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
 *    (LGPL v3) along with this program.
 *    If not, see <http://www.gnu.org/licenses/>.
 *
 ******************************************************************************/

import { Component, useProps } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";
import { usePopover } from "@web/core/popover/popover_hook";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import { formatFloat, formatMonetary } from "@web/views/fields/formatters";

const PRODUCT_FIELDS = ["name", "categ_id", "default_code", "qty_available"];
// The cost is only displayed to sales managers.
const COST_GROUP = "sales_team.group_sale_manager";

/**
 * Extract the id of a many2one value of a record (`{ id, display_name }`, `[id, display_name]`, or `id`).
 */
function extractId(value) {
    if (!value) {
        return null;
    }
    if (Array.isArray(value)) {
        return value[0] || null;
    }
    if (typeof value === "object") {
        return value.id || null;
    }
    return typeof value === "number" ? value : null;
}

/**
 * Popover component displaying the product details.
 */
export class ProductDetailPopover extends Component {
    static template = "product_web_hover.ProductDetailPopover";
    props = useProps();

    get details() {
        return this.props.productDetails;
    }

    get recordData() {
        return this.props.record.data;
    }

    get productImageUrl() {
        return `/web/image/product.product/${this.details.id}/image_128`;
    }

    get categoryName() {
        if (!this.details.categ_id) {
            return "";
        }
        if (Array.isArray(this.details.categ_id)) {
            return this.details.categ_id[1] || "";
        }
        return this.details.categ_id.display_name || "";
    }

    get hasCost() {
        return this.details.standard_price !== undefined;
    }

    get isInStock() {
        return this.details.qty_available > 0;
    }

    formatQuantity(quantity) {
        return formatFloat(quantity);
    }

    formatCurrency(amount) {
        return formatMonetary(amount, {
            currencyId: extractId(this.recordData.currency_id),
        });
    }

    onMouseEnter() {
        this.props.onKeepOpen?.();
    }

    onMouseLeave() {
        this.props.onScheduleClose?.();
    }
}

/**
 * Widget placed in the sale order line list: an info icon opening the
 * product details popover when hovered (or clicked).
 */
export class ProductDetailWidget extends Component {
    static template = "product_web_hover.ProductDetailWidget";
    props = useProps(standardWidgetProps);

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.popover = usePopover(ProductDetailPopover, {
            position: "bottom",
            closeOnClickAway: true,
        });
        // Identifies the latest open request, to ignore outdated answers.
        this.requestId = 0;
        this.closeTimeout = null;
    }

    get productId() {
        return extractId(this.props.record?.data?.product_id);
    }

    /**
     * Section and note lines have no product, so they get no icon.
     */
    get hasProduct() {
        return Boolean(this.productId);
    }

    async fetchProductDetails(productId) {
        const fields = [...PRODUCT_FIELDS];
        if (await user.hasGroup(COST_GROUP)) {
            fields.push("standard_price");
        }
        const [product] = await this.orm.read("product.product", [productId], fields);
        return product;
    }

    cancelClose() {
        if (this.closeTimeout) {
            clearTimeout(this.closeTimeout);
            this.closeTimeout = null;
        }
    }

    scheduleClose() {
        this.cancelClose();
        this.closeTimeout = setTimeout(() => {
            this.popover.close();
            this.closeTimeout = null;
        }, 200);
    }

    async openPopover(target) {
        this.cancelClose();
        if (this.popover.isOpen) {
            return;
        }
        const requestId = ++this.requestId;
        let details;
        try {
            details = await this.fetchProductDetails(this.productId);
        } catch (error) {
            if (requestId === this.requestId) {
                this.notification.add(_t("The product details could not be loaded."), {
                    type: "danger",
                });
            }
            throw error;
        }
        if (requestId !== this.requestId || !details || !target.isConnected) {
            return;
        }
        this.popover.open(target, {
            record: this.props.record,
            productDetails: details,
            onKeepOpen: () => this.cancelClose(),
            onScheduleClose: () => this.scheduleClose(),
        });
    }

    async onMouseEnter(ev) {
        await this.openPopover(ev.currentTarget);
    }

    onMouseLeave() {
        this.requestId++;
        this.scheduleClose();
    }

    async onClick(ev) {
        if (this.popover.isOpen) {
            this.cancelClose();
            this.popover.close();
        } else {
            await this.openPopover(ev.currentTarget);
        }
    }
}

export const productDetailWidget = {
    component: ProductDetailWidget,
    listViewWidth: 24,
    fieldDependencies: [
        { name: "product_id", type: "many2one" },
        { name: "product_uom_qty", type: "float" },
        { name: "price_unit", type: "float" },
        { name: "currency_id", type: "many2one" },
    ],
};

registry.category("view_widgets").add("product_detail_popover_widget", productDetailWidget);
