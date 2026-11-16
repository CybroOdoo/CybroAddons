/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { Component, proxy, useProps, t } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class BookOrderPopup extends Component {
//Popup to create and save a POS booked order with pickup or delivery details.
    static template = "pos_book_order.BookOrderPopup";
    static components = {
        Dialog,
    };
    props = useProps({
        title: t.string().optional(""),
        close: t.function(),
        partner: t.object(),
        order: t.object().optional(),
        confirmText: t.string().optional(_t("Save")),
        cancelText: t.string().optional(_t("Discard")),
        clearText: t.string().optional(_t("Clear")),
        body: t.string().optional(""),
        getPayload: t.function().optional(),
    });

    setup() {
        this.pos = usePos();
        this.order = this.props.order || this.pos.getOrder();
        this.state = proxy({
            method: "pickup",
            order_note: "",
            pickup_date: "",
            delivery_date: "",
            delivery_address: this.props.partner?.contact_address || this.props.partner?.street || "",
        });
    }

    get totalAmount() {
        return this.pos.formatCurrency(this.order?.priceIncl || 0);
    }

    get currentDate() {
        return new Date().toISOString().split("T")[0];
    }

    async confirm() {
        const pickup_date = this.state.method === "pickup" ? (this.state.pickup_date || "") : "";
        const delivery_date = this.state.method === "deliver" ? (this.state.delivery_date || "") : "";
        const order_note = this.state.order_note || "";
        const partner = this.props.partner.id;
        const address = this.state.method === "deliver" ? (this.state.delivery_address || "") : "";
        const phone = this.props.partner.phone || "";

        let jsDate = this.order?.date_order;
        let date;
        if (jsDate instanceof Date) {
            date = jsDate.toISOString().slice(0, 19).replace("T", " ");
        } else if (typeof jsDate === "string") {
            date = jsDate.replace("T", " ").split(".")[0];
        } else {
            date = new Date().toISOString().slice(0, 19).replace("T", " ");
        }

        const pos_order = this.order?.uuid || this.order?.uid || this.order?.name || "";
        const price_list = this.order?.pricelist_id?.id || false;

        const product = {
            product_id: [],
            qty: [],
            price: [],
            tax_ids: [],
        };

        for (const line of (this.order?.lines || [])) {
            const pid = line.product_id?.id;
            const qty = line.qty;
            const unit = line.price_unit;
            const tax_ids = line.tax_ids?.map((t) => t.id || t) || [];

            product.product_id.push(pid);
            product.qty.push(qty);
            product.price.push(unit);
            product.tax_ids.push(tax_ids);
        }

        const book_order = await this.pos.data.call(
            "book.order",
            "create_booked_order",
            [partner, phone, address, date, price_list, product, order_note, pickup_date, delivery_date, pos_order],
            {}
        );
        const bookId = typeof book_order === "object" ? book_order.id : book_order;
        const bookName = typeof book_order === "object" ? book_order.name : book_order;

        if (this.order) {
            this.order.is_booked = true;
            this.order.booking_ref_id = bookId;
            this.order.booking_ref_name = bookName;
            const bookedData = {
                id: bookId,
                name: bookName,
                partner_id: partner,
                partner_name: this.props.partner?.name || "",
                phone: phone,
                address: address,
                note: order_note,
                pickup: pickup_date ? pickup_date + " 00:00:00" : false,
                deliver: delivery_date ? delivery_date + " 00:00:00" : false,
                pos_order_uid: pos_order,
            };
            this.order.booked_data = bookedData;
            if (this.order.uiState) {
                this.order.uiState.is_booked = true;
                this.order.uiState.booking_ref_id = bookId;
                this.order.uiState.booking_ref_name = bookName;
                this.order.uiState.booked_data = bookedData;
            }
        }

        const result = await this.pos.data.call("book.order", "all_orders", ["all"]);
        this.pos.navigate("BookedOrdersScreen", {
            data: result,
            new_order: true,
            booked_order_uuid: this.order?.uuid,
        });

        this.props.close();
    }
}