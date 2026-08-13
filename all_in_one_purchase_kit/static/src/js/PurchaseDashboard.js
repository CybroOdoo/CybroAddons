/* @odoo-module*/
import {registry} from '@web/core/registry';
import {Component, useRef, useState, onWillStart, onMounted} from '@odoo/owl'
import {useService} from "@web/core/utils/hooks";
import {PurchaseTiles} from './purchaseTile'
import {_t} from "@web/core/l10n/translation";

/**
 * Class representing the purchase dashboard component.
 */
class purchaseDashboard extends Component {
    setup() {
        /**
         * State variable for purchase-related data.
         * @type {Object}
         */
        this.purchase = useState({})
        this.action = useService('action')
        this.selectedVendor = useState({selected: null})
        this.root = useRef('root');
        this.orm = useService('orm')

        this.chartInstances = {
            productAnalysis: null,
            vendorAnalysis: null,
            byMonthPurchase: null,
            topProduct: null,
        };

        onWillStart(async () => {
            this.purchase.monthlyData = await this.orm.call('purchase.order', 'get_orders_by_month', [])
            this.purchase.orders = await this.orm.call('purchase.order', 'get_monthly_data', ['this_month'])
            this.purchase.pending = await this.orm.call('purchase.order', 'get_pending_purchase_data', [])
            this.purchase.upcoming = await this.orm.call('purchase.order', 'get_upcoming_purchase_data', [])
            this.purchase.topChart = await this.orm.call('purchase.order', 'get_top_chart_data', ['top_product'])
            this.purchase.vendors = await this.orm.call('purchase.order', 'purchase_vendors', [])
            this.purchase.categoryAnalysis = await this.orm.call('purchase.order.line', 'product_categ_analysis', [])
            this.selectedVendor.selected = this.purchase.vendors.length !== 0 ? this.purchase.vendors[0].id : 0;
            await this.getRenderVendorAnalysisData()
        })
        onMounted(() => {
            this.renderProductAnalysis();
            this.renderVendorAnalysis();
            this.renderByMonthPurchase();
            this.renderTopProduct();
        });
    }

    /**
     * Handler for selecting a mode.
     * @param {Object} event - The event object.
     */
    async handleOnchangeSelect(event) {
        const option = event.target.value;
        this.purchase.orders = await this.orm.call('purchase.order', 'get_select_mode_data', [option])
    }

    /**
     * Handler for changing the product category.
     * @param {Object} event - The event object.
     */
    async handleOnChangeProductCategory(event) {
        const category_id = parseInt(event.target.value);
        const {count, name} = await this.orm.call('purchase.order.line', 'product_categ_data', [category_id])
        this.purchase.categoryAnalysis.values.name = name;
        this.purchase.categoryAnalysis.count = count;
        this.renderProductAnalysis()
    }

    /**
     * Render the product analysis chart.
     */
    renderProductAnalysis() {
        const ctx = this.root.el.querySelector("#product_categ_purchases");
        if (!ctx) return; // Guard against missing canvas
        if (this.chartInstances.productAnalysis) {
            this.chartInstances.productAnalysis.destroy();
        }
        const label = this.purchase.categoryAnalysis.values.name.map((obj) => obj.en_US);
        const count = this.purchase.categoryAnalysis.count;
        this.chartInstances.productAnalysis = new Chart(ctx, {
            type: 'line',
            data: {
                labels: label,
                datasets: [{
                    label: 'Quantity Done',
                    data: count,
                    backgroundColor: '#003f5c',
                    borderColor: '#003f5c',
                    borderWidth: 1,
                    fill: false
                }]
            },
            options: {
                scales: {y: {beginAtZero: true}},
                responsive: true,
                maintainAspectRatio: false,
            }
        });
    }

    /**
     * Fetch and render vendor analysis data.
     */
    async getRenderVendorAnalysisData() {
        this.purchase.renderVendorAnalysisData = await this.orm.call('purchase.order', 'purchase_vendor_details', [this.selectedVendor.selected])
    }

    /**
     * Handler for changing the vendor analysis.
     * @param {Object} event - The event object.
     */
    async handleOnChangeVendorAnalysis(event) {
        this.selectedVendor.selected = parseInt(event.target.value)
        await this.getRenderVendorAnalysisData()
        this.renderVendorAnalysis()
    }

    /**
     * Render the vendor analysis chart.
     */
    renderVendorAnalysis() {
        const ctx = this.root.el.querySelector("#purchase_vendors");
        if (!ctx) return;
        if (this.chartInstances.vendorAnalysis) {
            this.chartInstances.vendorAnalysis.destroy();
        }
        const name = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const {
            purchase_amount,
            po_count,
            draft_amount,
            draft_count,
            approve_amount,
            approve_count,
            cancel_amount,
            cancel_count
        } = this.purchase.renderVendorAnalysisData;
        this.chartInstances.vendorAnalysis = new Chart(ctx, {
            type: 'line',
            data: {
                labels: name,
                datasets: [
                    {
                        label: 'Purchase Order Total',
                        data: purchase_amount,
                        backgroundColor: '#0000ff',
                        borderColor: '#0000ff',
                        borderWidth: 1,
                        fill: false
                    },
                    {
                        label: 'Draft Order Total',
                        data: draft_amount,
                        backgroundColor: '#71d927',
                        borderColor: '#71d927',
                        borderWidth: 1,
                        fill: false
                    },
                    {
                        label: 'To Approve',
                        data: approve_amount,
                        backgroundColor: '#ff0066',
                        borderColor: '#ff0066',
                        borderWidth: 1,
                        fill: false
                    },
                    {
                        label: 'Cancelled Orders',
                        data: cancel_amount,
                        backgroundColor: '#ffff1a',
                        borderColor: '#ffff1a',
                        borderWidth: 1,
                        fill: false
                    },
                ]
            },
            options: {
                scales: {y: {beginAtZero: true}},
                responsive: true,
                maintainAspectRatio: false,
            }
        });
    }

    /**
     * Render the purchase data by month.
     */
    renderByMonthPurchase() {
        const ctx = this.root.el.querySelector("#canvas");
        if (!ctx) return;
        if (this.chartInstances.byMonthPurchase) {
            this.chartInstances.byMonthPurchase.destroy();
        }
        const month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const count = this.purchase.monthlyData.count;
        this.chartInstances.byMonthPurchase = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: month,
                datasets: [{
                    label: 'Count',
                    data: count,
                    backgroundColor: '#ac3973',
                    borderColor: '#ac3973',
                    borderWidth: 1,
                    type: 'bar',
                    fill: false
                }]
            },
            options: {
                scales: {y: {beginAtZero: true}},
                responsive: true,
                maintainAspectRatio: false,
            }
        });
    }

    /**
     * Handler for changing the top product.
     * @param {Object} event - The event object.
     */
    async handleOnChangeTopProduct(event) {
        const selected_id = event.target.value;
        this.purchase.topChart = await this.orm.call('purchase.order', 'get_top_chart_data', [selected_id])
        this.renderTopProduct()
    }

    /**
     * Render the top product chart.
     */
    renderTopProduct() {
        const ctx = this.root.el.querySelector(".top_pie_chart");
        if (!ctx) return; // Guard against missing canvas
        // Destroy the previous chart instance if it exists
        if (this.chartInstances.topProduct) {
            this.chartInstances.topProduct.destroy();
        }

        const label = this.purchase.topChart[1].map((item) => item.en_US || item);
        const datas = this.purchase.topChart[0];
        const background_color = datas.map(() => '#' + Math.floor(Math.random() * 16777215).toString(16));

        const data = {
            labels: label,
            datasets: [{
                label: "",
                data: datas,
                backgroundColor: background_color,
                borderColor: background_color,
                borderWidth: 1
            }]
        };

        const options = {
            responsive: true,
            title: {display: false},
            legend: {
                display: true,
                position: "right",
                labels: {fontColor: "#333", fontSize: 16}
            },
            scales: {
                yAxes: [{
                    gridLines: {color: "rgba(0, 0, 0, 0)", display: false},
                    ticks: {min: 0, display: false}
                }]
            }
        };

        // Create the new chart instance and store it
        this.chartInstances.topProduct = new Chart(ctx, {
            type: "doughnut",
            data: data,
            options: options
        });
    }

    /**
     * Navigate to the backend for purchase orders.
     */
    goBackend() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: _t('Purchase Order'),
            res_model: 'purchase.order',
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            target: 'self',
            domain: [['state', 'in', ['purchase', 'done']], ['id', 'in', this.purchase.orders.purchase_orders_ids]],
        });
    }

    /**
     * Handle priority orders.
     */
    priorityOrders() {
        if (this.priority_orders) {
            var options = {
                on_reverse_breadcrumb: self.on_reverse_breadcrumb,
            };
        }
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: _t("Priority Order"),
            res_model: 'purchase.order',
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            target: 'self',
            domain: [['priority', '=', 1], ['id', 'in', this.purchase.orders.priority_orders_ids]],
        });
    }

    /**
     * Navigate to the vendor backend.
     */
    vendorBackend() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: _t('Vendor'),
            res_model: 'res.partner',
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            target: 'self',
            domain: [['id', "in", this.purchase.orders.vendor_id]],
        });
    }
}

/**
 * Template for the purchase dashboard component.
 */
purchaseDashboard.template = 'PurchaseDashboard'
purchaseDashboard.components = {
    PurchaseTiles
}
registry.category('actions').add('purchase_dashboard', purchaseDashboard);
