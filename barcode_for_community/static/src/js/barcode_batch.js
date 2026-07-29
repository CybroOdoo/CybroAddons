/** @odoo-module */
import {registry} from "@web/core/registry";
import {BarcodeDialog} from "./barcode_dialog";
import {Component, useState, onWillStart, useRef, useEffect} from "@odoo/owl";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import {useBus, useService} from "@web/core/utils/hooks";
import {jsonrpc} from "@web/core/network/rpc_service";
import {ChoosePicking} from "./choosePicking";

const DEFAULT_FUNCTIONS = [
    'action_main_menu', 'action_validate',
    'action_cancel', 'action_put_in_pack',
    'print_batch']

const actionRegistry = registry.category("actions");

export class CustomBarcodeBatch extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            batches: []
        })
        this.actionService = useService("action")
        onWillStart(async () => await this.getBatchTransfers())


    }

    handleGoBack() {
        window.history.go(-1)
    }

    /**
     * Function for opening the transfer view
     */
    _onClickOpenTransfer(id, name) {
        localStorage.setItem('custom-barcode-batch-transfer', id)
        this.actionService.doAction({
            type: "ir.actions.client",
            name: name,
            tag: "custom_batch_lines_client_action",
            target: "current",
        })
    }

    /**
     * Function for opening the wizard
     */
    OpenBatchTransfer(ev, id, name) {
        ev.stopPropagation()
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: name,
            res_model: 'stock.picking.batch',
            res_id: id,
            target: "current",
            views: [
                [false, "form"]
            ],
        })
    }

    /**
     * Function for getting all records of batch transfer
     */
    async getBatchTransfers() {
        this.state.batches = await this.orm.searchRead(
            "stock.picking.batch", [
                ["state", "=", 'in_progress']
            ], ["name", "id", "picking_type_id", "scheduled_date"]
        )
    }
}

CustomBarcodeBatch.template = "barcode_for_community.BarcodeBatchTransfer";
actionRegistry.add('custom_batch_client_action', CustomBarcodeBatch);

export class CustomBarcodeMoveLines extends Component {
    setup() {
        this.actionService = useService("action")
        this.state = useState({
            line: this.props.line
        })
        this.orm = useService("orm")
        this.root = useRef("MoveLine-root")
        this.dialog = useService("dialog");
    }

    handleEdit() {
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Stock Move Line',
            target: 'new',
            res_model: "stock.move.line",
            res_id: this.props.line.id,
            views: [
                [false, 'form']
            ],
        }, {
            onClose: async () => await this.actionService.doAction('soft_reload')
        })
    }

    handleDelete(){
        this.dialog.add(ConfirmationDialog, {
            body: _t("Are you sure you want to delete this record?"),
            confirm: () => this.deleteConfirm(),
            cancel: () => {},
        });
    }

    async deleteConfirm(){
        await this.orm.unlink('stock.move.line', [this.props.line.id])
        await this.actionService.doAction('soft_reload');
    }

    /**
     * Function for invisible the modal
     */
    _onClickDiscardChanges() {
        this.root.el.querySelector('#BatchLineModal').style.display = 'none'
        this.root.el.querySelector('.input_for_quantity').value = this.state.line.quantity_product_uom
        this.is_float = false;
    }

    /**
     * Function for adding number to value of the input box
     */
    _onclickNumber(number) {
        if (!this.is_float) {
            this.root.el.querySelector('.input_for_quantity').value = this.root.el.querySelector('.input_for_quantity').value + number
        } else {
            this.root.el.querySelector('.input_for_quantity').value = Number(this.root.el.querySelector('.input_for_quantity').value) + "." + Number(number)
            this.is_float = false;
        }
    }

    /**
     * Function for increment or decrement the quantity of the record by 1
     */
    _onClickDialOperation(operation) {
        if (operation == 'add') {
            this.root.el.querySelector('.input_for_quantity').value = Number(this.root.el.querySelector('.input_for_quantity').value) + 1
        } else {
            this.root.el.querySelector('.input_for_quantity').value = Number(this.root.el.querySelector('.input_for_quantity').value) - 1
        }
        this.is_float = false;
    }

    /**
     * Function for applying the decimal value in the quantity
     */
    _onClickDialDecimal() {
        if (this.root.el.querySelector('.input_for_quantity').value.indexOf('.') === -1) {
            this.is_float = true;
        }
    }

    /**
     * Function for opening the wizard
     */
    _onClickOpenWizard(model, id) {
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Product',
            target: 'current',
            res_model: model,
            res_id: Number(id),
            views: [
                [false, 'form']
            ],
        })
    }

    /**
     * Function for apply button in the modal for changing the quantity of the record
     */
    async _onClickApplyChanges(value) {
        const lot_name = this.state.line.tracking !== 'none' ? this.root.el.querySelector('.input_for_batch_serial_number').value : ''
        this.state.line.quantity_product_uom = value
        await this.orm.write('stock.move.line', [this.state.line.id], {
            'quantity': Number(value),
            'lot_name': lot_name
        })
        this.root.el.querySelector('#BatchLineModal').style.display = 'none'
        this.is_float = false;
        await this.actionService.doAction('soft_reload');
    }

    /**
     * Function for removing the last value from input value
     */
    _onClickDialRemove() {
        var value = this.root.el.querySelector('.input_for_quantity').value
        if (value) {
            if (value.charAt(value.length - 2) == '.') {
                this.root.el.querySelector('.input_for_quantity').value = value.slice(0, -2);
            } else {
                this.root.el.querySelector('.input_for_quantity').value = value.slice(0, -1);
            }
        }
        this.is_float = false;
    }
}

CustomBarcodeMoveLines.template = "barcode_for_community.CustomBarcodeMoveLines";

export class CustomBarcodeBatchLines extends Component {
    setup() {
        this.user = useService('user');
        this.id = this.props.action.params.id || this.props.action.params.active_id
        this.orm = useService("orm");
        this.rpc = useService("rpc");
        this.dialog = useService("dialog");
        this.root = useRef("BarcodeTransferLine-Root");
        this.notification = useService("notification")
        this.sound = useService("barcodeSound");
        this.state = useState({
            data: {},
            move_line: [],
            temp_product_response: {},// Stores the response if the scanned product/serial does not exist in the move line
            temp_picking_ids: []
        })
        this.barcodeState = useState({
            recentScan: false,
            lastScanTracking: false,
            message: "",
            lastScannedProduct: false,
            pickingType: ""
        })
        const barcode = useService("barcode");
        this.actionService = useService("action")
        this.locations = false
        onWillStart(async () => await this.getData())
        useBus(barcode.bus, "barcode_scanned", (ev) => this.ReadBarcode(ev.detail.barcode));
        onWillStart(async () => {
            var data = await jsonrpc('/barcode-batch/location-package', {})
            this.group_stock_tracking_lot = data.package
            this.group_stock_multi_locations = data.location
        })
        useEffect(() => {
            this.env.bus.trigger("TOGGLE_NAVBAR:HIDE", {show: false})
            return () => {
                this.env.bus.trigger("TOGGLE_NAVBAR:HIDE", {show: true})
            }
        })
    }

    showNotification(message = "", type = "danger", sticky = false, sound = true) {
        this.notification.add(message, {
            type,
            sticky,
        })
        if (sound) this.sound.Alert.play()
    }

    async fetchScannedData(barcode, batch_id = this.id) {
        return await this.rpc("/barcode/barcode-scanned", {
            barcode, picking_id: false, batch_id
        })
    }
    /**
     * Function for navigating to main menu page
     */
    action_main_menu() {
        return this.actionService.doAction({
            type: "ir.actions.client",
            name: 'Barcode',
            tag: "custom_barcode_tags",
            target: "fullscreen",
        })
    }
    /**
     * Function for validate function in batch transfer
     */
    async action_validate(){
        await this.doActionButton("action_done", {
            skip_backorder: true,
            skip_sms: true,
        });
    }

    _onClickActionValidate(){
        this.action_validate()
    }
    /**
     * Function for printing the batch transfer
     */
    async print_batch() {
        const response = await jsonrpc('/inventory_commands', {
            code: "print_batch",
            id: this.id
        })
        if (typeof response === "object") {
            this.actionService.doAction(response)
        }
    }
    /**
     * Function for cancelling the batch transfer
     */
    async action_cancel() {
        await this.doActionButton("action_cancel", {}, false)
        this.notification.add('The operation has been canceled.', {
            type: "warning",
            sticky: false,
        })
        this._onClickExit()
    }
    /**
     * Function for putting in the pack
     */
    async action_put_in_pack() {
        await this.doActionButton("action_put_in_pack", {}, false)
        this.showNotification("Pack is assigned to the scanned products", "success")
        await this.notify()
    }

    async doActionButton(name, context = {}, reload = true) {
        const action = {
            type: "object",
            resId: this.id,
            name,
            resModel: "stock.picking.batch",
            onClose: () => reload && this.actionService.doAction('soft_reload')
        }
        if (context) {
            action["context"] = context;
        }
        await this.actionService.doActionButton(action);
    }

    async processBatchScan(response) {
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

    async _processProductScan(response) {
        switch (response.res_model) {
            case "product.product":
                if (this.barcodeState.lastScanTracking === "lot" && this.barcodeState.lastScannedProduct[0] !== response.data[0].id) {
                    return this.showNotification("Please scan a Lot number before scanning new products")
                }
                if (this.barcodeState.lastScanTracking === "serial") {
                    return this.showNotification("Please scan a serial number before scanning new products")
                } else if (["lot", "none"].includes(this.barcodeState.lastScanTracking)) {
                    await this.applyPicking(response)
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
                this.assignRecent("", "")
                break;
            case "stock.lot":
                if (["serial", "lot"].includes(this.barcodeState.lastScanTracking)) {
                    await this.assignBarcode(response)
                } else await this.applyPicking(response)
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
                await this.applyPicking(response)
                return this.assignRecent(response.res_model, response.data[0].tracking, [response.data[0].id])
            case "stock.lot":
                await this.applyPicking(response)
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
                this.showNotification("You can't reassign Serial/Lot.")
                break;
            case "product.product":
                await this.applyPicking(response)
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

    openPickingModal() {
        this.dialog.add(ChoosePicking, this.getPickingProps)
    }

    async _callBackend(func, args = [], kwargs = {}) {
        await this.orm.call("barcode.management", func, args, {...kwargs,  rec_model: "stock.picking.batch", rec_model_id: this.id});
    }

    async applyPicking(response) {
        await this._callBackend("add_stock_move_line", [response.exist_picking_ids[0]], response)
    }

    assignRecent(model, tracking, product = false) {
        this.barcodeState.recentScan = model;
        this.barcodeState.lastScanTracking = model === "product.product" ? tracking : ""
        this.barcodeState.lastScannedProduct = product
    }

    async assignPackage(response) {
        const {picking_ids} = this.state.data
        await this._callBackend("assign_package_move_line_batch", [picking_ids], response);
    }

    async addLocationToLines(response) {
        const {picking_ids} = this.state.data
        await this._callBackend("add_stock_location_batch", [picking_ids], response);
        if (this.barcodeState.recentScan !== "stock.location" && this.barcodeState.pickingType === "internal") {
            this.showNotification("Source location has been applied to scanned products/package, now you can scan destination location if you want to.", 'success')
        }
    }

    async _processDefaultScan(response) {
        if (["product.product", "stock.lot"].includes(response.res_model)) {
            await this.applyPicking(response)
            let product = response.res_model === "product.product" ? [response.data[0].id] : false
            this.assignRecent(response.res_model, response.data[0].tracking, product)
        } else return this.showNotification("Scan Products or Serial number first")
    }

    async assignBarcode(response) {
        const {lastScannedProduct} = this.barcodeState
        await this._callBackend("assign_barcode_move_line", [response.exist_picking_ids[0], lastScannedProduct[0]], response);
    }

    async assignPicking(pickingId) {
        await this._callBackend("add_stock_move_line", [pickingId], this.state.temp_product_response);
        const {data} =  this.state.temp_product_response
        this.assignRecent(this.state.temp_product_response.res_model, data[0].tracking, [data[0].id])
        this.state.temp_picking_ids = [];
        this.state.temp_product_response = {}

        await this.notify()
    }

    get getPickingProps() {
    return {
        pickingIds: this.state.temp_picking_ids.length
            ? this.state.temp_picking_ids
            : (this.state.temp_product_response
                ? this.state.temp_product_response.picking_ids
                : this.state.data.picking_ids),
        assignPicking: this.assignPicking.bind(this),
        }
    }

    /**
     * Function works when the barcode catches the barcode code and passing the code to python
     */
    async ReadBarcode(barcode) {
        barcode = String(barcode, "")
        if (DEFAULT_FUNCTIONS.includes(barcode)) {
            if (typeof this[barcode] === "function") {
                this[barcode]()
            }
        } else {
            const response = await this.fetchScannedData(barcode)
            if (!response.is_error) {
                if (!["serial", "lot"].includes(this.barcodeState.lastScanTracking) && response.res_model === 'product.product' || (response.res_model === 'stock.lot' && this.barcodeState.recentScan !== "product.product") || (response.res_model === 'product.product' && !response.product_exist)) {
                    if (!response.product_exist) {
                        this.state.temp_product_response = response // store the response in temp
                        return this.openPickingModal()
                    } else if (response.product_exist && response.exist_in_many_picking) {
                        this.state.temp_product_response = response
                        this.state.temp_picking_ids = response.exist_picking_ids || [];
                        return this.openPickingModal()
                    }
                }
                if (this.barcodeState.recentScan === "product.product" && ["serial", "lot"].includes(this.barcodeState.lastScanTracking) && response.res_model === "stock.lot") {
                    await this.assignBarcode(response)
                    this.assignRecent(response.res_model, "")
                    await this.notify()
                } else {
                    await this.processBatchScan(response)
                    await this.notify()
                }
            } else this.showNotification("Nothing has been found for this barcode")
        }
    }


    /**
     * Function works return to the previous menu
     */
    _onClickExit() {
        this.env.config.breadcrumbs.length > 1 ? this.env.config.historyBack() : window.history.go(-1)
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
     * Function for put in pack function in batch transfer
     */
    _onClickActionPackage() {
        this.action_put_in_pack()
    }

    /**
     * Function for displaying the data in the batch transfer view
     */
    async getData() {
        const [response] = await this.orm.call("stock.picking.batch", "get_barcode_batch", [this.id])
        this.state.data = {
            'name': response.name,
            'picking_type_id': response.picking_type_id[0],
            'picking_type': response.picking_type,
            'state': response.state
        }
        if (response) {
            this.barcodeState.recentScan = response.barcode_recent_scan
            this.barcodeState.lastScanTracking = response.last_scan_tracking
            this.barcodeState.lastScannedProduct = response.last_scanned_product
            this.barcodeState.pickingType = response.picking_type
        }
        await this.notify()

    }

    async notify() {
        this.state.move_line = await this.orm.call("stock.picking.batch", "get_barcode_batch_move_line", [this.id])
        this.state.data.picking_ids = this.state.move_line.reduce((acc, item) => {
            if (!acc.includes(item.picking_id[0])) {
                acc.push(item.picking_id[0]);
            }
            return acc;
        }, []);
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
}

CustomBarcodeBatchLines.template = "barcode_for_community.BarcodeBatchTransferLines";
CustomBarcodeBatchLines.components = {
    CustomBarcodeMoveLines
}
actionRegistry.add('custom_batch_lines_client_action', CustomBarcodeBatchLines);