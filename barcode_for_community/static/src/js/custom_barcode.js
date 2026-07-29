/** @odoo-module */
import {registry} from "@web/core/registry";
import {Component, useState, useRef, onWillStart} from "@odoo/owl";
import {useService, useBus} from "@web/core/utils/hooks";
import {BarcodeDialog} from "./barcode_dialog";
import {jsonrpc} from "@web/core/network/rpc_service";
import {Dropdown} from "@web/core/dropdown/dropdown";
import {DropdownItem} from "@web/core/dropdown/dropdown_item";

const actionRegistry = registry.category("actions");

export class CustomBarcode extends Component {
    setup() {
        const barcode = useService("barcode");
        this.root = useRef('BarcodeRoot')
        this.actionService = useService("action")
        this.companyService = useService("company");
        this.sound = useService("barcodeSound");
        this.notification = useService("notification")
        this.dialog = useService("dialog");
        this.menuService = useService("menu");
        this.orm = useService("orm")
        this.user = useService("user");
        this.state = useState({
            types: [],
            index: 4
        })

        useBus(barcode.bus, "barcode_scanned", (ev) => this.ReadBarcode(ev.detail.barcode))
        onWillStart(async () => {
            await this.getOperationTypes()
        });
    }

    getMenuItemHref(payload) {
        const parts = [`menu_id=${payload.id}`];
        if (payload.actionID) {
            parts.push(`action=${payload.actionID}`);
        }
        return "#" + parts.join("&");
    }

    onNavBarDropdownItemSelection(menu) {
        if (menu) {
            this.menuService.selectMenu(menu);
        }
    }

    /**
     * Function for all operations types in the corresponding company
     */
    async getOperationTypes() {
        const StockOperation = await this.orm.searchRead(
            "stock.picking.type", [
                ["company_id", "=", this.companyService.currentCompany.id],
                ["code", "!=", "mrp_operation"]
            ], ["name"]
        );
        const operationData = [];
        for (let i = 0; i < StockOperation.length; i++) {
            var PickingDraft = await this.orm.searchCount(
                "stock.picking", [
                    ["picking_type_id", "=", StockOperation[i].id],
                    ["state", "=", 'draft']
                ])
            var PickingReady = await this.orm.searchCount(
                "stock.picking", [
                    ["picking_type_id", "=", StockOperation[i].id],
                    ["state", "=", 'assigned']
                ])
            var PickingDone = await this.orm.searchCount(
                "stock.picking", [
                    ["picking_type_id", "=", StockOperation[i].id],
                    ["state", "=", 'done']
                ])
            operationData.push({
                'id': StockOperation[i].id,
                'name': StockOperation[i].name,
                PickingDraft,
                PickingReady,
                PickingDone
            })
        }
        this.state.types = operationData;
    }

    /**
     * Function works when the barcode catches the barcode code and passing the code to python
     */
    async ReadBarcode(barcode) {
        barcode = String(barcode)
        this.currentCompany = this.companyService.currentCompany;
        const StockPicking = await this.orm.searchRead(
            "stock.picking", [
                ["name", "=", barcode]
            ], ["name", "id",]
        )
        const PickingBatch = await this.orm.searchRead(
            "stock.picking.batch", [
                ["name", "=", barcode]
            ], ["name", "id",]
        )
        if (PickingBatch.length > 0) {
            var id = PickingBatch[0].id
            var name = PickingBatch[0].name
            localStorage.setItem('custom-barcode-batch-transfer', id)
            this.actionService.doAction({
                type: "ir.actions.client",
                name: name,
                tag: "custom_batch_lines_client_action",
                target: "current"
            })
        } else if (StockPicking.length > 0) {
            var id = StockPicking[0].id
            var name = StockPicking[0].name
            localStorage.setItem('custom-barcode-inventory', id)
            localStorage.setItem('custom-barcode-inventory-type', 'stock-picking')
            this.actionService.doAction({
                type: "ir.actions.client",
                name: name,
                tag: "custom_location_client_action",
                target: "current",
                params: {
                    id
                }
            })
        } else if (barcode === 'action_scrap') {
            this.actionService.doAction({
                name: 'Scrap',
                type: 'ir.actions.act_window',
                res_model: 'stock.scrap',
                views: [
                    [false, 'form']
                ],
                view_mode: 'form',
                target: 'self',
            })
        } else {
            var data = await jsonrpc('/barcode/main-barcode', {
                'code': barcode,
                'company_id': this.companyService.currentCompany.id,
            })
            if (data.type === 'product') {
                this.actionService.doAction({
                    type: 'ir.actions.act_window',
                    res_model: 'stock.quant',
                    domain: [
                        ["product_id", "=", data.id]
                    ],
                    view_mode: 'tree',
                    name: data.name,
                    views: [
                        [false, 'tree']
                    ],
                    target: 'current'
                })
            } else if (data.type === 'operation_type') {
                localStorage.setItem('custom-barcode-inventory', data.stock_transfer_id)
                localStorage.setItem('custom-barcode-inventory-type', data.type)
                this.actionService.doAction({
                    type: "ir.actions.client",
                    name: data.stock_transfer_name,
                    tag: "custom_location_client_action",
                    target: "current",
                    params: {
                        id: data.stock_transfer_id
                    }
                })
            } else if (data.type === 'location') {
                localStorage.setItem('custom-barcode-inventory', data.stock_transfer_id)
                localStorage.setItem('custom-barcode-inventory-type', data.type)
                this.actionService.doAction({
                    type: "ir.actions.client",
                    name: data.stock_transfer_name,
                    tag: "custom_location_client_action",
                    target: "current",
                    params: {
                        id: data.stock_transfer_id
                    }
                })
            } else {
                this.sound.Alert.play()
                this.notification.add('Please scan the product or location or document', {
                    type: "warning",
                    sticky: false,
                })
            }
        }
    }

    /**
     * Function for opening the view for the corresponding operation types
     */
    _onClickOperation(operation_id, name) {
        localStorage.setItem('custom-barcode-operation-type', operation_id)
        localStorage.setItem('custom-barcode-operation-name', name)
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            res_model: 'stock.picking',
            domain: [
                ["picking_type_id", "=", Number(operation_id)],
                ["state", "=", "assigned"],
                "|",
                ["user_id", "=", this.user.userId],
                ["user_id", "=", false]
            ],
            view_mode: 'kanban',
            name: name,
            views: [
                [false, 'kanban']
            ],
            target: 'main',
            context: {
                'kanban_view_ref': 'barcode_for_community.view_stock_picking_kanban'
            }
        })
    }

    /**
     * Function for opening batch view
     */
    _onClickOpenBatch() {
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            res_model: 'stock.picking.batch',
            domain: [
                ["state", "=", "in_progress"],
                "|",
                ["user_id", "=", this.user.userId],
                ["user_id", "=", false]
            ],
            view_mode: 'kanban',
            name: "Batch Transfers",
            views: [
                [false, 'kanban']
            ],
            target: 'main',
            context: {
                'kanban_view_ref': 'barcode_for_community.view_stock_picking_batch_kanban'
            }
        });
    }

    /**
     * Function for opening product quantity view
     */
    _onClickOpenInventoryAdjustment() {
        this.actionService.doAction({
            type: "ir.actions.client",
            name: 'Inventory Adjustment',
            tag: "custom_adjustment_client_action",
            target: "current",
        })
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

    get availableOperations() {
        return this.state.types.slice(0, this.state.index)
    }

    get hasShowMore() {
        const showMore = this.state.types.length
        return showMore > 4 && this.state.index < showMore
    }

    handleShowMore() {
        if (this.isSmall) {
            const maxIndex = this.state.types.length;
            this.state.index = Math.min(this.state.index + 6, maxIndex);
        } else {
            this.root.el.querySelector('#BarcodeMainModal').style.display = 'block'
        }
    }

    get isSmall() {
        return this.env.isSmall
    }
}

CustomBarcode.template = "barcode_for_community.Barcode";
CustomBarcode.components = {Dropdown, DropdownItem}
actionRegistry.add('custom_barcode_tags', CustomBarcode);