/** @odoo-module */
// Import necessary modules and components
import {registry} from "@web/core/registry";
import {BarcodeDialog} from "./barcode_dialog";
import {Component, useState, useRef, useEffect} from "@odoo/owl";
import {useService, useBus} from "@web/core/utils/hooks";
import {CustomBarcodeAdjustmentLines} from "./barcode_adjustment_lines"
import {jsonrpc} from "@web/core/network/rpc_service";

export const scrollToView = (selector, args = {}) => {
    const element = document.querySelector(selector);
    if (element) {
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'start',
            ...args
        });
    } else {
        console.error(`Element with class ${selector} not found.`);
    }
}
const actionRegistry = registry.category("actions");

export class CustomBarcodeAdjustment extends Component {
    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action")
        this.dialog = useService("dialog");
        this.notification = useService("notification")
        const barcode = useService("barcode");
        this.sound = useService("barcodeSound");
        this.location = false
        this.state = useState({
            adjust_stock: [],
            selected_stock: []
        })
        useEffect(() => {
            this.env.bus.trigger("TOGGLE_NAVBAR:HIDE", {show: false})
            return () => {
                this.env.bus.trigger("TOGGLE_NAVBAR:HIDE", {show: true})
            }
        })
        useBus(barcode.bus, "barcode_scanned", (ev) => this.ReadBarcode(ev.detail.barcode))
        useBus(this.env.bus, 'barcode-cancel-stock-quantity', (ev) => this._onClickCancelSelected(ev.detail));
        useBus(this.env.bus, 'barcode-applying-multi-stock-quantity', (ev) => this.MultiApplyQuantity(ev.detail));
        this.root = useRef('BarcodeAdjustmentRoot')
        this.getAdjustmentData()
    }

    /**
     * Function for cancelling the selected records in the view
     */
    _onClickCancelSelected(ids) {
        var self = this
        jsonrpc('/barcode-adjustment/cancel_stock_quant', {
            'quant_ids': ids
        }).then(() => {
            if (self.state.selected_stock == ids) {
                self.state.selected_stock = []
            }
            self.state.adjust_stock = self.state.adjust_stock.filter(item => !ids.includes(item.id))
        })
    }

    /**
     * Function for applying the selected records in the view
     */
    _onClickApplySelected() {
        var self = this
        if (this.state.selected_stock.length) {
            jsonrpc('/barcode-adjustment/apply_multiple_inventory', {
                'quant_ids': self.state.selected_stock
            }).then((response) => {
                self.actionService.doAction('soft_reload')
                if (response) {
                    self.actionService.doAction(response)
                    self.state.adjust_stock = self.state.adjust_stock.filter(item => !self.state.selected_stock.includes(item.id))
                    self.state.selected_stock = []
                } else {
                    self.state.adjust_stock = self.state.adjust_stock.filter(item => !self.state.selected_stock.includes(item.id))
                    self.state.selected_stock = []
                }
            })
        } else {
            self.sound.Danger.play()
            self.notification.add('Please select minimum one product ', {
                type: "warning",
                sticky: false,
            })
        }
    }

    /**
     * Function change the data from the list that are confirmed
     */
    MultiApplyQuantity(data) {
        if (data.value) {
            this.state.selected_stock.push(data.id)
        } else {
            this.state.selected_stock = this.state.selected_stock.filter(item => item !== data.id)
        }
    }

    /**
     * Function for open web cam and scan the barcode
     */
    _onClickScanProduct() {
        this.dialog.add(BarcodeDialog, {
            title: 'Barcode Scanner',
            ReadBarcode: (result) => {
                this.ReadBarcode(result)
            }
        })
    }

    /**
     * Function works when the barcode catches the barcode code and passing the code to python
     */
    ReadBarcode(barcode) {
        barcode = String(barcode)
        var self = this
        if (barcode === 'action_main_menu') {
            this.actionService.doAction({
                type: "ir.actions.client",
                name: 'Barcode',
                tag: "custom_barcode_tags",
                target: "inline",
            })
        } else if (barcode === 'action_validate') {
            this._onClickApplySelected()
        } else {
            jsonrpc('/barcode-adjustment/product-barcode', {
                'code': barcode,
                'location': this.location
            }).then(function (response) {

                if (response.type === 'location') {
                    self.root.el.querySelector('.adjustment_location_header').innerHTML = '<span class="marquee-text">Scan product from the location ' + response.name + ' <i class="fa fa-barcode"/> </span>'
                    self.location = response.id
                } else if (response.type === 'not_storable') {
                    self.sound.Alert.play()
                    self.notification.add('The product ' + response.name + ' is not a storable product please scan a storable product', {
                        type: "warning",
                        sticky: false,
                    })
                } else if (response.type === 'product') {
                    self.state.adjust_stock.unshift(response);

                } else if (response.type === 'exist_product') {
                    const taskIndex = self.state.adjust_stock.findIndex(task => task['id'] === response.id);
                    if (response.error){
                        self.notification.add('The Serial Number ' + response.lot_id + ' is already used in these location(s): ' + response.location_id +'., try again', {
                            type: "warning",
                            sticky: false,
                        })
                    }
                    else{
                        if (taskIndex !== -1) {
                            if (taskIndex !== 0) {
                                const task = self.state.adjust_stock.splice(taskIndex, 1)[0];
                                self.state.adjust_stock.unshift(task);
                            }
                            self.state.adjust_stock.find(task => task['id'] === response.id).inv_quantity += 1;
                        }
                    }
                } else {
                    self.sound.Alert.play()
                    self.notification.add('Product or Location is not found, try again', {
                        type: "warning",
                        sticky: false,
                    })
                }
                setTimeout(() => scrollToView(".dummy-top"), 300) //TODO: maybe use 100?
            })
        }
    }

    /**
     * Function for displaying the data in the inventory adjustment view
     */
    async getAdjustmentData() {
        this.state.adjust_stock = await jsonrpc('/barcode-adjustment/get_adjustment_stock_data', {})
    }

    handleGoBack() {
        window.history.go(-1)
    }
}

CustomBarcodeAdjustment.template = "barcode_for_community.BarcodeAdjustment";
CustomBarcodeAdjustment.components = {
    CustomBarcodeAdjustmentLines
}
actionRegistry.add('custom_adjustment_client_action', CustomBarcodeAdjustment);