/** @odoo-module **/
import { formView } from '@web/views/form/form_view';
import { registry } from "@web/core/registry";
import { FormRenderer } from "@web/views/form/form_renderer";
import { FormController } from "@web/views/form/form_controller";
import { useEffect, useExternalListener } from "@odoo/owl";
export class MasterSearch extends FormController {
    setup() {
        super.setup();
        useEffect(() => {
            const expandElements = document.querySelectorAll('.expand_tile')
            const background = document.querySelector('.oe_search_bgnd')
            const RadioBtns = document.querySelectorAll('.o_radio_input')
            if (background.length > 0) {
                document.title = 'Search';
            }
            expandElements.forEach((element) => {
                element.addEventListener("click", this.clickedExpandTile)
            })
            RadioBtns.forEach((element) => {
                element.addEventListener("change", this.onChangeRadioBtn)
            })
            return () => {
                expandElements.forEach((element) => {
                    element.removeEventListener("click", this.clickedExpandTile)
                })
                RadioBtns.forEach((element) => {
                    element.removeEventListener("change", this.onChangeRadioBtn)
                })
            }
        })
    }
    clickedExpandTile(e) {
        var resultDiv = this.closest('.oe_result_div')
        var element = resultDiv.querySelector('.oe_details_list')
        if (element.style.display === "none" || element.style.display === "") {
            element.style.display = "block";
        } else {
            element.style.display = "none";
        }
    }
    onChangeRadioBtn(e) {
        let targetEl = this.dataset.value;
        const treeEls = document.querySelectorAll('.oe_details_list')
        treeEls.forEach((element) => {
            if (element.style.display === "none" || element.style.display === "") {
                element.classList.remove('oe_details_list--show');
            } else {
                element.classList.add('d-none');
            }
        });
        const searchTabs = document.querySelectorAll('.oe_search_tab')
        switch(targetEl){
            case 'customer':
            searchTabs.forEach((el) => {
                el.classList.add('d-none');
            })
            const customerResult = document.querySelector('#customer_search_results')
            customerResult.classList.add('d-block');
            customerResult.classList.remove('d-none');
            break;
            case 'product':
            searchTabs.forEach((el) => {
                el.classList.add('d-none');
            })
            const productResult = document.querySelector('#product_search_results')
            productResult.classList.add('d-block');
            productResult.classList.remove('d-none');
            break;
            case 'transaction details':
            searchTabs.forEach((el) => {
                el.classList.add('d-none');
            })
            const TransactionResult = document.querySelector('#inventory_search_results')
            TransactionResult.classList.add('d-block');
            TransactionResult.classList.remove('d-none');
            break;
            case 'sale details':
            searchTabs.forEach((el) => {
                el.classList.add('d-none');
            })
            const SaleResult = document.querySelector('#sale_search_results')
            SaleResult.classList.add('d-block');
            SaleResult.classList.remove('d-none');
            break;
            case 'purchase details':
            searchTabs.forEach((el) => {
                el.classList.add('d-none');
            })
            const PurchaseResult = document.querySelector('#purchase_search_results')
            PurchaseResult.classList.add('d-block');
            PurchaseResult.classList.remove('d-none');
            break;
            case 'account details':
            searchTabs.forEach((el) => {
                el.classList.add('d-none');
            })
            const AccountResult = document.querySelector('#accounting_search_results')
            AccountResult.classList.add('d-block');
            AccountResult.classList.remove('d-none');
            break;
            case 'any':
            searchTabs.forEach((el) => {
                el.classList.remove('d-none');
            })
            break;
        }
        const RecentSearch = document.querySelector('#recent_searches')
        RecentSearch.classList.add('d-block');
        RecentSearch.classList.remove('d-none');
    }
}
export const MasterSearchClass = {
   ...formView,
   Controller: MasterSearch,
};
registry.category("views").add("master_search", MasterSearchClass);
