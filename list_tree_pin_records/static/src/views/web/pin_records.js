import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";
import { onMounted, signal } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

patch(ListRenderer.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.pinnedRecordIds = signal([]);

        onMounted(() => {
            if (this.canPinRecords) {
                this.loadPins();
            }
        });
    },

    get canPinRecords() {
        if (!this.hasSelectors) {
            return false;
        }
        if (this.isX2Many || (this.props.list && (this.props.list.isEmbedded || this.props.list.isGrouped))) {
            return false;
        }
        if (this.env.dialogData) {
            return false;
        }
        if (this.tableRef?.el?.closest(".o_field_x2many_list, .o_select_create_dialog_content")) {
            return false;
        }
        return true;
    },

    isRecordPinned(record) {
        if (!record || !this.pinnedRecordIds) {
            return false;
        }
        const resId = parseInt(record.resId, 10);
        return this.pinnedRecordIds().includes(resId);
    },

    getRowClass(record) {
        const classNames = super.getRowClass(...arguments);
        if (!this.isRecordPinned(record)) {
            return classNames;
        }
        if (Array.isArray(classNames)) {
            return [...classNames, "o_pinned_row"];
        } else if (typeof classNames === "object" && classNames !== null) {
            return { ...classNames, o_pinned_row: true };
        }
        return classNames ? `${classNames} o_pinned_row` : "o_pinned_row";
    },

    getPinnedOrderedRecords(list) {
        if (!this.canPinRecords || !list || !list.records) {
            return list ? list.records : [];
        }
        const pinnedIds = this.pinnedRecordIds ? this.pinnedRecordIds() : [];
        if (!pinnedIds || !pinnedIds.length) {
            return list.records;
        }
        const pinned = [];
        const unpinned = [];
        for (const record of list.records) {
            const resId = parseInt(record.resId, 10);
            if (pinnedIds.includes(resId)) {
                pinned.push(record);
            } else {
                unpinned.push(record);
            }
        }
        return [...pinned, ...unpinned];
    },

    async loadPins() {
        if (!this.canPinRecords || !this.props.list) {
            return;
        }

        const currentModel =
            (this.props.list.model?.env?.searchModel?.resModel) ||
            this.props.list.resModel;

        if (!currentModel) {
            return;
        }

        const result = await this.orm.call("pin.records", "pin_record", [currentModel]);
        if (result && result.length) {
            this.pinnedRecordIds.set(result.map((item) => parseInt(item.id, 10)));
        } else {
            this.pinnedRecordIds.set([]);
        }
    },

    async pin_record_details(ev, record) {
        if (ev?.stopPropagation) {
            ev.stopPropagation();
        }
        if (!record) {
            return;
        }

        const pinColor = "#4AEBC8";
        const resId = parseInt(record.resId, 10);
        const currentPins = this.pinnedRecordIds() || [];

        if (currentPins.includes(resId)) {
            this.pinnedRecordIds.set(currentPins.filter((id) => id !== resId));
        } else {
            this.pinnedRecordIds.set([...currentPins, resId]);
        }

        await this.orm.call("pin.records", "save_pin_record", [
            [resId, record.resModel, pinColor]
        ]);
    },
});
