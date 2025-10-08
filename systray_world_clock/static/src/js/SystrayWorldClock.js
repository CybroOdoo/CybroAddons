/** @odoo-module **/

import { Component, useState, onMounted} from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { registry } from "@web/core/registry";

export class Analogue extends Component {
    static template = "systray_world_clock.AnalogueInterface";
    async setup() {
        super.setup(...arguments);
        onMounted(() => {
            this.renderClock();
            this.intrvl = setInterval(() => {
                this.renderClock();
            }, 1000);
        });
    }

    calcTime(offset) {
        // Calculating time based on the offset
        const d = new Date(),
        utc = d.getTime() + (d.getTimezoneOffset() * 60000);
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

    renderClock(){
        //Update the analogue clock time
        let [nd, localestring] = this.calcTime(this.props.offset);
        let currentClockClass = this.props.currentClockClass;
        let h = (nd.getHours() % 12) + nd.getMinutes() / 59;
        let m = nd.getMinutes();
        let s = nd.getSeconds();
        h *= 30;
        m *= 6;
        s *= 6;
        const $hoursArr = document.querySelector('.' + currentClockClass + ' .hours');
        const $minutesArr = document.querySelector('.' + currentClockClass + ' .minutes');
        const $secondsArr = document.querySelector('.' + currentClockClass + ' .seconds');
        if($hoursArr){
            $hoursArr.style.transform = `rotate(${h}deg)`
            $minutesArr.style.transform = `rotate(${m}deg)`
            $secondsArr.style.transform = `rotate(${s}deg)`
        }
        if (18 <= nd.getHours() || nd.getHours() < 6) {
            $('#clocks_container .clock.' + currentClockClass).addClass('night-clock');
        }
        else {
            $('#clocks_container .' + currentClockClass).removeClass('night-clock');
        }
    }
}

export class WorldClock extends Component {
    static components = { Dropdown, Analogue }
    static template = "systray_world_clock.Systray_clock";
    async setup() {
        // Initialize and fetch the data from the time zone
        super.setup(...arguments);
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            isOpen: false,
            notes: [],

           })
        const fields = ['name', 'tz', 'offset'];
        const domain = [];
        const result = await this.orm.call("systray.world.clock.config", "search_read", [], {
            fields: ["name", "tz", "offset"],
            domain: [],
        });
        this.ClockConfigIds = result;
        if (result.length != 0){
            this.state.isOpen = true
        }
        const data = []
        for (let clock of result) {
            let offsetStr = clock.offset.toString().replace('.', '_');
            let currentClockClass = 'clock' + offsetStr;
            this.offset = clock.offset
            let [nd, localestring] = this.calcTime(clock.offset);
            data.push({
                'id': clock.id,
                'name': clock.name,
                'offset': clock.offset,
                'tz': clock.tz,
                'currentClockClass': currentClockClass + clock.id,
                'nd': nd,
                'localestring': localestring
            });
        }
        this.state.notes = data;
    }
    // Calculating time based on the offset
    calcTime(offset) {
        const d = new Date(),
            utc = d.getTime() + (d.getTimezoneOffset() * 60000);
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
    //Settings view for adding the different timezone
    onClickSettings(ev) {
        ev.stopPropagation();
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Clock Settings',
            res_model: 'systray.world.clock.config',
            view_mode: 'list, form',
            views: [[false, 'list'], [false, 'form']]
        });
    }
}

export const systrayItem = {
    Component: WorldClock,
};
registry.category("systray").add("WorldClock", systrayItem, { sequence: 0 });
