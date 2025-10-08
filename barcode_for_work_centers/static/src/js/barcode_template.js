/** @odoo-module */
import { registry } from '@web/core/registry';
import { onWillStart, Component } from "@odoo/owl";
const actionRegistry = registry.category("actions");
import { useService } from "@web/core/utils/hooks";
import { useAutofocus } from "@web/core/utils/hooks";
const { useRef } = owl;
import rpc from "web.rpc";
var hours = 0;
var minutes = 0;
var seconds = 0;
var isPaused = true;

/**
 * Represents a barcode scanning view component.
 */
class BarcodeScanningView extends Component {
    /**
     * Initializes the necessary services and references for the application.
     * - Sets up action and notification services.
     * - Sets up an input reference with autofocus.
     * - Initializes references for manual order, pause, continue buttons, and a timer.
     *
     **/
    setup() {
        this.action = useService("action");
        this.notification = useService("notification");
        this.inputRef = useAutofocus();
        this.man_order =useRef('autofocus')
        this.pause_ref = useRef('pause-ref');
        this.continue_ref = useRef('continue-ref')
        this.buttons_ref = useRef('buttons-ref');
        this.timer = useRef('timer');
        super.setup(...arguments);
        onWillStart(async () => {
        });
        }

    /**
     * Executes the scanning process.
     */
    ScanNow() {
        var self = this;
        var man_order = this.man_order.el.value;
        if (!man_order) {
            self.notification.add(self.env._t("Scan the barcode on input field"), {
                type: "success",
            });
        } else {
            this.clicked_record = this.props.action.params.id;
            var clicked_record = this.props.action.params.id;
            rpc.query({
                model: 'mrp.workorder',
                method: 'action_work_order_start_stop',
                args: [, clicked_record, man_order],
            }).then(function (result) {
                var state = result;
                if (state["pop_up"] == "start") {
                    self.buttons_ref.el.classList.remove('d-none');
                    self.continue_ref.el.classList.add('d-none')
                    self.notification.add(self.env._t("Work order started"), {
                        type: "success",
                    });
                    self.TimerStart();
                } else if (state["pop_up"] == "end") {
                    self.notification.add(self.env._t("Work order finished"), {
                        type: "success",
                    });
                    self.buttons_ref.el.classList.add('d-none')
                    self.PauseTimer();
                } else if (state["pop_up"] == "already done") {
                    self.notification.add(self.env._t("It is already in a done state"), {
                        type: "success",
                    });
                    self.continue_ref.el.classList.add('d-none')
                } else if (state["pop_up"] == "not match") {
                    self.pause_ref.el.classList.add('d-none')
                    self.notification.add(self.env._t("No matching manufacturing order for this barcode"), {
                        type: "danger",
                    });
                }
            });
        }
    }
    /**
     * Pauses the work order.
     */
    pauseWorkOrder() {
        var self = this;
        var man_order = this.man_order.el.value;
        var clicked_record = this.clicked_record;
        rpc.query({
            model: 'mrp.workorder',
            method: 'action_pause',
            args: [, clicked_record, man_order],
        }).then(function (result) {
            if (result == "paused") {
                self.continue_ref.el.classList.remove('d-none');
                self.pause_ref.el.classList.add('d-none')
                self.notification.add(self.env._t("All work orders are paused"), {
                    type: "danger",
                });
                self.PauseTimer();
            }
        });
    }

    /**
     * Continues the work order.
     */
    ContinueWorkOrder() {
        var self = this;
        var man_order = this.man_order.el.value;
        var clicked_record = this.clicked_record;
        rpc.query({
            model: 'mrp.workorder',
            method: 'action_continue',
            args: [, clicked_record, man_order],
        }).then(function (result) {
            if (result == "continue") {
                self.pause_ref.el.classList.remove('d-none');
                self.continue_ref.el.classList.add('d-none')
                self.notification.add(self.env._t("Work order continued"), {
                    type: "success",
                });
                self.TimerStart();
            }
        });
    }

    /**
     * Marks the work order as done.
     */
    doneWorkOrder() {
        var self = this
        var man_order = this.man_order.el.value
        var clicked_record = this.clicked_record
        rpc.query({
            model: 'mrp.workorder',
            method: 'action_done',
            args: [, clicked_record, man_order],
        }).then(function(result) {
            if (result == "done") {
                self.buttons_ref.el.classList.add('d-none')
                self.notification.add(self.env._t("Work order completed"), {
                    type: "success",
                });
                self.PauseTimer();
                self.ResetTimer();
            }
        });
    }

    /**
     * Starts the timer.
     */
    TimerStart() {
        if (isPaused) {
            isPaused = false;
            this.timer.el.classList.remove('d-none');
            this.setInterval = setInterval(displayTimer, 1000);
        }
    }

    /**
     * Pauses the timer.
     */
    PauseTimer() {
        isPaused = true;
        clearInterval(this.setInterval);
    }

    /**
     * Resets the timer.
     */
    ResetTimer() {
        clearInterval(this.setInterval);
        seconds = 0;
        minutes = 0;
        hours = 0;
        this.timer.el.classList.add('d-none')
    }
    static template = "barcode_scanning_view";
}

/**
 * Displays the timer.
 */
function displayTimer() {
    this.$('.timer-display').empty();
    seconds = seconds + 1;
    if (seconds == 60) {
        minutes = minutes + 1;
        seconds = 0;
    }
    if (minutes == 60) {
        hours = hours + 1;
        minutes = 0;
    }
    if (seconds < 10) {
        var s = "0" + seconds;
    }
    if (seconds >= 10) {
        var s = seconds;
    }
    if (minutes < 10) {
        var m = "0" + minutes;
    }
    if (minutes >= 10) {
        var m = minutes;
    }
    if (hours < 10) {
        var h = "0" + hours;
    }
    if (hours >= 10) {
        var h = hours;
    }
    this.$('.timer-display').append(h + ':' + m + ':' + s);
}

/**
 * Template for the barcode scanning view.
 */
BarcodeScanningView.template = "barcode_scanning_view";

// Add the barcode scanning view to the action registry
actionRegistry.add('barcode_for_work_centers_scanning_template', BarcodeScanningView);
