/** @odoo-module **/
import Registries from 'point_of_sale.Registries';
const { Order } = require('point_of_sale.models');
const { _lt } = require('@web/core/l10n/translation');
import { useListener } from "@web/core/utils/hooks";
const { useRef, onMounted, useState} = owl;
import TicketScreen from 'point_of_sale.TicketScreen';

class BarcodePopup extends TicketScreen {
    setup() {
        super.setup();
        this.state = useState({
            barcodeValue: this.props.startingValue
        });
        useListener('do-refund-edit', this._onDoRefundbarcode);
        this.pos = this.env.pos;
        this.pos_orders = null;
        this.pos_orderline = [];
        this.pos.receipt_barcode_reader = null;
        this.barcode = useRef('barcode');
        onMounted(this.onMounted);
    }

    async _onDoRefundbarcode(ev) {
        const input_barcode = this.state.barcodeValue;
        let order = false;
        var self = this

        const return_order = await this.rpc({
            model: 'pos.order',
            method: 'find_order',
            args: [,input_barcode],
        }).then(async function(data){
            if(data === false){
            self.cancel();
            self.alert_popup();
        }
        else if (data === "error"){
            self.cancel();
            self.error_popup();
        }
        const fetchedOrders = await self.rpc({
            model: 'pos.order',
            method: 'export_for_ui',
            args: [parseInt(data)],
            context: self.env.session.user_context,
        }).then(async function(result){
            await self.env.pos._loadMissingProducts(result);
            await self.env.pos._loadMissingPartners(result);
            let for_fetch;
        result.forEach((order) => {
            for_fetch = Order.create({}, { pos: self.env.pos, json: order });
        });
        order = for_fetch;
        order.orderlines.forEach((lines) => { self._getToRefundDetailbarcode(lines) });
        if (!order) {
            self._state.ui.highlightHeaderNote = !self._state.ui.highlightHeaderNote;
            return;
        }
        if (self._doesOrderHaveSoleItem(order)) {
            if (!self._prepareAutoRefundOnOrder(order)) {
                // Don't proceed on refund if preparation returned false.
                return;
            }
        }
        const partner = order.get_partner();
        const allToRefundDetails = self._getRefundableDetails(partner);
        if (allToRefundDetails.length == 0) {
            self._state.ui.highlightHeaderNote = !self._state.ui.highlightHeaderNote;
            return;
        }
        // The order that will contain the refund orderlines.
        // Use the destinationOrder from props if the order to refund has the same
        // partner as the destinationOrder.
        const destinationOrder =
            self.props.destinationOrder &&
            partner === self.props.destinationOrder.get_partner() &&
            !self.env.pos.doNotAllowRefundAndSales()
                ? self.props.destinationOrder
                : self._getEmptyOrder(partner);

        // Add a check to see if the fiscal position exists in the pos

        if (order.fiscal_position_not_found) {
            self.showPopup('ErrorPopup', {
                title: self.env._t('Fiscal Position not found'),
                body: self.env._t('The fiscal position used in the original order is not loaded. Make sure it is loaded by adding it in the pos configuration.')
            });
            return;
        }

        // Add orderline for each toRefundDetail to the destinationOrder.
        for (const refundDetail of allToRefundDetails) {
            const product = self.env.pos.db.get_product_by_id(refundDetail.orderline.productId);
            const options = self._prepareRefundOrderlineOptions(refundDetail);
            await destinationOrder.add_product(product, options);
            refundDetail.destinationOrderUid = destinationOrder.uid;
        }
        destinationOrder.fiscal_position = order.fiscal_position;

        // Set the partner to the destinationOrder.
        if (partner && !destinationOrder.get_partner()) {
            destinationOrder.set_partner(partner);
            destinationOrder.updatePricelist(partner);
        }
        if (self.env.pos.get_order().cid !== destinationOrder.cid) {
            self.env.pos.set_order(destinationOrder);
        }
        self.env.posbus.trigger('close-popup', {
            popupId: self.props.id,
            response: { confirmed: true, payload: await self.getPayload() },
        });
        });
        });
    }
    _getToRefundDetailbarcode(orderline) {
        if (orderline.id in this.env.pos.toRefundLines) {
            return this.env.pos.toRefundLines[orderline.id];
        } else {
            const partner = orderline.order.get_partner();
            const orderPartnerId = partner ? partner.id : false;
            const newToRefundDetail = {
                qty: orderline.quantity,
                orderline: {
                    id: orderline.id,
                    productId: orderline.product.id,
                    price: orderline.price,
                    qty: orderline.quantity,
                    refundedQty: orderline.refunded_qty,
                    orderUid: orderline.order.uid,
                    orderBackendId: orderline.order.backendId,
                    orderPartnerId,
                    tax_ids: orderline.get_taxes().map(tax => tax.id),
                    discount: orderline.discount,
                },
                destinationOrderUid: false,
            };
            this.env.pos.toRefundLines[orderline.id] = newToRefundDetail;
            return newToRefundDetail;
        }
    }
    alert_popup() {
        let title = 'Alert'
        let body= 'This order has already been returned'
        let popup = 'SuccessPopup'
        this.showPopup(popup, {
                    title: this.env._t(title),
                    body: this.env._t(body),
        });
    }
    error_popup() {
        let title = 'Invalid Barcode!'
        let body= 'Sorry Please Enter a Valid Barcode'
        let popup = 'ErrorPopup'
        this.showPopup(popup, {
                    title: this.env._t(title),
                    body: this.env._t(body),
        });
    }
    onMounted() {
        this.barcode.el.focus();
    }
    getPayload() {
        return {
            barcodeValue: this.state.barcodeValue,
        }
    }
    confirm() {
        this.trigger('do-refund-edit');
    }
    cancel() {
    this.env.posbus.trigger('close-popup', {
            popupId: this.props.id,
            response: { confirmed: false},
        });
    }
}
BarcodePopup.template = 'pos_return_barcode.BarcodePopup';
BarcodePopup.defaultProps = {
    confirmText: _lt('Confirm'),
    cancelText: _lt('Cancel'),
    title: '',
    body: '',
};
Registries.Component.add(BarcodePopup);