/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component , useRef } from "@odoo/owl";

export class QrcodeScanner extends Component{
/*
    Open Qr Code scanner Window
*/
    setup() {
        super.setup();
        this.result = useRef("result");
        this.reader = useRef("reader");
        this.orm = useService("orm");
    }
    load_qr() {
        var self=this
        const scanner = new Html5QrcodeScanner('reader', {
            qrbox: {
                width: 250,
                height: 250,
            },  // Sets dimensions of scanning box (set relative to reader element width)
            fps: 20, // Frames per second to attempt a scan
        });
        scanner.render(success, error);
        // Starts scanner
        async function success(data) {
            const keyValuePairs = data.split(',');
            const result = {};
            for (const pair of keyValuePairs) {
                const [key, value] = pair.split(':');
                const trimmedKey = key.trim();
                if (value){
                    const trimmedValue = value.trim();
                    result[trimmedKey] = trimmedValue;
                }
            }
            if (result.hasOwnProperty('Event')){
                scanner.clear();
                self.reader.el.classList.add('d-none');
                var domain = [['event_ticket_id','=',parseInt(result['Ticket'])],
                ['event_id','=',parseInt(result['code'])], ['state','=','open']];
                var fields = ['name','partner_id'];
                const vals = await self.orm.call('event.registration', 'search_read', [domain,fields])
                if (vals.length === 0) {
                    var successMessage = document.createElement('h2');
                    successMessage.innerHTML = `<h2>Success!</h2>`;
                    self.result.el.appendChild(successMessage);
                    var event = document.createElement('h2');
                    event.innerHTML = `<p>Event : ${result['Event']}</p>`;
                    self.result.el.appendChild(event);
                    var newelement = document.createElement('p');
                    newelement.innerHTML = `<p style="color:red;">No Attendee Found!!</p>`;
                    self.result.el.appendChild(newelement);
                }
                else{
                    var successMesage = document.createElement('h2');
                    successMesage.innerHTML = `<h2>Success!</h2>`;
                    self.result.el.appendChild(successMesage);
                    var event = document.createElement('h2');
                    event.innerHTML = `<p>Event : ${result['Event']}</p>`;
                    self.result.el.appendChild(event);
                    var newelement = document.createElement('div');
                    newelement.innerHTML = `<div><label style="display: inline-flex;" for="select_attendee_id">
                    Select Attendee : <select name="select_attendee_id" id="select_attendee_id" class="attendee_selection"
                    style="">
                    </select></label><br/><br/><button id="mark_as_attending" icon="fa fa-check" class="btn btn-primary" >
                    Mark as Attending</button></div>`;
                    self.result.el.appendChild(newelement);
                    self.result.el.children[2].children[0].children[3].addEventListener('click', function() {
                        for (let i = 0; i < vals.length; i++) {
                            if (self.result.el.children[2].children[0].children[0].children[0].value == vals[i]['name']){
                                self.orm.call('event.registration', 'action_set_done', [parseInt(vals[i]['id'])]).then(function(){
                                  location.reload();
                                });
                            }
                        }
                    })
                    for (let i = 0; i < vals.length; i++) {
                        var options = document.createElement('option');
                        options.innerHTML = `<option id='option' value=${vals[i]['id']}>${vals[i]['name']}</option>`;
                        self.result.el.children[2].children[0].children[0].children[0].appendChild(options);
                    };
                }
            }
            else{
                var invalidMessage = document.createElement('h2');
                invalidMessage.innerHTML = `<h2 style="color:red;">Invalid!</h2>`;
                self.result.el.appendChild(invalidMessage);
                scanner.clear();
                self.reader.el.classList.add('d-none');
            }
        }
        function error(err) {
            console.warn(err);// Prints any errors to the console
        }
    }
};
QrcodeScanner.template = "event_ticket_qr_scanner.QrCodeScanner";
registry.category("actions").add("js_function", QrcodeScanner);
