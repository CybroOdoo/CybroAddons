import { OrderDisplay } from "@point_of_sale/app/components/order_display/order_display";
import { patch } from "@web/core/utils/patch";
import { proxy } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";

// Patch OrderDisplay to add search across current order lines
patch(OrderDisplay.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
        // Dedicated reactive state to avoid overriding OrderDisplay's own state
        this.searchState = proxy({
            search: "",
            lines: [],
            noProductsAvailable: false,
        });
    },

    /**
     * Filter current order lines by product name, default code, or barcode.
     */
    _onKeyupSearch(event) {
        const rawSearch = (event?.target?.value || "").toLowerCase().trim();
        const searchNormalized = rawSearch.replace(/\s+/g, "");
        this.searchState.search = event?.target?.value || "";

        if (rawSearch.length > 0) {
            const currentLines = this.order?.getOrderlines?.() || [];
            const matchingLines = currentLines.filter((line) => {
                if (!line) {
                    return false;
                }
                const product = line.product_id;
                const displayName = (
                    line.full_product_name ||
                    product?.display_name ||
                    line.display_name ||
                    ""
                ).toLowerCase();
                const productName = (product?.name || "").toLowerCase();
                const defaultCode = (product?.default_code || "").toLowerCase();
                const barcode = (product?.barcode || "").toLowerCase();

                const normDisplayName = displayName.replace(/\s+/g, "");
                const normProductName = productName.replace(/\s+/g, "");

                return (
                    displayName.includes(rawSearch) ||
                    productName.includes(rawSearch) ||
                    normDisplayName.includes(searchNormalized) ||
                    normProductName.includes(searchNormalized) ||
                    defaultCode.includes(rawSearch) ||
                    barcode.includes(rawSearch)
                );
            });

            this.searchState.lines = matchingLines;
            this.searchState.noProductsAvailable = matchingLines.length === 0;
        } else {
            this.searchState.lines = [];
            this.searchState.noProductsAvailable = false;
        }
    },

    /**
     * Select the matched orderline and clear search.
     */
    _onSelectOrderline(line) {
        if (this.order && line) {
            this.order.selectOrderline(line);
            this._onClickCancelSearch();
        }
    },

    /**
     * Clear search input and results.
     */
    _onClickCancelSearch() {
        this.searchState.search = "";
        this.searchState.lines = [];
        this.searchState.noProductsAvailable = false;
    },
});

OrderDisplay.components = { ...OrderDisplay.components, Dropdown, DropdownItem };
