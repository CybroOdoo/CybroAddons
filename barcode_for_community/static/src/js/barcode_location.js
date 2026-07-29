/** @odoo-module **/
import {registry} from "@web/core/registry";
import {BarcodeDialog} from "./barcode_dialog";
import {Component, onWillStart, useEffect, useRef, useState} from "@odoo/owl";
import {useBus, useService} from "@web/core/utils/hooks";
import {CustomBarcodeLocationLines} from "./barcode_location_lines"
import {jsonrpc} from "@web/core/network/rpc_service";

const DEFAULT_FUNCTIONS = [
    'action_main_menu', 'action_validate',
    'action_cancel', 'action_picking',
    'action_slip', 'action_put_in_pack',
    'action_scrap', 'action_return'
]

const actionRegistry = registry.category("actions");

export class CustomBarcodeLocation extends Component {
    setup() {
        const barcode = useService("barcode");
        this.id = this.props.action.params.id || this.props.action.params.active_id
        if (!this.id) {
            this.id = parseInt(sessionStorage.getItem("custom-barcode-transfer-id")) || false
        } else {
            sessionStorage.setItem("custom-barcode-transfer-id", this.id);
        }
        this.type = localStorage.getItem("custom-barcode-inventory-type")
        this.dialog = useService("dialog");
        this.orm = useService("orm");
        this.rpc = useService("rpc");
        this.sound = useService("barcodeSound");
        this.actionService = useService("action")
        this.notification = useService("notification")
        this.state = useState({
            transfer: [],
            data: [],
            selected_move: [],
            lot_move: [],
            lineTransfer: [],
            navHasLargeText: false
        })
        this.barcodeState = useState({
            recentScan: false, // Stores recently scanned model name for future ref,
            lastScanTracking: false,
            message: "",
            lastScannedProduct: false,
            withBarcode: false,
            pickingType: ""
        })
        onWillStart(async () => await this.getData())
        useBus(barcode.bus, "barcode_scanned", ({detail}) => this.barcodeReader(detail.barcode))
        useBus(this.env.bus, 'barcode-cancel-stock-move', async ({detail}) => await this._onClickCancelSelected(detail));
        useBus(this.env.bus, 'barcode-applying-multi-stock-quantity', (ev) => this.MultiApplyQuantity(ev.detail));
        useEffect((instruction) => {
            this.state.navHasLargeText = instruction.length >= 35;
        }, () => [this.nextInstruction])
        useEffect(() => {
            this.env.bus.trigger("TOGGLE_NAVBAR:HIDE", {show: false})
            return () => {
                this.env.bus.trigger("TOGGLE_NAVBAR:HIDE", {show: true})
            }
        }, () => [])
    }

    async doActionButton(name, context = {}, reload = true) {
        const action = {
            type: "object",
            resId: this.id,
            name,
            resModel: "stock.picking",
            onClose: () => reload && this.actionService.doAction('soft_reload')
        }
        if (context) {
            action["context"] = context;
        }
        await this.actionService.doActionButton(action);
    }

    async action_validate() {
        await this.doActionButton("button_validate", {
            skip_backorder: true,
            skip_sms: true,
        });
    }

    async action_cancel() {
        await this.doActionButton("action_cancel", {}, false)
        this.notification.add('The operation has been canceled.', {
            type: "warning",
            sticky: false,
        })
        this.actionGoBack()
    }

    async action_put_in_pack() {
        await this.doActionButton("action_put_in_pack", {}, false)
        this.showNotification("Pack is assigned to the scanned products", "success")
        await this.notify()
    }

    async inventoryCommand(code) {
        const response = await jsonrpc('/inventory_commands', {
            code,
            id: this.id
        })
        if (typeof response === "object") {
            this.actionService.doAction(response)
        }
    }

    async action_slip() {
        await this.inventoryCommand("action_slip")
    }

    async action_picking() {
        await this.inventoryCommand("action_picking")
    }

    async action_return() {
        try {
            const [picking] = await this.orm.read('stock.picking', [this.id], ['state']);
            if (picking && picking.state === 'done') {
                this.actionService.doAction({
                    type: "ir.actions.act_window",
                    res_model: 'stock.return.picking',
                    name: 'Reverse Transfer',
                    views: [[false, "form"]],
                    target: "new",
                    context: {
                        active_id: Number(this.id),
                        active_model: 'stock.picking'
                    },
                });
            } else {
                this.notification.add('Please validate the order first.', {
                    type: "danger",
                    sticky: true,
                });
            }
            this.state.transfer = await jsonrpc('/barcode-location/get-product-data', {
                'pick_id': this.id
            })
        } catch (error) {
            console.error("Error in return operation:", error);
        }

    }

    /**
     * Function change the data from the list that are confirmed
     */
    MultiApplyQuantity(data) {
        if (data.value) {
            this.state.selected_move.push(data.id)
        } else {
            this.state.selected_move = this.state.selected_move.filter(item => item !== data.id)
        }
    }

    /**
     * Function for cancelling the selected records in the view
     */
    async _onClickCancelSelected({id, resModel}) {
        await this.orm.call("barcode.management", "action_remove_move_line", [this.id, Number(id), resModel])
//        this.assignRecent("", "")
        this.state.transfer = this.state.transfer.filter(item => ![id].includes(item.id))
    }

    async readPicking() {
        return await this.orm.call('stock.picking', "get_barcode_picking", [this.id]);
    }

    /**
     * Function for displaying the data in the inventory transfers
     */
    async getData() {
        if (this.id) {
            const [response] = await this.readPicking()
            if (response) {
                this.state.data = {
                    'name': response.name,
                    'state': response.state,
                    'location': response.location_id,
                    'location_name': response.location_id[1],
                    'destination': response.location_dest_id[1],
                    'destination_id': response.location_dest_id[0]
                }
                this.barcodeState.recentScan = response.barcode_recent_scan
                this.barcodeState.lastScanTracking = response.last_scan_tracking
                this.barcodeState.lastScannedProduct = response.last_scanned_product
                this.barcodeState.pickingType = response.picking_type
                this.barcodeState.withBarcode = response.with_barcode
            }
            this.state.transfer = await jsonrpc('/barcode-location/get-product-data', {
                'pick_id': this.id
            })
        }

    }

    /**
     * Function for returns to the previous menu
     */
    actionGoBack() {
        this.env.config.breadcrumbs.length > 1 ? this.env.config.historyBack() : this.OpenMainScreen()
    }

    /**
     * Function for returns to the menu Screen
     */
    OpenMainScreen() {
        window.history.go(-1)
    }

    /**
     * Function for open web cam and scan the barcode
     */
    _onClickScanProduct() {
        this.dialog.add(BarcodeDialog, {
            title: 'Barcode Scanner',
            ReadBarcode: async (result) => {
                await this.barcodeReader(result)
            }
        })
    }

    /**
     * Function for the action confirm in stock.picking
     */
    async _onClickApplyPicking() {
        var self = this
        var response = await jsonrpc('/barcode-location/product-barcode-confirm', {
            'pick_id': self.id
        })
        if (response != true) {
            self.actionService.doAction(response)
        } else {
            this.actionService.doAction('soft_reload')
        }
    }

    async fetchScannedData(barcode) {
        return await this.rpc("/barcode/barcode-scanned", {
            barcode, picking_id: this.id
        })
    }

    action_main_menu() {
        return this.actionService.doAction({
            type: "ir.actions.client",
            name: 'Barcode',
            tag: "custom_barcode_tags",
            target: "fullscreen",
        })
    }

    /**
     * Function for checking the product is with lot or serial.
     */
    async barcodeReader(barcode) {
        barcode = String(barcode, "")
        if (DEFAULT_FUNCTIONS.includes(barcode)) {
            if (typeof this[barcode] === "function") {
                this[barcode]()
            }
        } else {
            const response = await this.fetchScannedData(barcode)
            if (!response.is_error) {
                await this.processPicking(response)
                await this.notify() //FIXME: Maybe find a way to update it from the client instead of expensive calls,
                // at least for some operations
            } else if (this.barcodeState.recentScan === "product.product" && ["serial", "lot"].includes(this.barcodeState.lastScanTracking)) { //TODO: check response model
                await this.assignBarcode(response)
                await this.notify()
                this.assignRecent("stock.lot", "")
            } else this.showNotification("Nothing has been found for this barcode")
        }
    }

    async notify() {
        this.state.transfer = await jsonrpc('/barcode-location/get-product-data', {
            'pick_id': this.id
        })
    }

    showNotification(message = "", type = "danger", sticky = false, sound = true) {
        this.notification.add(message, {
            type,
            sticky,
        })
        if (sound) this.sound.Alert.play()
    }

    assignRecent(model, tracking, product = false) {
        this.barcodeState.recentScan = model;
        this.barcodeState.lastScanTracking = model === "product.product" ? tracking : ""
        this.barcodeState.lastScannedProduct = product
    }

    async _processProductScan(response) {
        switch (response.res_model) {
            case "product.product":
                if (this.barcodeState.lastScanTracking === "lot" && this.barcodeState.lastScannedProduct[0] !== response.data[0].id) {
                    return this.showNotification("Please scan a Lot number before scanning new products")
                }
                if (this.barcodeState.lastScanTracking === "serial") {
                    return this.showNotification("Please scan a serial number before scanning new products")
                } else if (["lot", "none"].includes(this.barcodeState.lastScanTracking)) {
                    await this.addMoveLine(response)
                }
                this.assignRecent(response.res_model, response.data[0].tracking, [response.data[0].id])
                break;
            case "stock.location":
                if (this.barcodeState.lastScanTracking === "lot") {
                    return this.showNotification("Please scan a Lot number before scanning new products")
                }
                if (["serial", "lot"].includes(this.barcodeState.lastScanTracking)) {
                    return this.showNotification("Please scan a serial/lot number for the previous scanned product(s) before scanning the location")
                }
                await this.addLocationToLines(response)
                this.assignRecent(response.res_model, "")
                break;
            case "stock.lot":
                if (["serial", "lot"].includes(this.barcodeState.lastScanTracking)) {
                    await this.assignBarcode(response)
                } else await this.addMoveLine(response)
                this.assignRecent(response.res_model, "")
                break;
            case "stock.quant.package":
                if (["serial", "lot"].includes(this.barcodeState.lastScanTracking)) {
                    return this.showNotification("Please scan a serial/lot number for the previous scanned product(s) before scanning the package")
                } else await this.assignPackage(response)
                this.assignRecent(response.res_model, "")
                break;
            default:
                break;
        }
    }

    async _processPackageScan(response) {
        switch (response.res_model) {
            case "stock.quant.package":
                return this.showNotification("You can't Reassign package, " +
                    "Please scan a location for the package or scan a product.")
            case "stock.location":
                await this.addLocationToLines(response)
                break;
            default:
                await this._processDefaultScan(response)
                break;
        }
        this.assignRecent(response.res_model, "")
    }

    async _processLocationScan(response) {
        switch (response.res_model) {
            case "stock.location":
                response.picking_type === "internal" ? await this.addLocationToLines(response) : this.showNotification("You can't reassign location.")
                break;
            case "product.product":
                await this.addMoveLine(response)
                return this.assignRecent(response.res_model, response.data[0].tracking, [response.data[0].id])
            case "stock.lot":
                await this.addMoveLine(response)
                break;
            case "stock.quant.package":
                if (["outgoing", "internal"].includes(response.picking_type)) {
                    await this.assignPackage(response);
                } else if (response.picking_type === "incoming") {
                    this.showNotification("You can't reassign a package to a moved products.")
                }
                break;
            default:
                break;
        }
        this.assignRecent(response.res_model, "")
    }

    async _processSerialNLotScan(response) {
        switch (response.res_model) {
            case "stock.lot":
                await this.showNotification("You can't reassign Serial/Lot.")
                break;
            case "product.product":
                await this.addMoveLine(response)
                return this.assignRecent(response.res_model, response.data[0].tracking, [response.data[0].id])
            case "stock.quant.package":
                await this.assignPackage(response)
                break;
            case "stock.location":
                await this.addLocationToLines(response)
                break;
            default:
                break;
        }
        this.assignRecent(response.res_model, "")
    }

    get nextInstruction() {
        let instruction = "Scan Product or Serial/Lot."
        if (this.barcodeState.recentScan === "product.product") {
            switch (this.barcodeState.lastScanTracking) {
                case "serial":
                    return "Scan a Serial for the product."
                case "lot":
                    return "Scan the same product or scan Lot number for the scanned products."
                case "none":
                default:
                    if (this.barcodeState.pickingType == 'internal'){
                        return "Scan Product or Serial/Lot or package or source location."
                    }
                    else return "Scan Product or Serial/Lot or package or destination location."
            }
        } else if (this.barcodeState.recentScan === "stock.lot") {
            if (this.barcodeState.pickingType == 'internal'){
                return "Scan Product or Serial/Lot or package or source location."
            }
            else return "Scan Product or Serial/Lot or package or destination location."
        } else if (this.barcodeState.recentScan === "stock.location") {
            return this.barcodeState.pickingType in ["incoming", "outgoing"] ? "Scan Product or Serial/Lot or Package." : "Scan Product or Serial/Lot"
        } else if (this.barcodeState.recentScan === "stock.quant.package") {
            if (this.barcodeState.pickingType == 'internal'){
                return "Scan Product or Serial/Lot or package or source location."
            }
            else return "Scan Product or Serial/Lot or package or destination location."
        }
        return instruction
    }

    async _processDefaultScan(response) {
        if (["product.product", "stock.lot"].includes(response.res_model)) {
            await this.addMoveLine(response)
            let product = response.res_model === "product.product" ? [response.data[0].id] : false
            this.assignRecent(response.res_model, response.data[0].tracking, product)
        } else return this.showNotification("Scan Products or Serial number first")
    }

    async processPicking(response) {
        if (this.barcodeState.recentScan === "product.product") {
            await this._processProductScan(response)
        } else if (this.barcodeState.recentScan === "stock.quant.package") {
            await this._processPackageScan(response)
        } else if (this.barcodeState.recentScan === "stock.location") {
            await this._processLocationScan(response)
        } else if (this.barcodeState.recentScan === "stock.lot") {
            await this._processSerialNLotScan(response)
        } else {
            await this._processDefaultScan(response)
            this.barcodeState.message = "You can scan a new product"
        }
    }

    async _callBackend(data, func, args = []) {
        await this.orm.call("barcode.management", func, [this.id, ...args], {...data})
    }

    async addMoveLine(data) {
        await this._callBackend(data, "add_stock_move_line")
    }

    async addLocationToLines(data) {
        await this._callBackend(data, "add_stock_location");
        if (this.barcodeState.recentScan !== "stock.location" && this.barcodeState.pickingType === "internal") {
            this.showNotification("Source location has been applied to scanned products/package, now you can scan destination location if you want to.", 'success')
        }
    }

    async assignBarcode(data) {
        const {lastScannedProduct} = this.barcodeState
        const args = lastScannedProduct ? [lastScannedProduct[0]] : []
        await this._callBackend(data, "assign_barcode_move_line", args);
    }

    async assignPackage(data) {
        await this._callBackend(data, "assign_package_move_line");
    }

    async backToMain() {
        await this.actionService.doAction('barcode_for_community.custom_barcode_action')
    }
}

CustomBarcodeLocation.template = "barcode_for_community.BarcodeLocation";
CustomBarcodeLocation.components = {
    CustomBarcodeLocationLines
}
actionRegistry.add('custom_location_client_action', CustomBarcodeLocation);