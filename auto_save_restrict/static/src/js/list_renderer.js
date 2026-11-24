import { ListRenderer } from "@web/views/list/list_renderer";
import { patch } from "@web/core/utils/patch";

patch(ListRenderer.prototype, {
    /** Patch ListRenderer to prevent auto-saving rows when clicking outside. */
    onGlobalClick(ev) {
        if (!(this.editedRecord() || this.state.showGroupInput)) {
            return;
        }

        const table = this.tableRef();
        if (table) {
            table.querySelector("tbody")?.classList.remove("o_keyboard_navigation");
        }

        const target = ev.target;
        if (this.state.showGroupInput && this.groupInputRef() !== target) {
            this.state.showGroupInput = false;
        }

        // Prevent automatic leaveEditMode() (auto-save) on outside click.
        // The record remains in edit mode until the user explicitly clicks Save, Discard, or navigates away.
    },
});
