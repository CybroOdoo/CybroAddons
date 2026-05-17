/**@odoo-module **/
import { Interaction } from '@web/public/interaction';
import { rpc } from "@web/core/network/rpc";
import { registry } from '@web/core/registry';

export class PropertyView extends Interaction {
    static selector = 'div[id="property_container"]';
    dynamicContent = {
               '.property_action_buttons': { 't-on-click': this._changeView },
               '.o_property_item': { 't-on-click': this.fetchPropertyItem },
               '.auction_submit': { 't-on-click': this._submitAuction },
         };

         async _changeView(ev) {
            const action_id = ev.currentTarget.dataset.action;
            const viewMap = {
                "0": "#property_item_view",
                "2": "#property_sales_view",
                "3": "#property_rental_view",
                "1": "#property_auction_view",
            };

            this.el.querySelectorAll('.property_action_buttons')
                .forEach(btn => btn.classList.remove('active'));

            Object.values(viewMap).forEach((selector) => {
                const el = this.el.querySelector(selector);
                if (el) {
                    el.classList.add("d-none");
                    el.style.display = "none";
                }
            });

            ev.currentTarget.classList.add('active');
            const selectedView = this.el.querySelector(viewMap[action_id]);
            if (selectedView) {
                selectedView.classList.remove("d-none");
                selectedView.style.display = "";
            }

            if (action_id === "1") {
                const auction_data = await rpc("/property/auction/");
                const container = this.el.querySelector('.auction_cards');
                if (container) container.innerHTML = auction_data;
            }
        }

         fetchPropertyItem(ev) {
            const record_id = ev.currentTarget.dataset.property_id;
            window.location = `/property/${record_id}`;
        }


         async _submitAuction(ev) {
            const property_id = ev.currentTarget.dataset.id;

            const bidInput = this.el.querySelector(`#property-${property_id}`);
            const lastBidEl = this.el.querySelector(`#last-bid-${property_id}`);
            const bidStartEl = this.el.querySelector(`#bid-start-${property_id}`);
            const toast = this.el.querySelector('.toast');

            const bid_amount = parseFloat(bidInput?.value);
            let last_bid = parseFloat(lastBidEl?.textContent);
            const bid_start = parseFloat(bidStartEl?.textContent);

            if (last_bid === 0) {
                last_bid = 1;
            }

            if (bid_amount && last_bid && bid_start) {
                if (bid_amount <= last_bid || bid_amount <= bid_start) {
                    toast.classList.add('show');
                } else {
                    const auction_data = await rpc(`/property/auction/${property_id}/bid`, {
                        bid_amount: bid_amount
                    });
                    if (auction_data) {
                        const auctionBtn = this.el.querySelector('#auction_button');
                        auctionBtn?.click();
                    }
                }
            } else {
                toast.classList.add('show');
            }
         }

};
registry
    .category('public.interactions')
    .add('advanced_property_management.property_view', PropertyView);
