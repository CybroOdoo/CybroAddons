/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, useRef } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

export class QrcodeScanner extends Component {
    setup() {
        super.setup();
        this.result = useRef("result");
        this.reader = useRef("reader");
        this.orm = useService("orm");

        // Ensure QR scanner loads only when the component is mounted
        onMounted(() => {
            this.loadQRScanner();
        });
    }

    async loadQRScanner() {
        await loadJS("https://cdn.jsdelivr.net/npm/html5-qrcode@2.3.8/html5-qrcode.min.js");
        this.startQRScanner();
    }

    startQRScanner() {
        if (!this.reader.el) {
            console.error("❌ QR Scanner Error: Element with ID 'reader' not found!");
            return;
        }

        this.qrScanner = new Html5QrcodeScanner("reader", {
            qrbox: { width: 250, height: 250 },
            fps: 20,
        });

        this.qrScanner.render(
            (data) => this.onScanSuccess(data),
            (err) => console.warn("QR Scan Error:", err)
        );
    }

    async onScanSuccess(data) {
        console.log("✅ Scanned Data:", data);
        this.qrScanner.clear();
        this.reader.el.classList.add("d-none");
        this.result.el.style.padding = "12px";

        // Parsing scanned QR data
        const keyValuePairs = data.split(',');
        const result = {};
        for (const pair of keyValuePairs) {
            const [key, value] = pair.split(':');
            if (value) result[key.trim()] = value.trim();
        }

        if (!result['Event'] || !result['Ticket'] || !result['code']) {
            this.result.el.innerHTML = `<h2 style="color:red;">Invalid QR Code!</h2>`;
            return;
        }

        var domain = [['event_ticket_id', '=', parseInt(result['Ticket'])],
                      ['event_id', '=', parseInt(result['code'])], ['state', '=', 'open']];
        var fields = ['name', 'partner_id'];

        const attendees = await this.orm.call('event.registration', 'search_read', [domain, fields]);

        let successHTML = `<h2 style="color:green;">Success! Ticket Scanned</h2>
                           <p>Event: <strong>${result['Event']}</strong></p>`;

        if (attendees.length === 0) {
            successHTML += `<p style="color:red;">No Attendee Found!</p>`;
        } else {
            successHTML += `<label for="select_attendee_id">Select Attendee:</label>
                            <select id="select_attendee_id" class="attendee_selection">`;
            attendees.forEach(attendee => {
                successHTML += `<option value="${attendee.id}">${attendee.name}</option>`;
            });
            successHTML += `</select><br/><br/>
                            <button id="mark_as_attending" class="btn btn-primary">Mark as Attending</button>`;
        }

        this.result.el.innerHTML = successHTML;

        if (attendees.length > 0) {
            document.getElementById("mark_as_attending").addEventListener("click", async () => {
                const selectedId = document.getElementById("select_attendee_id").value;
                await this.orm.call('event.registration', 'action_set_done', [parseInt(selectedId)]);
                location.reload();
            });
        }
    }
}

QrcodeScanner.template = "event_ticket_qr_scanner.QrCodeScanner";
registry.category("actions").add("js_function", QrcodeScanner);
