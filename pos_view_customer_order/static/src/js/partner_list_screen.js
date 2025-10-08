/** @odoo-module **/

const PartnerListScreen = require('point_of_sale.PartnerListScreen');
const Registries = require('point_of_sale.Registries');

/** Extends the PartnerListScreen and added additional function getOrders
    to view particular customers past orders from customers portal **/
const GetOrderPartnerListScreen = (PartnerListScreen) =>
        class extends PartnerListScreen {
            setup(){
                super.setup();
            }
            // Function to get particular partners order from pos
            goToOrders() {
                this.showScreen('TicketScreen');
                this.back(true);
                this.back(true);
                const partner = this.state.editModeProps.partner;
                const partnerHasActiveOrders = this.env.pos
                    .get_order_list()
                    .some((order) => order.partner?.id === partner.id);
                const ui = {
                    searchDetails: {
                        fieldName: "PARTNER",
                        searchTerm: partner.name,
                    },
                    filter: partnerHasActiveOrders ? "" : "SYNCED",
                };
                this.showScreen("TicketScreen", { ui });
            }
        };
Registries.Component.extend(PartnerListScreen, GetOrderPartnerListScreen);
