/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import {PharmaDashboard} from "@pharmaceutical_base/components/dashboard/dashboard";

/**
 * Four equipment figures on the pharma overview: GMP-critical equipment,
 * items under maintenance, calibrations due and open preventive tasks.
 * Equipment figures are current positions, not period counts, so the date
 * filter of the dashboard does not apply to them.
 */
patch(PharmaDashboard.prototype, {
    setup() {
        super.setup(...arguments);
        Object.assign(this.state, {
            equipmentAvailable: true,
            eqGmpCritical: 0,
            eqUnderMaintenance: 0,
            eqCalibrationDue: 0,
            eqPreventiveOpen: 0,
        });
    },

    async fetchData() {
        await Promise.all([super.fetchData(...arguments), this.fetchEquipmentData()]);
    },

    async fetchEquipmentData() {
        try {
            const [gmp, underMaintenance, calibrationDue, preventiveOpen] = await Promise.all([
                this.orm.searchCount("maintenance.equipment", this.eqDomain("gmp")),
                this.orm.searchCount("maintenance.equipment", this.eqDomain("maintenance")),
                this.orm.searchCount("maintenance.equipment", this.eqDomain("calibration")),
                this.orm.searchCount("maintenance.request", this.eqDomain("preventive")),
            ]);
            Object.assign(this.state, {
                eqGmpCritical: gmp,
                eqUnderMaintenance: underMaintenance,
                eqCalibrationDue: calibrationDue,
                eqPreventiveOpen: preventiveOpen,
            });
        } catch {
            this.state.equipmentAvailable = false;
        }
    },

    eqDomain(kind) {
        switch (kind) {
            case "gmp":
                return [["gmp_critical", "=", true]];
            case "maintenance":
                return [["gmp_critical", "=", true], ["maintenance_open_count", ">", 0]];
            case "calibration":
                return [["calibration_state", "in", ["due_soon", "overdue"]]];
            case "preventive":
                return [["maintenance_type", "=", "preventive"],
                    ["pharma_state", "!=", "qa_verified"], ["archive", "=", false]];
        }
        return [];
    },

    openEquipmentTile(kind) {
        const isRequest = kind === "preventive";
        const names = {
            gmp: "GMP-Critical Equipment",
            maintenance: "Equipment Under Maintenance",
            calibration: "Calibration Due",
            preventive: "Open Preventive Maintenance",
        };
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: names[kind],
            res_model: isRequest ? "maintenance.request" : "maintenance.equipment",
            domain: this.eqDomain(kind),
            views: [[false, "list"], [false, "form"]],
        });
    },
});
