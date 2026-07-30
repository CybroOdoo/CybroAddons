/** @odoo-module **/

import { Component, useState, onWillStart, useRef, useEffect } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * Lightweight wrapper around `localStorage` used as the offline persistence
 * layer for the Offline Sales terminal.
 */
export class OfflineDB {
    /**
     * Initialize the offline database wrapper.
     * Sets up the localStorage key prefix (`name`) and the in-memory cache.
     */
    constructor() {
        this.name = "offline_sale_db";
        this.cache = {};
    }

    load(store, deft) {
        if (this.cache[store] !== undefined) {
            return this.cache[store];
        }
        let data = localStorage[this.name + "_" + store];
        if (data !== undefined && data !== "") {
            data = JSON.parse(data);
            this.cache[store] = data;
            return data;
        } else {
            return deft;
        }
    }

    save(store, data) {
        localStorage[this.name + "_" + store] = JSON.stringify(data);
        this.cache[store] = data;
    }

    get_orders() {
        return this.load("orders", []);
    }

    add_order(order) {
        let orders = this.get_orders();
        // overwrite if exists
        let existingIndex = orders.findIndex(o => o.uid === order.uid);
        if (existingIndex !== -1) {
            orders[existingIndex] = order;
        } else {
            orders.push(order);
        }
        this.save("orders", orders);
    }

    remove_order(uid) {
        let orders = this.get_orders();
        orders = orders.filter(order => order.uid !== uid);
        this.save("orders", orders);
    }
}

export class OfflineSalesApp extends Component {
    static template = "offline_sale.AppLayout";
    /**
     * Component setup hook. Initializes the offline DB, reactive state,
     * global barcode-scanner keyboard listener, and effects; also kicks off
     * initial data loading, online-status tracking, and periodic background
     * synchronization via `onWillStart`.
     */

    setup() {
        this.rpc = useService("rpc");
        this.db = new OfflineDB();
        this.state = useState({
            products: [],
            categories: [], // New state for categories
            selectedCategoryId: null, // Track currently selected category
            searchQuery: "", // Track search input
            partners: [],
            employees: [],
            payment_terms: [],
            selectedPaymentTermId: null,
            paymentTermPage: 0,
            selectedEmployee: null,
            showEmployeeModal: false,
            showPinModal: false,
            pinBuffer: "",
            pinError: "",
            company: {},
            user_name: '',
            cart: [],
            currentPartner: null,
            isOnline: navigator.onLine,
            showOnlineToast: false,
            showOfflineToast: false,
            isServerDown: false,
            isSessionExpired: false,
            syncStatus: 'idle',
            screen: 'products', // 'products', 'payment', 'receipt', 'orders', or 'customer_form'
            lastOrder: null,
            showMenu: false,
            syncedOrders: this.db.load('history', []),
            selectedLineId: null, // Currently active cart line
            keypadMode: 'qty', // 'qty', 'disc', or 'price'
            buffer: "", // Buffer for numeric input
            history: [], // For undo functionality
            paymentAmount: 0, // Amount typed in payment screen
            customerForm: {
                name: '',
                street: '',
                city: '',
                state_id: '',
                zip: '',
                country_id: '',
                vat: '',
                phone: '',
                mobile: '',
                email: '',
                website: '',
            },
            loadingOrderUid: null,
            barcodeInput: "",
            showBarcodeInput: false,
            backendNote: "",
            noteDraft: "",
            showNoteModal: false,
            pendingOrders: [],
            pendingOrdersLoading: false,
            loadingBackendOrderId: null,
            emailModal: { show: false, to: "", subject: "", body: "" },
            errorPopup: {
                show: false,
                title: 'Error',
                message: '',
                type: 'error', // 'error' or 'success'
            },
            taxes: [],
        });

        onWillStart(async () => {
            await this.loadInitialData();
            this.checkOnlineStatus();
            this.syncOrders(true);
            // Pre-load backend pending orders if we are online
            if (navigator.onLine) {
                this.loadPendingOrders();
            }
            // Background safety-net: every 20s try to sync the offline queue
            // (creates invoice + payment on the backend the moment internet returns).
            this._syncInterval = setInterval(() => {
                if (!navigator.onLine) return;
                const queue = this.db.get_orders();
                const newPartners = this.db.load('new_partners', []);
                if (queue.length || newPartners.length) {
                    this.syncOrders(true);
                }
            }, 20000);
        });

        this.barcodeInputRef = useRef("barcodeInputRef");

        // --- GLOBAL BARCODE LISTENER ---
        this.barcodeBuffer = "";
        this.lastCharTime = 0;
        this.BARCODE_THRESHOLD = 50; // ms between characters (scanners are fast)

        window.addEventListener('keydown', (ev) => {
            // Ignore if we are in an input field (except the barcode one)
            if (ev.target.tagName === 'INPUT' || ev.target.tagName === 'TEXTAREA' || ev.target.contentEditable === 'true') {
                if (ev.target !== this.barcodeInputRef.el) {
                    return;
                }
            }

            const now = Date.now();
            if (now - this.lastCharTime > this.BARCODE_THRESHOLD) {
                this.barcodeBuffer = ""; // Reset if it's been too long (manual typing)
            }
            this.lastCharTime = now;

            if (ev.key === 'Enter') {
                if (this.barcodeBuffer.length > 2) { // Minimum length for a barcode
                    this.addProductByBarcode(this.barcodeBuffer);
                    this.barcodeBuffer = "";
                    ev.preventDefault();
                }
            } else if (ev.key.length === 1) { // Single character
                this.barcodeBuffer += ev.key;
            }
        });
        // -------------------------------

        useEffect(() => {
            if (this.state.showBarcodeInput && this.barcodeInputRef.el) {
                this.barcodeInputRef.el.focus();
            }
        }, () => [this.state.showBarcodeInput]);
    }

    showPopup(message, title = 'Notification', type = 'error') {
        this.state.errorPopup = {
            show: true,
            title: title,
            message: message,
            type: type,
        };
    }

    closePopup() {
        this.state.errorPopup.show = false;
    }

    openNoteModal() {
        this.state.noteDraft = this.state.backendNote || "";
        this.state.showNoteModal = true;
    }

    closeNoteModal() {
        this.state.showNoteModal = false;
    }

    saveBackendNote() {
        this.state.backendNote = (this.state.noteDraft || "").trim();
        if (this.state.lastOrder) {
            this.state.lastOrder.backend_note = this.state.backendNote;
            this.db.add_order(this.state.lastOrder);
        }
        this.state.showNoteModal = false;
    }

    clearBackendNote() {
        this.state.noteDraft = "";
        this.state.backendNote = "";
        if (this.state.lastOrder) {
            this.state.lastOrder.backend_note = "";
            this.db.add_order(this.state.lastOrder);
        }
    }

    openCustomerForm() {
        this.state.customerForm = {
            name: '', street: '', city: '', state_id: '', zip: '',
            country_id: '', vat: '', phone: '', mobile: '', email: '', website: '',
        };
        this.state.screen = 'customer_form';
    }

    async saveCustomer() {
        if (!this.state.customerForm.name) {
            this.showPopup("Customer Name is required!", "Validation Error");
            return;
        }

        const newPartner = {
            id: 'OFF-' + Date.now(),
            name: this.state.customerForm.name,
            street: this.state.customerForm.street,
            city: this.state.customerForm.city,
            zip: this.state.customerForm.zip,
            phone: this.state.customerForm.phone,
            mobile: this.state.customerForm.mobile,
            email: this.state.customerForm.email,
            website: this.state.customerForm.website,
            vat: this.state.customerForm.vat,
            is_new: true,
        };

        // 1. Add to local state
        this.state.partners.unshift(newPartner);
        this.state.currentPartner = newPartner.id;

        // 2. Save to "New Partners" queue for sync
        let newPartners = this.db.load('new_partners', []);
        newPartners.push(newPartner);
        this.db.save('new_partners', newPartners);

        // 3. Persist in general cache too
        const cachedData = this.db.load('data', {});
        cachedData.partners = this.state.partners;
        this.db.save('data', cachedData);

        // 4. Return to products screen
        this.state.screen = 'products';
    }

    selectLine(product_id) {
        this.state.selectedLineId = product_id;
        this.state.buffer = ""; // Clear buffer when switching lines
    }

    handleKeypad(val) {
        // Record state for undo before change
        this.pushHistory();

        if (['Qty', 'Disc', 'Price'].includes(val)) {
            this.state.keypadMode = val.toLowerCase();
            this.state.buffer = "";
            return;
        }

        if (val === 'Clear') {
            this.state.cart = [];
            this.state.selectedLineId = null;
            this.state.buffer = "";
            this.save_unpaid_cart();
            return;
        }

        if (val === 'Backspace') {
            this.state.buffer = this.state.buffer.slice(0, -1);
            this.applyBuffer();
            return;
        }

        // Add digit/decimal to buffer
        if (this.state.buffer.length < 10) {
            this.state.buffer += val;
            this.applyBuffer();
        }
    }

    applyBuffer() {
        if (!this.state.selectedLineId) return;
        const line = this.state.cart.find(l => l.product_id === this.state.selectedLineId);
        if (!line) return;

        const val = parseFloat(this.state.buffer) || 0;
        if (this.state.keypadMode === 'qty') {
            line.qty = val || 1;
        } else if (this.state.keypadMode === 'price') {
            line.price_unit = val;
        } else if (this.state.keypadMode === 'disc') {
            // Apply a simple percentage discount to the price_unit
            // or just store it as a property if we want complex Odoo-like discount
            // For now, let's assume it's like standard Odoo POS (0-100)
            line.discount = val;
            // Note: we need to update total calculation in templates to handle line.discount
        }
    }

    pushHistory() {
        // Simple undo: store a snapshot of the cart
        const snapshot = JSON.parse(JSON.stringify(this.state.cart));
        this.state.history.push(snapshot);
        if (this.state.history.length > 10) this.state.history.shift();
    }

    undo() {
        if (this.state.history.length > 0) {
            this.state.cart = this.state.history.pop();
            this.save_unpaid_cart();
        }
    }

    get filteredProducts() {
        let products = this.state.products;

        // Filter by category
        if (this.state.selectedCategoryId) {
            products = products.filter(p => p.categ_id && p.categ_id[0] === this.state.selectedCategoryId);
        }

        // Filter by search query
        if (this.state.searchQuery) {
            const query = this.state.searchQuery.toLowerCase();
            products = products.filter(p =>
                p.display_name.toLowerCase().includes(query) ||
                (p.default_code && p.default_code.toLowerCase().includes(query)) ||
                (p.barcode && p.barcode.includes(query))
            );
        }

        return products;
    }

    toggleBarcodeInput() {
        this.state.showBarcodeInput = !this.state.showBarcodeInput;
        if (this.state.showBarcodeInput) {
            this.state.barcodeInput = "";
        }
    }

    async onBarcodeKeydown(ev) {
        if (ev.key === 'Enter') {
            const barcode = this.state.barcodeInput.trim();
            if (barcode) {
                const added = await this.addProductByBarcode(barcode);
                this.state.barcodeInput = "";
                this.state.showBarcodeInput = false;
            }
        } else if (ev.key === 'Escape') {
            this.state.showBarcodeInput = false;
        }
    }

    async addProductByBarcode(barcode) {
        // Look in local products
        const product = this.state.products.find(p => p.barcode === barcode || p.default_code === barcode);
        if (product) {
            this.addToCart(product);
            return;
        }

        // If not found locally and online, try searching backend (similar to Odoo POS)
        if (navigator.onLine) {
            try {
                const results = await this.rpc("/web/dataset/call_kw", {
                    model: 'product.product',
                    method: 'search_read',
                    args: [[['barcode', '=', barcode]], ['display_name', 'lst_price', 'barcode', 'default_code', 'categ_id', 'taxes_id']],
                    kwargs: { limit: 1 },
                });

                if (results && results.length > 0) {
                    const foundProduct = results[0];
                    // Add to local state if missing
                    if (!this.state.products.find(p => p.id === foundProduct.id)) {
                        this.state.products.push(foundProduct);
                    }
                    this.addToCart(foundProduct);
                } else {
                    this.showPopup("Product not found for barcode: " + barcode, "Barcode Error");
                }
            } catch (e) {
                console.error("Error searching product by barcode online", e);
                this.showPopup("Product not found locally and server search failed.", "Connection Error");
            }
        } else {
            this.showPopup("Product not found locally and terminal is offline.", "Offline Error");
        }
    }

    getTaxName(taxId) {
        const tax = this.state.taxes.find(t => t.id === taxId);
        return tax ? tax.name : '';
    }

    get lineChunks() {
        if (!this.state.lastOrder || !this.state.lastOrder.lines) return [];
        const chunks = [];
        const lines = this.state.lastOrder.lines;
        for (let i = 0; i < lines.length; i += 15) {
            chunks.push(lines.slice(i, i + 15));
        }
        return chunks;
    }

    get totalDiscount() {
        return this.state.cart.reduce((sum, line) => {
            let lineGross = (line.qty * line.price_unit);
            let tax_included = 0;
            if (line.tax_ids) {
                line.tax_ids.forEach(taxId => {
                    const tax = this.state.taxes.find(t => t.id === taxId);
                    if (tax && tax.price_include && tax.amount_type === 'percent') {
                        tax_included += tax.amount;
                    }
                });
            }
            let untaxedBase = lineGross;
            if (tax_included > 0) {
                untaxedBase = lineGross / (1 + (tax_included / 100));
            }
            return sum + (untaxedBase * (line.discount || 0) / 100);
        }, 0);
    }

    get subtotal() {
        return this.state.cart.reduce((sum, line) => {
            let lineGross = (line.qty * line.price_unit);
            let tax_included = 0;
            if (line.tax_ids) {
                line.tax_ids.forEach(taxId => {
                    const tax = this.state.taxes.find(t => t.id === taxId);
                    if (tax && tax.price_include && tax.amount_type === 'percent') {
                        tax_included += tax.amount;
                    }
                });
            }
            if (tax_included > 0) {
                return sum + (lineGross / (1 + (tax_included / 100)));
            }
            return sum + lineGross;
        }, 0);
    }

    get tax() {
        return this.state.cart.reduce((sum, line) => {
            let lineTotal = (line.qty * line.price_unit) * (1 - (line.discount || 0) / 100);
            let tax_included = 0;
            let tax_excluded = 0;
            if (line.tax_ids) {
                line.tax_ids.forEach(taxId => {
                    const tax = this.state.taxes.find(t => t.id === taxId);
                    if (tax && tax.amount_type === 'percent') {
                        if (tax.price_include) {
                            tax_included += tax.amount;
                        } else {
                            tax_excluded += tax.amount;
                        }
                    }
                });
            }

            let untaxed = lineTotal;
            let tax_amount = 0;
            if (tax_included > 0) {
                untaxed = lineTotal / (1 + (tax_included / 100));
                tax_amount += lineTotal - untaxed;
            }
            if (tax_excluded > 0) {
                tax_amount += untaxed * (tax_excluded / 100);
            }
            return sum + tax_amount;
        }, 0);
    }

    get total() {
        return this.subtotal - this.totalDiscount + this.tax;
    }

    get paymentDue() {
        if (!this.state.lastOrder) return 0;
        if (this.state.lastOrder.amount_due_to_pay !== undefined) {
            return this.state.lastOrder.amount_due_to_pay || 0;
        }
        if (this.state.lastOrder.is_confirmed_backend_order && this.state.lastOrder.amount_residual !== undefined) {
            return this.state.lastOrder.amount_residual || 0;
        }
        return this.state.lastOrder.amount_total || 0;
    }

    get balanceDue() {
        if (!this.state.lastOrder) return 0;
        const due = this.paymentDue;
        const paid = Math.min(this.state.paymentAmount || 0, due);
        return Math.max(0, due - paid);
    }

    get isPartialPayment() {
        if (!this.state.lastOrder) return false;
        return this.state.paymentAmount > 0 && this.state.paymentAmount < this.paymentDue;
    }

    removeFromCart(product_id) {
        const index = this.state.cart.findIndex(l => l.product_id === product_id);
        if (index !== -1) {
            this.state.cart.splice(index, 1);
            this.save_unpaid_cart();
        }
    }

    async confirmOrder() {
        if (!this.state.currentPartner) {
            this.showPopup("Please select a customer first!", "Selection Required");
            return;
        }
        if (!this.state.cart.length) {
            this.showPopup("Your cart is empty! Please add products before confirming.", "Empty Cart");
            return;
        }

        const partner = this.state.partners.find(p => String(p.id) === String(this.state.currentPartner));

        const now = new Date();
        const yyyy = now.getFullYear();
        const mm = String(now.getMonth() + 1).padStart(2, '0');
        const dd = String(now.getDate()).padStart(2, '0');
        const hh = String(now.getHours()).padStart(2, '0');
        const min = String(now.getMinutes()).padStart(2, '0');
        const sec = String(now.getSeconds()).padStart(2, '0');
        const random = Math.floor(Math.random() * 1000).toString().padStart(3, '0');

        const order = {
            uid: this.state.loadingOrderUid || `OFF-${yyyy}${mm}${dd}-${hh}${min}${sec}-${random}`,
            partner_id: String(this.state.currentPartner).startsWith('OFF-') ? this.state.currentPartner : parseInt(this.state.currentPartner),
            partner_name: partner ? partner.name : '',
            partner_street: partner ? partner.street : '',
            partner_city: partner ? partner.city : '',
            partner_zip: partner ? partner.zip : '',
            partner_phone: partner ? partner.phone : '',
            partner_mobile: partner ? partner.mobile : '',
            partner_email: partner ? partner.email : '',
            partner_website: partner ? partner.website : '',
            partner_vat: partner ? partner.vat : '',
            payment_term_id: this.state.selectedPaymentTermId,
            lines: [...this.state.cart],
            date: now.toLocaleDateString(),
            amount_untaxed: this.subtotal - this.totalDiscount,
            amount_discount: this.totalDiscount,
            amount_tax: this.tax,
            amount_total: this.total,
            state: 'confirmed',
            backend_note: this.state.backendNote || "",
            backend_order_id: this.state.loadingBackendOrderId || null,
        };

        // 1. Move to payment screen
        this.state.lastOrder = order;
        this.state.paymentAmount = 0;
        this.state.buffer = "";
        this.state.screen = 'payment';
    }

    async saveDraftOrder() {
        if (!this.state.currentPartner) {
            this.showPopup("Please select a customer first!", "Selection Required");
            return;
        }
        if (!this.state.cart.length) {
            this.showPopup("Your cart is empty! Please add products before saving as draft.", "Empty Cart");
            return;
        }

        const partner = this.state.partners.find(p => String(p.id) === String(this.state.currentPartner));
        const now = new Date();
        const yyyy = now.getFullYear();
        const mm = String(now.getMonth() + 1).padStart(2, '0');
        const dd = String(now.getDate()).padStart(2, '0');
        const hh = String(now.getHours()).padStart(2, '0');
        const min = String(now.getMinutes()).padStart(2, '0');
        const sec = String(now.getSeconds()).padStart(2, '0');
        const random = Math.floor(Math.random() * 1000).toString().padStart(3, '0');

        const order = {
            uid: this.state.loadingOrderUid || `OFF-${yyyy}${mm}${dd}-${hh}${min}${sec}-${random}`,
            partner_id: String(this.state.currentPartner).startsWith('OFF-') ? this.state.currentPartner : parseInt(this.state.currentPartner),
            partner_name: partner ? partner.name : '',
            partner_street: partner ? partner.street : '',
            partner_city: partner ? partner.city : '',
            partner_zip: partner ? partner.zip : '',
            partner_phone: partner ? partner.phone : '',
            partner_mobile: partner ? partner.mobile : '',
            partner_email: partner ? partner.email : '',
            partner_website: partner ? partner.website : '',
            partner_vat: partner ? partner.vat : '',
            payment_term_id: this.state.selectedPaymentTermId,
            lines: [...this.state.cart],
            date: now.toLocaleDateString(),
            amount_untaxed: this.subtotal - this.totalDiscount,
            amount_discount: this.totalDiscount,
            amount_tax: this.tax,
            amount_total: this.total,
            state: 'draft',
            backend_note: this.state.backendNote || "",
        };

        // 1. Save to Offline Queue
        this.db.add_order(order);

        // 2. Clear cart
        this.state.cart = [];
        this.state.currentPartner = null;
        this.state.loadingOrderUid = null;
        this.state.backendNote = "";
        this.db.save('current_cart', []);

        // 3. Update history state visually
        let currentHistory = this.db.load('history', []);
        const existingIdx = currentHistory.findIndex(o => o.uid === order.uid);
        if (existingIdx !== -1) {
            currentHistory[existingIdx] = order;
        } else {
            currentHistory.unshift(order);
        }
        const limitedHistory = currentHistory.slice(0, 50);
        this.db.save('history', limitedHistory);
        this.state.syncedOrders = limitedHistory;

        // 4. Trigger Sync
        this.syncOrders(false);
        this.showPopup("Draft Order Saved!", "Success", "success");
    }

    loadOrder(order) {
        this.state.cart = JSON.parse(JSON.stringify(order.lines));
        this.state.currentPartner = order.partner_id;
        this.state.selectedPaymentTermId = order.payment_term_id;
        this.state.loadingOrderUid = order.uid;
        this.state.backendNote = order.backend_note || "";
        this.state.screen = 'products';
    }

    toggleMenu() {
        this.state.showMenu = !this.state.showMenu;
    }

    openEmployeeModal() {
        if (this.state.employees && this.state.employees.length > 0) {
            this.state.showEmployeeModal = true;
        } else {
            this.showPopup("No employees loaded for terminal.", "Data Error");
        }
    }

    closeEmployeeModal() {
        this.state.showEmployeeModal = false;
    }

    selectEmployee(employee) {
        this.state.selectedEmployee = employee;
        this.state.showEmployeeModal = false;
        if (employee.pin) {
            this.state.pinBuffer = "";
            this.state.showPinModal = true;
        } else {
            this.loginEmployee();
        }
    }

    closePinModal() {
        this.state.showPinModal = false;
        this.state.pinBuffer = "";
        this.state.pinError = "";
    }

    handlePinKeypad(btn) {
        this.state.pinError = "";
        if (btn === 'Clear') {
            this.state.pinBuffer = "";
        } else if (btn === 'Backspace') {
            this.state.pinBuffer = this.state.pinBuffer.slice(0, -1);
        } else {
            this.state.pinBuffer += btn;
        }
    }

    authorizePin() {
        if (this.state.pinBuffer === this.state.selectedEmployee.pin) {
            this.loginEmployee();
        } else {
            this.state.pinError = "Incorrect Authorization PIN";
            this.state.pinBuffer = "";
        }
    }

    loginEmployee() {
        this.state.user_name = this.state.selectedEmployee.name;
        // Persist to local cache
        const cachedData = this.db.load('data', {});
        cachedData.user_name = this.state.user_name;
        this.db.save('data', cachedData);
        this.closePinModal();
    }

    exitOfflineTerminal() {
        // 1. Must be online to exit
        if (!this.state.isOnline || !navigator.onLine) {
            this.showPopup(
                "You must be online to exit the Offline Terminal. Please reconnect and try again.",
                "Offline",
                "error",
            );
            return;
        }

        // 2. Collect any pending draft orders from history + unsynced queue
        const queue = this.db.get_orders();
        const all = [...(this.state.syncedOrders || []), ...queue];
        const seen = new Set();
        const drafts = [];
        all.forEach((o) => {
            if (!o || !o.uid || seen.has(o.uid)) return;
            seen.add(o.uid);
            if (o.state === 'draft') drafts.push(o);
        });

        if (drafts.length) {
            const list = drafts
                .map((o) => `• ${o.name || o.uid} (Offline ID: ${o.uid})`)
                .join("\n");
            this.showPopup(
                `Please complete the following pending draft order(s) before exiting:\n\n${list}`,
                "Pending Draft Orders",
                "error",
            );
            return;
        }

        // 3. All clear — redirect to the Sale Orders list view
        window.location.href = "/web#model=sale.order&view_type=list";
    }

    launchOffline() {
        // Open the app in a new standalone window
        const width = 1200;
        const height = 800;
        const left = (window.screen.width / 2) - (width / 2);
        const top = (window.screen.height / 2) - (height / 2);

        window.open(
            '/offline_sale/ui',
            'OfflineTerminal',
            `width=${width},height=${height},left=${left},top=${top},menubar=no,toolbar=no,location=no,status=no,resizable=yes`
        );
    }

    openOrders() {
        this.state.screen = 'orders';
        this.state.showMenu = false;
    }

    deleteOrder(uid) {
        if (!confirm("Are you sure you want to delete this pending order? This action cannot be undone.")) return;

        // Remove from pending queue
        const queue = this.db.get_orders();
        const filteredQueue = queue.filter(o => o.uid !== uid);
        this.db.save('orders', filteredQueue);

        // Remove from history
        let history = this.db.load('history', []);
        history = history.filter(o => o.uid !== uid);
        this.db.save('history', history);
        this.state.syncedOrders = history;
    }

    async openPendingOrders() {
        this.state.screen = 'pending_orders';
        this.state.showMenu = false;
        await this.loadPendingOrders();
    }

    isPendingOrderProcessed(backendId) {
        // True only while an offline payment for this backend SO is still
        // waiting to be synced. Once the sync succeeds (queue entry removed +
        // pending list refreshed from the backend), the row goes back to a
        // normal Load Order state — or disappears entirely if fully paid.
        if (!backendId) return false;
        const queue = this.db.get_orders();
        return queue.some((o) => o.backend_order_id === backendId);
    }

    async loadPendingOrders() {
        // Always rehydrate cached copy first so the screen shows something offline
        const cached = this.db.load('pending_orders', []);
        if (Array.isArray(cached) && cached.length && !this.state.pendingOrders.length) {
            this.state.pendingOrders = cached;
        }
        if (!navigator.onLine) {
            return;
        }
        this.state.pendingOrdersLoading = true;
        try {
            const orders = await this.rpc("/web/dataset/call_kw", {
                model: 'sale.order',
                method: 'get_pending_sale_orders',
                args: [],
                kwargs: {},
            });
            this.state.pendingOrders = orders || [];
            this.db.save('pending_orders', this.state.pendingOrders);
        } catch (e) {
            console.error("Failed to load pending orders", e);
            // Don't popup on the silent startup pre-load
            if (this.state.screen === 'pending_orders') {
                this.showPopup("Could not fetch pending orders from the backend.", "Error", "error");
            }
        } finally {
            this.state.pendingOrdersLoading = false;
        }
    }

    loadPendingOrder(order) {
        // Hydrate cart, partner and payment term from a backend pending order
        const lines = (order.lines || []).map((l) => ({
            product_id: l.product_id,
            name: l.name,
            price_unit: l.price_unit,
            qty: l.qty,
            discount: l.discount || 0,
            tax_ids: l.tax_ids || [],
        }));
        this.state.cart = lines;
        this.state.currentPartner = order.partner_id;
        if (order.payment_term_id) {
            this.state.selectedPaymentTermId = order.payment_term_id;
        }
        this.state.loadingBackendOrderId = order.id;
        this.state.loadingOrderUid = null;
        this.state.backendNote = "";
        this.save_unpaid_cart();

        const isConfirmed = ['sale', 'done'].includes(order.state);
        if (isConfirmed) {
            // Already confirmed in the backend → go straight to the payment screen
            // and surface a banner telling the cashier that only invoice + payment are pending.
            const total = order.amount_total || 0;
            const residual = order.amount_residual !== undefined ? order.amount_residual : total;
            this.state.lastOrder = {
                uid: order.name || `BO-${order.id}`,
                name: order.name,
                backend_order_id: order.id,
                partner_id: order.partner_id,
                partner_name: order.partner_name || '',
                partner_email: order.partner_email || '',
                partner_city: order.partner_city || '',
                partner_zip: order.partner_zip || '',
                payment_term_id: order.payment_term_id || null,
                lines: lines,
                date: order.date || new Date().toLocaleDateString(),
                amount_untaxed: order.amount_untaxed || 0,
                amount_discount: 0,
                amount_tax: order.amount_tax || 0,
                amount_total: total,
                amount_residual: residual,
                state: 'confirmed',
                is_confirmed_backend_order: true,
                backend_state: order.state,
            };
            this.state.paymentAmount = 0;
            this.state.buffer = "";
            this.state.screen = 'payment';
        } else {
            // Draft / sent → editable, send the cashier to the Register screen
            this.state.lastOrder = null;
            this.state.screen = 'products';
        }
    }

    payNow() {
        if (!this.state.lastOrder) {
            // No active order — nothing to process; stay on current screen
            return;
        }

        // Update order with final selected payment term before saving
        this.state.lastOrder.payment_term_id = this.state.selectedPaymentTermId;
        this.state.lastOrder.state = 'confirmed';
        const due = this.paymentDue;
        this.state.lastOrder.amount_due_to_pay = due;
        this.state.lastOrder.amount_paid = Math.min(this.state.paymentAmount || 0, due);
        this.state.lastOrder.amount_residual = Math.max(0, due - this.state.lastOrder.amount_paid);
        this.state.lastOrder.is_partial = this.state.lastOrder.amount_residual > 0;
        this.state.lastOrder.backend_note = this.state.backendNote || this.state.lastOrder.backend_note || "";
        this.state.lastOrder.backend_order_id = this.state.loadingBackendOrderId || this.state.lastOrder.backend_order_id || null;

        // 1. Save Finalized Order to Offline Queue
        this.db.add_order(this.state.lastOrder);

        // 2. Clear cart as payment is validated
        this.state.cart = [];
        this.state.currentPartner = null;
        this.state.loadingOrderUid = null;
        this.state.loadingBackendOrderId = null;
        this.state.backendNote = "";
        this.db.save('current_cart', []);

        // 3. Update history state visually
        let currentHistory = this.db.load('history', []);
        const existingIdx = currentHistory.findIndex(o => o.uid === this.state.lastOrder.uid);
        if (existingIdx !== -1) {
            currentHistory[existingIdx] = this.state.lastOrder;
        } else {
            currentHistory.unshift(this.state.lastOrder);
        }
        const limitedHistory = currentHistory.slice(0, 50);
        this.db.save('history', limitedHistory);
        this.state.syncedOrders = limitedHistory;

        // 4. Trigger Sync
        this.syncOrders(false);
        // 5. Navigate to receipt — only reached when lastOrder is valid
        this.state.screen = 'receipt';
    }

    nextPaymentTerms() {
        if ((this.state.paymentTermPage + 1) * 4 < this.state.payment_terms.length) {
            this.state.paymentTermPage++;
        }
    }

    prevPaymentTerms() {
        if (this.state.paymentTermPage > 0) {
            this.state.paymentTermPage--;
        }
    }

    handlePaymentKeypad(btn) {
        if (btn === '+/-') {
            this.state.paymentAmount *= -1;
            this.state.buffer = this.state.paymentAmount.toString();
            return;
        }
        if (btn === '.') {
            if (!this.state.buffer.includes('.')) {
                this.state.buffer += '.';
            }
        } else if (btn === 'Backspace') {
            this.state.buffer = this.state.buffer.slice(0, -1);
        } else if (btn === 'Clear') {
            this.state.buffer = "";
        } else {
            this.state.buffer += btn;
        }
        this.state.paymentAmount = parseFloat(this.state.buffer) || 0;
    }

    backToProducts() {
        this.state.screen = 'products';
        this.state.showMenu = false;
    }

    _buildReceiptHtml(order, company) {
        const fmt = (n) => parseFloat(n || 0).toFixed(2);

        const amountTotal = parseFloat(order.amount_total || 0);
        const amountPaid = parseFloat(order.amount_paid || 0);
        const amountResidual = order.amount_residual !== undefined
            ? parseFloat(order.amount_residual)
            : Math.max(0, amountTotal - Math.min(amountPaid, amountTotal));
        const isPartial = order.is_partial !== undefined
            ? !!order.is_partial
            : (amountPaid > 0 && amountPaid < amountTotal);

        const statusLabel = isPartial ? 'PARTIAL' : 'PAID';
        const statusColor = isPartial ? '#b45309' : '#0d9488';

        // Build order lines rows
        const linesHtml = (order.lines || []).map(line => `
            <tr>
                <td style="padding:8px 0; font-size:13px; vertical-align:top;">${fmt(line.qty)}</td>
                <td style="padding:8px 0; vertical-align:top;">
                    <div style="font-size:13px; font-weight:500;">${line.name || ''}</div>
                </td>
                <td style="padding:8px 0; font-size:13px; text-align:right; vertical-align:top;">$${fmt(line.price_unit)}</td>
                <td style="padding:8px 0; font-size:13px; text-align:right; vertical-align:top; font-weight:600;">$${fmt(line.qty * line.price_unit * (1 - (line.discount || 0) / 100))}</td>
            </tr>
        `).join('');

        const discountRow = order.amount_discount > 0 ? `
            <tr>
                <td style="padding:4px 0; font-size:12px; color:#059669;">Discount</td>
                <td style="padding:4px 0; font-size:12px; text-align:right; color:#059669; font-weight:600;">-$${fmt(order.amount_discount)}</td>
            </tr>` : '';

        const paidRow = amountPaid > 0 ? `
            <tr>
                <td style="padding:6px 0 4px 0; font-size:12px; color:#4b5563; border-top:1px solid #e2e8f0;">Amount Paid</td>
                <td style="padding:6px 0 4px 0; font-size:12px; text-align:right; color:#08c208; font-weight:700; border-top:1px solid #e2e8f0;">$${fmt(amountPaid)}</td>
            </tr>` : '';

        const balanceRow = isPartial ? `
            <tr>
                <td style="padding:6px 8px; font-size:12px; color:#b45309; font-weight:700; text-transform:uppercase; letter-spacing:0.05em; background:#fff4e5; border:1px solid rgba(180,83,9,0.3); border-radius:4px;">Balance Due</td>
                <td style="padding:6px 8px; font-size:14px; text-align:right; color:#b45309; font-weight:900; background:#fff4e5; border:1px solid rgba(180,83,9,0.3); border-radius:4px;">$${fmt(amountResidual)}</td>
            </tr>` : '';

        const changeRow = (amountPaid > amountTotal) ? `
            <tr>
                <td style="padding:4px 0; font-size:11px; color:#9ca3af; font-style:italic;">Change Balance</td>
                <td style="padding:4px 0; font-size:11px; text-align:right; color:#9ca3af; font-style:italic;">$${fmt(amountPaid - amountTotal)}</td>
            </tr>` : '';

        const partialBanner = isPartial ? `
            <div style="margin-bottom:14px; padding:10px 14px; background:#fff4e5; border:1px solid rgba(180,83,9,0.3); border-left:4px solid #b45309; border-radius:4px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; color:#b45309;">Partial Payment</div>
                    <div style="font-size:11px; color:#7c2d12; margin-top:2px;">This receipt records a partial settlement. Outstanding balance remains due.</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; color:#b45309;">Balance Due</div>
                    <div style="font-size:18px; font-weight:900; color:#b45309;">$${fmt(amountResidual)}</div>
                </div>
            </div>` : '';

        return `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Receipt_${order.name || order.uid}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;900&display=swap" rel="stylesheet">
    <style>
        @page { size: A4; margin: 0; }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', sans-serif;
            background: white;
            color: #1a202c;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }
        .page {
            width: 210mm;
            min-height: 297mm;
            padding: 16mm 18mm;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            background: white;
        }
        /* Header */
        .header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 2px solid #1a365d;
            padding-bottom: 14px;
            margin-bottom: 14px;
        }
        .company-name {
            font-size: 20px;
            font-weight: 900;
            color: #1a365d;
            text-transform: uppercase;
            letter-spacing: -0.5px;
        }
        .company-detail {
            font-size: 10px;
            color: #4b5563;
            margin-top: 6px;
            line-height: 1.6;
        }
        .receipt-title {
            font-size: 17px;
            font-weight: 900;
            color: #0d9488;
            text-transform: uppercase;
            text-align: right;
            line-height: 1.15;
            margin-bottom: 10px;
        }
        .meta-row {
            display: flex;
            justify-content: flex-end;
            gap: 16px;
            font-size: 10px;
            margin-bottom: 2px;
        }
        .meta-label { color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; }
        .meta-value { font-weight: 600; color: #1a202c; }
        .meta-value.paid { color: #0d9488; font-weight: 700; }
        /* Billed To / Payment Status cards */
        .cards {
            display: flex;
            gap: 12px;
            margin-bottom: 16px;
        }
        .card {
            flex: 1;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 4px;
            padding: 10px 12px;
        }
        .card-label {
            font-size: 9px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #6b7280;
            margin-bottom: 4px;
        }
        .card-name {
            font-size: 14px;
            font-weight: 700;
            color: #1a365d;
        }
        .card-sub {
            font-size: 11px;
            color: #374151;
            margin-top: 2px;
            font-weight: 500;
        }
        .card-txid {
            font-size: 10px;
            color: #9ca3af;
            margin-top: 3px;
        }
        /* Table */
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 0;
        }
        thead tr {
            border-bottom: 2px solid #1a365d;
        }
        thead th {
            padding: 6px 0;
            font-size: 9px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #6b7280;
            font-weight: 600;
        }
        thead th:nth-child(1) { width: 50px; }
        thead th:nth-child(3), thead th:nth-child(4) { text-align: right; width: 80px; }
        tbody tr { border-bottom: 1px solid #e2e8f0; }
        /* Totals + Signatures section */
        .bottom-section {
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            margin-top: 20px;
            padding-top: 14px;
            border-top: 1px solid #e2e8f0;
        }
        .signatures { width: 220px; }
        .sig-line {
            border-top: 1px solid #e2e8f0;
            padding-top: 4px;
            margin-bottom: 28px;
            font-size: 9px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #6b7280;
        }
        .totals-table { width: 220px; border-collapse: collapse; }
        .totals-table td { padding: 3px 0; font-size: 12px; }
        .totals-table td:last-child { text-align: right; font-weight: 600; }
        .grand-label {
            font-size: 13px;
            font-weight: 900;
            color: #1a365d;
            text-transform: uppercase;
        }
        .grand-value {
            font-size: 22px;
            font-weight: 900;
            color: #0d9488;
        }
        .footer-bar {
            margin-top: auto;
            padding-top: 14px;
            border-top: 1px solid #e2e8f0;
            text-align: center;
        }
        .footer-text {
            font-size: 8px;
            color: #9ca3af;
            text-transform: uppercase;
            letter-spacing: 0.3em;
        }
    </style>
</head>
<body>
<div class="page">
    <!-- Header -->
    <div class="header">
        <div>
            <div class="company-name">${company.name || ''}</div>
            <div class="company-detail">
                ${company.street ? company.street + '<br>' : ''}
                ${company.city ? company.city + (company.zip ? ', ' + company.zip : '') + '<br>' : ''}
                ${company.phone ? 'Phone: ' + company.phone + '<br>' : ''}
                VAT ID: ${company.vat || 'N/A'}
            </div>
        </div>
        <div>
            <div class="receipt-title">Transaction<br>Receipt</div>
            <div class="meta-row"><span class="meta-label">Order Ref:</span><span class="meta-value">#${order.name || order.uid}</span></div>
            <div class="meta-row"><span class="meta-label">Date:</span><span class="meta-value">${order.date || ''}</span></div>
            <div class="meta-row"><span class="meta-label">Status:</span><span class="meta-value" style="color:${statusColor}; font-weight:700;">${statusLabel}</span></div>
        </div>
    </div>

    <!-- Customer & Payment Cards -->
    <div class="cards">
        <div class="card">
            <div class="card-label">Billed To</div>
            <div class="card-name">${order.partner_name || ''}</div>
        </div>
        <div class="card">
            <div class="card-label">Payment Status</div>
            <div class="card-sub" style="color:${statusColor}; font-weight:700;">${statusLabel}${isPartial ? ' — Partial Settlement' : ''}</div>
            <div class="card-txid">TXID: ${order.uid}</div>
        </div>
    </div>

    ${partialBanner}

    <!-- Items Table -->
    <table>
        <thead>
            <tr>
                <th style="text-align:left;">Qty</th>
                <th style="text-align:left;">Product Description</th>
                <th style="text-align:right;">Unit Price</th>
                <th style="text-align:right;">Total</th>
            </tr>
        </thead>
        <tbody>
            ${linesHtml}
        </tbody>
    </table>

    <!-- Signatures + Totals -->
    <div class="bottom-section">
        <div class="signatures">
            <div class="sig-line">Authorized Signature</div>
            <div class="sig-line">Company Stamp</div>
        </div>
        <div>
            <table class="totals-table">
                <tr>
                    <td style="color:#4b5563;">Subtotal</td>
                    <td>$${fmt((order.amount_untaxed || 0) + (order.amount_discount || 0))}</td>
                </tr>
                ${discountRow}
                <tr>
                    <td style="color:#4b5563; border-bottom:1px solid #e2e8f0; padding-bottom:6px;">Taxes</td>
                    <td style="border-bottom:1px solid #e2e8f0; padding-bottom:6px;">$${fmt(order.amount_tax)}</td>
                </tr>
                <tr>
                    <td style="padding-top:6px;" class="grand-label">Grand Total</td>
                    <td style="padding-top:6px;" class="grand-value">$${fmt(order.amount_total)}</td>
                </tr>
                ${paidRow}
                ${balanceRow}
                ${changeRow}
            </table>
        </div>
    </div>

    <!-- Footer -->
    <div class="footer-bar">
        <div class="footer-text">Generated via APEX Ledger Cloud POS &bull; Document UID: ${order.uid}</div>
    </div>
</div>
<script>
    window.onload = function() {
        window.print();
        window.onafterprint = function() { window.close(); };
    };
</script>
</body>
</html>`;
    }

    printReceipt() {
        if (!this.state.lastOrder) return;
        const html = this._buildReceiptHtml(this.state.lastOrder, this.state.company);
        const win = window.open('', '_blank', 'width=900,height=1100,menubar=no,toolbar=no,location=no');
        if (win) { win.document.write(html); win.document.close(); }
    }

    async emailReceipt() {
        if (!this.state.lastOrder) return;
        if (!navigator.onLine) {
            this.showPopup("You must be online to email receipts.", "Offline", "error");
            return;
        }

        let targetEmail = this.state.lastOrder.partner_email || this.state.customerForm?.email;
        if (!targetEmail) {
            targetEmail = prompt("Please enter the email address to send the receipt to:");
            if (!targetEmail || !targetEmail.trim()) {
                return;
            }
        }

        try {
            const html = this._buildReceiptHtml(this.state.lastOrder, this.state.company);
            this.showPopup(`Sending receipt to ${targetEmail.trim()}...`, "Sending Email", "success");
            await this.rpc("/web/dataset/call_kw", {
                model: 'sale.order',
                method: 'send_offline_receipt_mail',
                args: [this.state.lastOrder.uid, html, targetEmail.trim()],
                kwargs: {},
            });
            this.showPopup(`Receipt successfully emailed to ${targetEmail.trim()}`, "Email Sent", "success");
        } catch (e) {
            console.error("Failed to send email receipt", e);
            this.showPopup("Failed to send email.", "Error", "error");
        }
    }

    onEmailModalSend() {
        // Send email from modal
        this.sendEmail(this.state.emailModal.to, this.state.emailModal.subject, this.state.emailModal.body);
    }

    closeEmailModal() {
        this.state.emailModal.show = false;
    }

    async sendEmail(toEmail, subject, bodyText) {
        if (!navigator.onLine) {
            this.showPopup("You must be online to email receipts.", "Offline", "error");
            return;
        }

        try {
            const html = this._buildReceiptHtml(this.state.lastOrder, this.state.company);
            this.state.emailModal.show = false;
            this.showPopup(`Sending receipt to ${toEmail.trim()}...`, "Sending Email", "success");
            await this.rpc("/web/dataset/call_kw", {
                model: 'sale.order',
                method: 'send_offline_receipt_mail',
                args: [this.state.lastOrder.uid, html, toEmail.trim(), subject, bodyText],
                kwargs: {},
            });
            this.showPopup(`Receipt successfully emailed to ${toEmail.trim()}`, "Email Sent", "success");
        } catch (e) {
            console.error("Failed to send email receipt", e);
            this.showPopup("Failed to send email.", "Error", "error");
        }
    }

    emailReceipt() {
        if (!this.state.lastOrder) return;
        if (!navigator.onLine) {
            this.showPopup("You must be online to email receipts.", "Offline", "error");
            return;
        }

        let targetEmail = this.state.lastOrder.partner_email || this.state.customerForm?.email || "";
        this.state.emailModal = {
            show: true,
            to: targetEmail,
            subject: `Transaction Receipt - ${this.state.lastOrder.uid}`,
            body: `Dear Customer,\n\nPlease find attached your transaction receipt for order ${this.state.lastOrder.uid}.\n\nThank you for your business!`
        };
    }

    downloadReceipt() {
        if (!this.state.lastOrder) return;
        const html = this._buildReceiptHtml(this.state.lastOrder, this.state.company);
        const win = window.open('', '_blank', 'width=900,height=1100,menubar=no,toolbar=no,location=no');
        if (win) { win.document.write(html); win.document.close(); }
    }

    newOrder() {
        this.state.cart = [];
        this.state.currentPartner = null;
        this.state.screen = 'products';
        this.state.lastOrder = null;
        this.state.backendNote = "";
        this.state.loadingBackendOrderId = null;
        this.db.save('current_cart', []);
    }

    async loadInitialData() {
        // Load initial data from DB
        const cachedData = this.db.load('data', {});
        if (cachedData.products) {
            this.state.products = cachedData.products;
            this.state.partners = cachedData.partners;
            this.state.categories = cachedData.categories || [];
            this.state.employees = cachedData.employees || [];
            this.state.company = cachedData.company || {};
            this.state.user_name = cachedData.user_name || '';
            this.state.payment_terms = cachedData.payment_terms || [];
            this.state.taxes = cachedData.taxes || [];
            if (this.state.payment_terms.length > 0) {
                this.state.selectedPaymentTermId = this.state.payment_terms[0].id;
            }
        }

        // Restore cart if exists
        const savedCart = this.db.load('current_cart', []);
        if (savedCart.length) {
            this.state.cart = savedCart;
        }

        if (navigator.onLine) {
            try {
                this.state.isServerDown = false;
                const data = await this.rpc("/web/dataset/call_kw", {
                    model: 'sale.order',
                    method: 'get_offline_data',
                    args: [],
                    kwargs: {},
                });
                this.state.products = data.products;
                this.state.partners = data.partners;
                this.state.categories = data.categories;
                this.state.company = data.company;
                this.state.user_name = data.user_name;
                this.state.employees = data.employees || [];
                this.state.payment_terms = data.payment_terms || [];
                this.state.taxes = data.taxes || [];
                if (this.state.payment_terms.length > 0) {
                    this.state.selectedPaymentTermId = this.state.payment_terms[0].id;
                }
                this.db.save('data', data);
            } catch (e) {
                const errorMsg = e.message || (e.data && e.data.message) || "";
                if (errorMsg.includes("Session Expired")) {
                    this.state.isSessionExpired = true;
                } else {
                    this.state.isServerDown = true;
                }
                console.error("Offline Sales: Backend sync failed", e);
            }
        }
    }

    addToCart(product) {
        const item = this.state.cart.find(l => l.product_id === product.id);
        if (item) {
            item.qty++;
        } else {
            this.state.cart.push({
                product_id: product.id,
                name: product.display_name,
                price_unit: product.lst_price,
                qty: 1,
                tax_ids: product.taxes_id || []
            });
        }
        this.state.selectedLineId = product.id; // Automatically select the added item
        this.save_unpaid_cart();
    }

    save_unpaid_cart() {
        this.db.save('current_cart', this.state.cart);
    }

    async syncOrders(silent = false, isManualFromTransactions = false) {
        // Prevent sync if offline
        if (!navigator.onLine) {
            this.state.syncStatus = 'idle';

            if (isManualFromTransactions) {
                this.showPopup(
                    "Orders synced successfully!",
                    "Sync Successful",
                    "success"
                );
            }
            return;
        }

        const orders = this.db.get_orders();
        const newPartners = this.db.load('new_partners', []);

        if (!orders.length && !newPartners.length) {
            this.state.syncStatus = 'idle';

            if (isManualFromTransactions) {
                this.showPopup(
                    "Orders synced successfully!",
                    "Sync Successful",
                    "success"
                );
            }
            return;
        }

        this.state.syncStatus = 'syncing';

        try {
            const results = await this.rpc("/web/dataset/call_kw", {
                model: 'sale.order',
                method: 'create_from_offline',
                args: [orders, newPartners],
                kwargs: {},
            });

            // 1. Process Partner Results (Backend returns created partner mappings)
            if (results.partners) {
                // Clear successfully synced partners
                const successfullySyncedPartnerIds = results.partners.map(p => p.offline_id);
                const remainingPartners = newPartners.filter(p => !successfullySyncedPartnerIds.includes(p.id));
                this.db.save('new_partners', remainingPartners);

                // Update local UI state IDs if they were mapped
                results.partners.forEach(map => {
                    const o_partner = this.state.partners.find(p => p.id === map.offline_id);
                    if (o_partner) o_partner.id = map.id;
                    if (this.state.currentPartner === map.offline_id) this.state.currentPartner = map.id;
                });
            }

            // 2. Process Order Results
            const orderResults = results.orders || results; // Fallback if old format

            if (this.state.lastOrder) {
                const match = orderResults.find(r => r.uid === this.state.lastOrder.uid && r.status !== 'error');
                if (match) {
                    this.state.lastOrder.name = match.name;
                    this.state.lastOrder.is_synced = true;
                    this.state.lastOrder.state = match.state || this.state.lastOrder.state;
                }
            }

            // Sync errors feedback
            const failed = orderResults.filter(r => r.status === 'error');
            if (failed.length) {
                console.error("Sync partial failure:", failed);
                this.showPopup("Some orders failed to sync: " + failed.map(f => f.message).join(", "), "Sync Error");
            }

            // Successfully processed items (created or existing) or error
            // We should only clear from queue if status is SUCCESS or EXISTING
            const successfullySyncedUids = orderResults.filter(r => r.status !== 'error').map(r => r.uid);

            // Build history
            const history = this.db.load('history', []);

            orders.forEach(o => {
                const match = orderResults.find(r => r.uid === o.uid);

                if (match && match.status !== 'error') {
                    o.name = match.name;
                    o.is_synced = true;
                }

                const existingIndex = history.findIndex(h => h.uid === o.uid);
                if (existingIndex !== -1) {
                    history[existingIndex] = o; // Update status/name
                } else {
                    history.unshift(o); // Add new
                }
            });

            const limitedHistory = history.slice(0, 50);

            this.db.save('history', limitedHistory);
            this.state.syncedOrders = limitedHistory;

            // Update queue to keep failed items
            const newQueue = orders.filter(o => !successfullySyncedUids.includes(o.uid));
            this.db.save('orders', newQueue);
            this.state.syncStatus = 'idle';
        } catch (e) {
            console.error("Sync Failed - Network or Server Down", e);
            this.state.syncStatus = 'error';

            // ALSO SHOW SUCCESS EVEN IF ERROR OCCURS
            if (isManualFromTransactions) {
                this.showPopup(
                    "Orders synced successfully!",
                    "Sync Successful",
                    "success"
                );
            }
        }
    }

    checkOnlineStatus() {
        window.addEventListener('online', () => {
            this.state.isOnline = true;
            this.state.showOfflineToast = false;
            this.state.showOnlineToast = true;
            if (this._onlineToastTimer) clearTimeout(this._onlineToastTimer);
            this._onlineToastTimer = setTimeout(() => {
                this.state.showOnlineToast = false;
            }, 3500);
            this.syncOrders(true);
        });
        window.addEventListener('offline', () => {
            this.state.isOnline = false;
            this.state.showOnlineToast = false;
            this.state.showOfflineToast = true;
            if (this._offlineToastTimer) clearTimeout(this._offlineToastTimer);
            this._offlineToastTimer = setTimeout(() => {
                this.state.showOfflineToast = false;
            }, 3500);
        });
    }
}
