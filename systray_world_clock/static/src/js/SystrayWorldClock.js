/** @odoo-module **/
import { Component, useState, onMounted,useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { registry } from "@web/core/registry";

export class Analogue extends Component {
    static template = "systray_world_clock.AnalogueInterface";

    setup() {
        super.setup();
         this.hoursHandRef = useRef("hoursHand");
        this.minutesHandRef = useRef("minutesHand");
        this.secondsHandRef = useRef("secondsHand");
        this.clockElementRef = useRef("clockElement");
        onMounted(() => {
            this.renderClock();
            this.interval = setInterval(() => {
                this.renderClock();
            }, 1000);
        });
    }

    calcTime(offset) {
        const d = new Date();
        const utc = d.getTime() + (d.getTimezoneOffset() * 60000);
        const nd = new Date(utc + (3600000 * offset));
        const options = {
            year: 'numeric',
            month: 'numeric',
            day: 'numeric',
            hour: 'numeric',
            minute: 'numeric',
            hour12: true
        };
        return [nd, nd.toLocaleString('en-US', options)];
    }

    renderClock() {
        const [nd, localestring] = this.calcTime(this.props.offset);
        const h = ((nd.getHours() % 12) + nd.getMinutes() / 59) * 30;
        const m = nd.getMinutes() * 6;
        const s = nd.getSeconds() * 6;

        // Accessing the refs safely
        if (this.hoursHandRef.el) this.hoursHandRef.el.style.transform = `rotate(${h}deg)`;
        if (this.minutesHandRef.el) this.minutesHandRef.el.style.transform = `rotate(${m}deg)`;
        if (this.secondsHandRef.el) this.secondsHandRef.el.style.transform = `rotate(${s}deg)`;

        const clockElement = this.clockElementRef.el;
        if (clockElement) {
            if (18 <= nd.getHours() || nd.getHours() < 6) {
                clockElement.classList.add('night-clock');
            } else {
                clockElement.classList.remove('night-clock');
            }
        }
    }

    willUnmount() {
        clearInterval(this.interval);
    }
}

export class WorldClock extends Component {
    static components = { Dropdown, Analogue };
    static template = "systray_world_clock.Systray_clock";

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            isOpen: false,
            notes: [],
        });

        this.loadClocks();
    }

    async loadClocks() {
        const fields = ['name', 'tz', 'offset'];
        const result = await this.orm.call("systray.world.clock.config", "search_read", [], { fields });

        if (result.length > 0) {
            this.state.isOpen = true;
            const data = result.map(clock => {
                const offsetStr = clock.offset.toString().replace('.', '_');
                const currentClockClass = 'clock' + offsetStr + clock.id;
                const [nd, localestring] = this.calcTime(clock.offset);
                return {
                    id: clock.id,
                    name: clock.name,
                    offset: clock.offset,
                    tz: clock.tz,
                    currentClockClass,
                    nd,
                    localestring,
                };
            });
            this.state.notes = data;
        }
    }

    calcTime(offset) {
        const d = new Date();
        const utc = d.getTime() + (d.getTimezoneOffset() * 60000);
        const nd = new Date(utc + (3600000 * offset));
        const options = {
            year: 'numeric',
            month: 'numeric',
            day: 'numeric',
            hour: 'numeric',
            minute: 'numeric',
            hour12: true,
        };
        return [nd, nd.toLocaleString('en-US', options)];
    }

    onClickSettings(ev) {
        ev.stopPropagation();
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Clock Settings',
            res_model: 'systray.world.clock.config',
            view_mode: 'list,form',
            target: 'current',
            views: [[false, 'list'], [false, 'form']],
        });
    }
}

export const systrayItem = {
    Component: WorldClock,
};
registry.category("systray").add("WorldClock", systrayItem, { sequence: 0 });
