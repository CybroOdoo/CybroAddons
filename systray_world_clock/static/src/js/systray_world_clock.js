/** @odoo-module **/
import core from 'web.core';
import SystrayMenu from 'web.SystrayMenu';
import Widget from 'web.Widget';
var QWeb = core.qweb;
var ClockWidget = Widget.extend({
    template: 'Systray_clock',
    events: {
        'show.bs.dropdown': 'onClickWorldClock',
        'hide.bs.dropdown': 'stopTimer',
        'click .settings': 'onClickSettings'
    },
    /**
     * Fetch data from the server to display the world clocks. Uses the RPC
     * method to search and read data from the 'systray.world.clock.config'
     * model with an empty domain and retrieves the 'name', 'tz', and
     * 'offset' fields. The function then assigns the retrieved clock
     * configurations to the ClockWidget instance's 'ClockConfigIds' property.
     *
     * @returns {Promise} A promise that resolves with the clock
     * configurations retrieved from the server.
     */
    willStart: function () {
        var self = this;
        return self._rpc({
            model: 'systray.world.clock.config',
            method: 'search_read',
            domain: [],
            fields: ['name', 'tz', 'offset']
        }).then(function (ClockConfigs) {
            self.ClockConfigIds = ClockConfigs;
        });
    },
    /**
     * This function is called when the icon is clicked on the systray menu.
     * Selects the clock container from the DOM, and then renders the clock
     * interface and starts the interval timer to keep the clock updated.
     */
    onClickWorldClock: function (ev) {
        ev.stopPropagation();
        this.clocksContainer = this.el.querySelector('#clocks_container');
        this.renderClock();
        this.intrvl = setInterval(() => {
            this.renderClock();
        }, 1000);
    },
    // Calculating time based on the offset
    calcTime: function (offset) {
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
    },
    // Rendering the clock interface
    renderClock: function () {
        var interfaceTemplate;
        // checks if no clocks are displayed.
        if (!this.el.querySelector('.time-info')) {
            if (this.ClockConfigIds.length > 0) {
                this.clocksContainer.innerHTML = '';
            }
            this.clockRendered = false;
        }
        //calculates the time for each clock and updates the
        // corresponding analogue clock display and digital time information.
        for (let clock of this.ClockConfigIds) {
            let offsetStr = clock.offset.toString().replace('.', '_');
            let currentClockClass = 'clock' + offsetStr;

            if (!this.clockRendered) {
                interfaceTemplate = QWeb.render("AnalogueInterface", {
                    currentClockClass: currentClockClass,
                    country: clock.name
                });
            }
            if (interfaceTemplate) {
                this.clocksContainer.innerHTML += interfaceTemplate;
            }
            /**
             * Updates the analogue time of a clock based on its time zone
             * offset and renders it on the webpage.
             *
             * Behavior:
             *
             * *Uses calcTime function to calculate the current time of the
             * clock based on its time zone offset.
             *
             * *Calculates the angle for each of the clock hands (hour,
             * minute, and second) based on the current time.
             *
             * *Rotates each clock hand to the calculated
             * angle using CSS transform: rotate() property.
             *
             * *Updates the digital time of the clock in the webpage by
             * setting the HTML of #digital-info element with localestring.
             *
             * *Checks the current time and adds/removes night-clock class
             * to the clock container based on whether it is daytime or
             * nighttime.
             */
            this.updateAnalogueTime = function () {
                const [nd, localestring] = this.calcTime(clock.offset);
                var hoursArr = this.el.querySelectorAll('.' + currentClockClass + ' .hours');
                var minutesArr = this.el.querySelectorAll('.' + currentClockClass + ' .minutes');
                var secondsArr = this.el.querySelectorAll('.' + currentClockClass + ' .seconds');
                let h = (nd.getHours() % 12) + nd.getMinutes() / 59;
                let m = nd.getMinutes();
                let s = nd.getSeconds();
                h *= 30;
                m *= 6;
                s *= 6;
                /**
                 * This function takes in a target element and a value, and
                 * sets the rotation style of the target element to the
                 * given value.
                 * @param target
                 * @param val
                 */
                const rotation = (target, val) => {
                    target.style.transform = `rotate(${val}deg)`;
                };
                hoursArr.forEach(hours => rotation(hours, h));
                minutesArr.forEach(minutes => rotation(minutes, m));
                secondsArr.forEach(seconds => rotation(seconds, s));
                $('#clocks_container .' + currentClockClass + '#digital-info').html(localestring);
                if (18 <= nd.getHours() || nd.getHours() < 6) {
                    $('#clocks_container .clock.' + currentClockClass).addClass('night-clock');
                }
                else {
                    $('#clocks_container .' + currentClockClass).removeClass('night-clock');
                }
            };
            // to update time in the clocks_container
            this.updateTime = function () {
                this.updateAnalogueTime();
            };
            this.updateTime();
        }
        this.clockRendered = true;
    },
    /**
     * Stops the interval timer that updates the clocks when the dropdown is
     * hidden. It clears the interval timer using the clearInterval method.
     */
    stopTimer: function () {
        clearInterval(this.intrvl);
    },
    // opens settings
    onClickSettings: function (ev) {
        ev.stopPropagation();
        this.do_action({
            type: 'ir.actions.act_window',
            name: 'Clock Settings',
            res_model: 'systray.world.clock.config',
            view_mode: 'list, form',
            views: [[false, 'list'], [false, 'form']]
        });
    }
});
SystrayMenu.Items.push(ClockWidget);
