odoo.define('event_ticket_qr_scanner.scan_ticket_qrcode', function (require){
"Use strict";
var core = require('web.core');
var rpc = require('web.rpc');
var AbstractAction = require('web.AbstractAction');
var QrcodeScanner = AbstractAction.extend({
/*
    Open Qr Code scanner Window
*/
 contentTemplate: 'event_ticket_qr_scanner.QrCodeScanner',
        events: {
        'click #barcode-scanner': 'load_qr',
        'click #mark_as_attending': 'markAsAttending'
        },
        load_qr: function (ev) {
            this.$('#result').html("")
            var self = this;
            const scanner = new Html5QrcodeScanner('reader', {
            qrbox: {
                width: 250,
                height: 250,
                },  // Sets dimensions of scanning box (set relative to reader element width)
            fps: 20, // Frames per second to attempt a scan
            });
            scanner.render(success, error);
            // Starts scanner
            function success(data) {
                const keyValuePairs = data.split(',');
                const result = {};
                for (const pair of keyValuePairs) {
                    const [key, value] = pair.split(':');
                    const trimmedKey = key.trim();
                    const trimmedValue = value.trim();
                    result[trimmedKey] = trimmedValue;
                }
                if (result.hasOwnProperty('Event')){
                    this.$('#result').html(`
                        <div style="text-align: center;" id='success_message'>
                        <h2>Success!</h2>
                        <p>Event : ${result['Event']}</p>
                        </div>`);
                scanner.clear();
                self.$('#reader').css('display', 'none');
                var domain = [['event_ticket_id','=',parseInt(result['Ticket'])],
                ['event_id','=',parseInt(result['code'])], ['state','in',['open','draft']]];
                var fields = ['name','partner_id'];
                rpc.query({
                   model: 'event.registration',
                   method: 'search_read',
                   args: [domain,fields],
                    }).then(function(vals){
                     if (vals.length === 0) {
                        this.$("#success_message").append(`<p style="color:red;">No Attendee Found!!</p>`);
                     }
                    else{
                        this.$('#success_message').append(`<label style="display: inline-flex;" for="select_attendee_id">
                        Select Attendee : <select name="select_attendee_id" id="select_attendee_id" class="attendee_selection"
                        style="">
                        </select></label><br/><br/><button id="mark_as_attending" icon="fa fa-check" class="btn btn-primary">
                        Mark as Attending</button>`)
                        for (let i = 0; i < vals.length; i++) {
                        var htmlToAppend = "<option id='option' value="+vals[i]['id']+">"+vals[i]['name']+"</option>";
                        this.$("#select_attendee_id").append(htmlToAppend);
                        };
                    }
                    });
                }
                else{
                this.$('#result').html(`<h2 style="color:red;">Invalid!</h2>`)
                scanner.clear();
                this.$el.find('#reader').css('display', 'none');
                }
            }
            function error(err) {
                console.warn(err);// Prints any errors to the console
            }
        },
        // Mark Selected attendees as attended the event
        markAsAttending(ev){
        var self = this;
        var attendee_id = this.$el.find('#select_attendee_id').val()
        rpc.query({
           model: 'event.registration',
           method: 'action_set_done',
           args: [parseInt(attendee_id)],
        }).then(function(){
              location.reload();
        });
        },
    });
    core.action_registry.add('js_function', QrcodeScanner);
     return QrcodeScanner;
});
