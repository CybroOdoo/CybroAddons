/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.OrderTrackingWidget = publicWidget.Widget.extend({
    init() {
        this.rpc = this.bindService("rpc");
    },
    // Bind the widget to the #deliveryTrackingForm element
		selector: '.TrackingTemplates',

    // Handler for the delivery tracking form submit event
		events: {
			'click #trackingInputBtn': '_onDeliveryTracking',
			'click #TrackingUpdate': '_onDeliveryTrackingUpdate',
			'input #trackingNumberInput': '_onTrackingNumberInput',
		},

        _onTrackingNumberInput:function(ev){
		if(!this.$el.find("#trackingNumberInput").val()){
		this.$el.find("#trackedTableDetails").hide();
		}
		},

		_onDeliveryTracking: function(ev) {
			let self = this
			//     Submit event handler for delivery tracking form
			self.$el.find('#deliveryTrackingForm').submit(function(e) {

				e.preventDefault();

				// Get the tracking number from the input field
				var trackingNumber = self.$el.find("#trackingNumberInput").val();
				// Call the server-side controller to update tracking details
				self.rpc("/tracking/details/update", {
                    'input_data': trackingNumber,
                 }).then(function(data) {
                    let noRecordsMsg = self.$el.find('#noRecordsMsg');
					// Check if data exists
					if (data.length > 0) {
					    		self.$el.find("#trackedTableDetails").show();
						// Display the tracking details in a table
						self.$el.find("#trackedTableDetails").html(`
                    <table class="table">
                        <thead class="thead-dark">
                            <tr>
                                <th scope="col">Sale Order</th>
                                <th scope="col">Delivery Partner</th>
                                <th scope="col">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>${data[0][1]}</td>
                                <td>${data[0][2]}</td>
                                <td>${data[0][3]}</td>
                            </tr>
                        </tbody>
                    </table>
                `);
						self.$el.find('#noRecordsMsg').hide();
					}

					// If no data is returned, display an alert and hide the table
					if (data.length <= 0) {
						self.$el.find('#NoRecordsApiKey').modal('show');
						self.$el.find("#trackedTableDetails").hide();
					}
                    });
			});
		},

		_onDeliveryTrackingUpdate: function(ev) {
			let self = this
			// Submit event handler for editing tracking status form
			self.$el.find('#editTrackingStatusForm').submit(function(e) {
				e.preventDefault();
				// Get input values
				var trackingNumber = self.$el.find("#trackingNumber").val();
				var apiKey = self.$el.find("#apiKey").val();
				var trackingStatus = self.$el.find("#trackingStatus").val();

				// Call the server-side controller to edit tracking status
				self.rpc("/tracking/details/edit", {
                    'api_key': apiKey,
					'tracking_number': trackingNumber,
					'tracking_status': trackingStatus,
                }).then(function(data) {
                    if (data.length > 0) {
						// Show success modal if data is returned
						self.$el.find('#successApiKey').modal('show');
					} else {
						// Show failure modal if no data is returned
						self.$el.find('#failedApiKey').modal('show');
					}
                });
			});
		},
})

