/** @odoo-module **/
import { registry } from '@web/core/registry';
import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";
import { proxy, onMounted, onWillUnmount } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
export class AccountMoveLineListController extends ListController {
     constructor() {
        super(...arguments);
        this.resIdList = [];
     }
     setup(){
         super.setup();
         this.state = proxy({ selectedRecordId: null ,
                                 selectedRecordIds: [],});
         this.action = useService("action")
         this.orm = useService("orm")
     }
     async openRecord(record) {
        const kanban_row = document.querySelector(`tr[data-id]`);
        const data_id = parseInt(kanban_row.getAttribute('data-id'))
        var data = await this.orm.call('account.bank.statement.line',
            'update_match_row_data',
            [record.resId])
        await this.orm.call('account.bank.statement.line', 'write', [[data_id], { lines_widget_json: JSON.stringify(data) }]);
        const rowSelector = document.querySelector(`tr[data-id='${record.id}']`)
         if (!record.clickCount) {
            record.clickCount = true
            rowSelector.style.backgroundColor = "#d1ecf1";
         } else {
            // Set the default background color here
            record.clickCount = false;
            rowSelector.style.backgroundColor = "white";
         }
        const currencySymbol = await this.orm.call('res.currency', 'read', [[record.data.currency_id.id]])
        const mainKanbanDiv = document.querySelector('#base_accounting_reconcile')
        const existingRow = document.querySelector(`tr[data-resId="${record.resId}"]`)
        const stateLineRow = document.querySelector('.statement_row')
        if (stateLineRow){
            const dataIdValue = stateLineRow.getAttribute('data-id');
            if(dataIdValue == record.resId){
                mainKanbanDiv.removeChild(stateLineRow);
            }
        }
        if (existingRow) {
            mainKanbanDiv.removeChild(existingRow);
        } else {
            // If the row doesn't exist, create and add it
            const dateObject = new Date(record.data.date);
            const year = dateObject.getFullYear();
            const month = String(dateObject.getMonth() + 1).padStart(2, '0'); // Months are 0-indexed
            const day = String(dateObject.getDate()).padStart(2, '0');
            const formattedDate = `${year}-${month}-${day}`;
            let amount = parseFloat(record.data.amount_residual);
            let debitColumn = '';
            let creditColumn = '';
            let partnerName = '';
            let moveId = '';

            // Check if partner_id exists and is not empty
            if (record.data.partner_id && record.data.partner_id.display_name) {
                partnerName = record.data.partner_id.display_name;
            }
            if (record.data.move_id && record.data.move_id.display_name) {
                moveId = `<br/><span id="moveLine" style="font-size: 12px; font-style: italic;font-weight: normal;color: #01666b;cursor: pointer;" data-moveId="${record.data.move_id.id}">${record.data.move_id.display_name}</span>`;
            }


            if (amount < 0) {
                debitColumn = `<td style="font-weight: bold; display: table-cell; max-width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; vertical-align: top;">${currencySymbol[0].symbol} ${-amount}</td>`;
            } else {
                creditColumn = `<td style="font-weight: bold; display: table-cell; max-width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; vertical-align: top;">${currencySymbol[0].symbol} ${amount}</td>`;
            }

            const newRow = document.createElement('tr');
            newRow.setAttribute('data-resId', record.resId); // Set a unique identifier for the row
            if (debitColumn !== '') {
                newRow.innerHTML = `<td style="font-weight: bold; display: table-cell; max-width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; vertical-align: top;">${record.data.account_id.display_name}
                                    ${moveId}<span style="font-size: 12px;font-style: italic;font-weight: normal;"> : ${record.data.name}</span></td>
                                    <td style="font-weight: bold; display: table-cell; max-width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; vertical-align: top;">${partnerName}</td>
                                    <td style="font-weight: bold; display: table-cell; max-width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; vertical-align: top;">${formattedDate}</td>
                                    ${debitColumn}
                                    <td style="font-weight: bold; display: table-cell; max-width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; vertical-align: top;"> </td>
                                    <td class="o_list_remove_record">
                                    <button class="btn oi oi-filled text-danger fa-trash-o" data-icon="delete" data-resId="${record.resId}"/>
                                    </td>`;

            } else if (creditColumn !== '') {
                newRow.innerHTML = `<td style="font-weight: bold; display: table-cell; max-width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; vertical-align: top;">${record.data.account_id.display_name}
                                    ${moveId}<span style="font-size: 12px;font-style: italic;font-weight: normal;"> : ${record.data.name}</span></td>
                                    <td style="font-weight: bold; display: table-cell; max-width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; vertical-align: top;">${partnerName}</td>
                                    <td style="font-weight: bold; display: table-cell; max-width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; vertical-align: top;">${formattedDate}</td>
                                    <td style="font-weight: bold; display: table-cell; max-width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; vertical-align: top;"> </td>
                                    ${creditColumn}
                                    <td class="o_list_remove_record">
                                    <button class="btn oi oi-filled text-danger fa-trash-o" data-icon="delete" data-resId="${record.resId}"/>
                                    </td>`;
            }
            newRow.addEventListener('click', async () => {
                const allRows = document.querySelectorAll('tr[data-resId]');
                allRows.forEach(row => {
                    row.classList.remove('selected-row');
                });
                 newRow.classList.add('selected-row');
                 if (record.resId){
                    const manualOpsTab = document.querySelector('[name="manual_operations_tab"]');
                    if (manualOpsTab) {
                        manualOpsTab.click();
                        const accountField = document.querySelector('[name="account_id"]');
                        accountField.value = record.data.account_id.display_name;
                    }
                 }
            });
            // Append the new row to the mainKanbanDiv
            mainKanbanDiv.appendChild(newRow);
            const deleteButtons = document.querySelectorAll('.fa-trash-o');
            deleteButtons.forEach(button => {
                button.addEventListener('click', async (event) => {
                    const btn = event.target.closest('[data-resId]') || event.target;
                    const resId = btn.getAttribute('data-resId');
                    await this.removeRecord(resId);
                });
            });
            const moveLine = document.querySelectorAll('#moveLine');
            moveLine.forEach(line => {
                line.addEventListener('click', async (event) => {
                    const moveId = event.target.getAttribute('data-moveId');
                    await this.ShowMoveForm(moveId);
                });
            });
        }
        this.updateResIdList();
        if (data_id) {
            if (this.resIdList.length) {
                var data = await this.orm.call('account.bank.statement.line', 'update_match_row_data', [this.resIdList[0]]);
                data.ids = this.resIdList;
                await this.orm.call('account.bank.statement.line', 'write', [[data_id], { lines_widget_json: JSON.stringify(data) }]);
            } else {
                await this.orm.call('account.bank.statement.line', 'write', [[data_id], { lines_widget_json: null }]);
            }
        }
    }
    async removeRecord(resId) {
        const mainKanbanDiv = document.querySelector('#base_accounting_reconcile');
        const rowToRemove = document.querySelector(`tr[data-resId="${resId}"]`);
        if (rowToRemove) {
            mainKanbanDiv.removeChild(rowToRemove);
            this.updateResIdList();
            const kanban_row = document.querySelector(`tr[data-id]`);
            if (kanban_row) {
                const data_id = parseInt(kanban_row.getAttribute('data-id'));
                if (this.resIdList.length) {
                    var data = await this.orm.call('account.bank.statement.line', 'update_match_row_data', [this.resIdList[0]]);
                    data.ids = this.resIdList;
                    await this.orm.call('account.bank.statement.line', 'write', [[data_id], { lines_widget_json: JSON.stringify(data) }]);
                } else {
                    await this.orm.call('account.bank.statement.line', 'write', [[data_id], { lines_widget_json: null }]);
                }
            }
        }
    }
    async ShowMoveForm(moveId) {
        // Convert moveId from string to integer
        const moveIdInt = parseInt(moveId, 10);
        // Check if the conversion is successful
        if (!isNaN(moveIdInt)) {
            this.action.doAction({
                type: 'ir.actions.act_window',
                res_model: 'account.move',
                res_id: moveIdInt,
                views: [[false, "form"]],
                target: 'current',
            });
        }
    }
    updateResIdList() {
        // Get all resId values from the current rows and update the resIdList array
        const rows = document.querySelectorAll('tr[data-resId]');
        this.resIdList = Array.from(rows).map(row => parseInt(row.getAttribute('data-resId'), 10));
    }

}
AccountMoveLineListController.template = 'base_accounting_kit.AccountMoveLineListController';
export const AccountMoveListView = {
    ...listView,
    Controller: AccountMoveLineListController,
};
registry.category('views').add('account_move_line_list_controller', AccountMoveListView);

export class AmlSelectListController extends ListController {
    setup() {
        super.setup();
        this.actionService = useService("action");
        this.orm = useService("orm");
        this.notification = useService("notification");
        let btnSelect = null;

        onMounted(() => {
            const activeStLineId = this.props.context && this.props.context.active_st_line_id;
            if (activeStLineId) {
                const modalDialog = document.querySelector('.modal-content') || document.querySelector('.o_dialog');
                if (modalDialog) {
                    let modalFooter = modalDialog.querySelector('.modal-footer');
                    if (!modalFooter) {
                        modalFooter = document.createElement('div');
                        modalFooter.className = 'modal-footer justify-content-start border-top p-2 bg-body';
                        modalDialog.appendChild(modalFooter);
                    }
                    if (!modalFooter.querySelector('.btn_aml_select')) {
                        btnSelect = document.createElement('button');
                        btnSelect.className = 'btn btn-primary px-3 btn_aml_select';
                        btnSelect.style.backgroundColor = '#714B67';
                        btnSelect.style.borderColor = '#714B67';
                        btnSelect.style.fontWeight = '500';
                        btnSelect.innerText = _t('Select');
                        btnSelect.onclick = (e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            this.onClickSelectSelected();
                        };
                        modalFooter.prepend(btnSelect);
                    }
                }
            }
        });

        onWillUnmount(() => {
            if (btnSelect && btnSelect.parentNode) {
                btnSelect.remove();
            }
        });
    }

    async onClickSelectSelected() {
        const activeStLineId = this.props.context.active_st_line_id;
        const selectedRecords = this.model.root.selection || [];
        const amlIds = selectedRecords.map(r => r.resId).filter(Boolean);
        if (!amlIds.length) {
            this.notification.add(_t("Please select at least one line to reconcile."), { type: 'warning' });
            return;
        }
        if (activeStLineId && amlIds.length > 0) {
            await this.orm.call('account.bank.statement.line', 'action_select_aml_to_reconcile', [activeStLineId, amlIds]);
            this.actionService.doAction({ type: 'ir.actions.client', tag: 'reload' });
        }
    }

    async openRecord(record) {
        if (record && record.toggleSelection) {
            record.toggleSelection();
        }
    }
}
export const AmlSelectListView = {
    ...listView,
    Controller: AmlSelectListController,
};
registry.category('views').add('aml_rec_select_list', AmlSelectListView);

export class PartnerSelectListController extends ListController {
    setup() {
        super.setup();
        this.actionService = useService("action");
        this.orm = useService("orm");
    }
    async openRecord(record) {
        const activeStLineId = this.props.context && this.props.context.active_st_line_id;
        if (activeStLineId && record.resId) {
            await this.orm.call('account.bank.statement.line', 'action_set_partner', [activeStLineId, record.resId]);
            this.actionService.doAction({ type: 'ir.actions.client', tag: 'reload' });
            return;
        }
        super.openRecord(...arguments);
    }
}
export const PartnerSelectListView = {
    ...listView,
    Controller: PartnerSelectListController,
};
registry.category('views').add('partner_rec_select_list', PartnerSelectListView);

export class AccountSelectListController extends ListController {
    setup() {
        super.setup();
        this.actionService = useService("action");
        this.orm = useService("orm");
    }
    async openRecord(record) {
        const activeStLineId = this.props.context && this.props.context.active_st_line_id;
        if (activeStLineId && record.resId) {
            await this.orm.call('account.bank.statement.line', 'action_set_account', [activeStLineId, record.resId]);
            this.actionService.doAction({ type: 'ir.actions.client', tag: 'reload' });
            return;
        }
        super.openRecord(...arguments);
    }
}
export const AccountSelectListView = {
    ...listView,
    Controller: AccountSelectListController,
};
registry.category('views').add('account_rec_select_list', AccountSelectListView);