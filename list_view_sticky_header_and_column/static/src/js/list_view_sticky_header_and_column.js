/** @odoo-module **/
/** This file will used to stick the selected header and column in  the list view **/
import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";

patch(ListRenderer.prototype, {
    setup() {
        super.setup();
    },
    /**
     * function defining the button having t-on-click _onClick
     */
    _onClickIcon(ev, column) {
    ev.preventDefault();
        ev.stopPropagation();
        const clickedHeader = ev.currentTarget.closest('th');
        const columnIndex = Array.from(clickedHeader.parentNode.children).indexOf(clickedHeader);
        console.log(this.__owl__.bdom.parentEl);
        // Remove 'sticky-column' and 'clicked-header' classes from relevant elements
        const stickyColumns = this.__owl__.bdom.parentEl.querySelectorAll('.sticky-column');
        stickyColumns.forEach(el => el.classList.remove('sticky-column'));
        const clickedHeaders = this.__owl__.bdom.parentEl.querySelectorAll('.clicked-header');
        clickedHeaders.forEach(el => el.classList.remove('clicked-header'));

        // Add 'clicked-header' class to the clicked header
        clickedHeader.classList.add('clicked-header');

        // Select table headers, rows, and footer
        const tableHeaders = this.__owl__.bdom.parentEl.querySelectorAll('.o_list_table th');
        const tableRows = this.__owl__.bdom.parentEl.querySelectorAll('.o_list_table tr');
        const tfootRowCells = this.__owl__.bdom.parentEl.querySelector('.o_list_table tfoot tr')?.children || [];

        // Select footer cells up to columnIndex (inclusive)
        const selectedFooterCells = Array.from(tfootRowCells).slice(0, columnIndex + 1);
        selectedFooterCells.forEach(cell => cell.classList.add('sticky-column'));

        // Select data row cells and header cells up to columnIndex (inclusive)
        const selectedColumns = this.__owl__.bdom.parentEl.querySelectorAll(
            `.o_data_row td:nth-child(-n+${columnIndex + 1})`
        );
        const selectedHeaderCells = Array.from(tableHeaders).slice(0, columnIndex + 1);

        // Remove 'sticky-column' class and 'left' style from all headers and data cells
        tableHeaders.forEach(header => {
            header.classList.remove('sticky-column');
            header.style.left = '';
        });
        this.__owl__.bdom.parentEl.querySelectorAll('.o_data_row td').forEach(cell => {
            cell.classList.remove('sticky-column');
            cell.style.left = '';
        });

        // Add 'sticky-column' class to selected columns and headers
        selectedColumns.forEach(cell => cell.classList.add('sticky-column'));
        selectedHeaderCells.forEach(header => header.classList.add('sticky-column'));

        this.__owl__.bdom.parentEl.querySelectorAll('.sticky-column').forEach(el => {
            if (el.tagName === 'TH') {
                el.style.top = '0';
            }
        });

        // Calculate left position for the target column
        const targetColumn = Array.from(selectedColumns).find(
            (el, idx) => idx % (columnIndex + 1) === columnIndex
        );
        const targetLeftPosition = targetColumn ? targetColumn.getBoundingClientRect().left - this.__owl__.bdom.parentEl.getBoundingClientRect().left : 0;

        // Adjust left position for sticky columns in headers and rows
        const columnsToAdjust = columnIndex + 1;
        tableRows.forEach(row => {
            const headerCells = row.querySelectorAll('th');
            const rowCells = row.querySelectorAll('td');
            for (let i = 0; i < columnsToAdjust; i++) {
                if (headerCells[i]) {
                    const leftPos = headerCells[i].getBoundingClientRect().left - this.__owl__.bdom.parentEl.getBoundingClientRect().left;
                    headerCells[i].style.left = `${leftPos}px`;
                }
                if (rowCells[i]) {
                    const leftPos = rowCells[i].getBoundingClientRect().left - this.__owl__.bdom.parentEl.getBoundingClientRect().left;
                    rowCells[i].style.left = `${leftPos}px`;
                }
            }
        });
    },
    /**
     * super onClickSortColumn function and remove the icon and element having the class sticky-column
     */
    onClickSortColumn(column) {
        super.onClickSortColumn(...arguments);
        const stickyColumns = this.__owl__.bdom.parentEl.querySelectorAll('.sticky-column');
        stickyColumns.forEach(el => el.classList.remove('sticky-column'));
        const clickedHeaders = this.__owl__.bdom.parentEl.querySelectorAll('.clicked-header');
        clickedHeaders.forEach(el => el.classList.remove('clicked-header'));
        const tableHeaders = this.__owl__.bdom.parentEl.querySelectorAll('.o_list_table th');
        tableHeaders.forEach(header => {
            header.classList.remove('sticky-column');
            header.style.left = '';
        });
    },
});
