import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";

/**
 * Tender page: totals of the prices typed by the vendor, and edit request.
 */
export class TenderBiddingForm extends Interaction {
    static selector = ".tender_details_page";
    dynamicContent = {
        ".vendor_bid": { "t-on-change": this.onChangeComputeTotal },
        ".edit-request-btn": { "t-on-click.prevent": this.locked(this.onClickEditRequest, true) },
    };

    async onClickEditRequest() {
        const bidId = this.el.querySelector(".bid_info")?.dataset.bid_id;
        const result = await this.waitFor(rpc("/edit_request", { bid_id: bidId }));
        if (result?.success) {
            window.location.href = "/edit_request_success";
        }
    }

    onChangeComputeTotal(ev) {
        const tbody = ev.target.closest("tbody");
        let grandTotal = 0;
        const productPrices = [...tbody.querySelectorAll(".product_row")].map((row) => {
            const input = row.querySelector(".vendor_bid");
            const qty = parseFloat(row.querySelector(".product_qty").dataset.qty) || 0;
            const price = parseFloat(input.value) || 0;
            const rowTotal = qty * price;
            row.querySelector(".total_price").textContent = rowTotal.toFixed(2);
            grandTotal += rowTotal;
            return [input.getAttribute("product_id"), price];
        });
        const grandTotalEl = tbody.querySelector(".total_row .grand_total");
        if (grandTotalEl) {
            grandTotalEl.textContent = grandTotal.toFixed(2);
        }
        const form = this.el.querySelector(".tender-bid-form");
        let hiddenInput = form.querySelector("input[name='product_bid_list']");
        if (!hiddenInput) {
            hiddenInput = document.createElement("input");
            hiddenInput.type = "hidden";
            hiddenInput.name = "product_bid_list";
            form.appendChild(hiddenInput);
        }
        hiddenInput.value = JSON.stringify(productPrices);
    }
}

registry
    .category("public.interactions")
    .add("advanced_tender_management.tender_bidding_form", TenderBiddingForm);
