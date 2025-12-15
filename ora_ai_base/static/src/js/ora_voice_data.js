/** @odoo-module **/
import { Component, useState } from "@odoo/owl";

//Handles real-time data updates for voice assistant interactions.
export class VoiceData extends Component {
        static template = "ora_ai_base.voice_data";
        setup() {
            this.state = useState({
                 customer: "",
                 products: [],
                 conversation: [],
            })
            this.busService = this.env.services.bus_service
            this.channel = "vapi_voice_channel"
            this.inbound_call_channel = "inbound_call_channel"
            this.busService.addChannel(this.channel)
            this.busService.addChannel(this.inbound_call_channel)
            this.busService.subscribe("notification", this.onMessage.bind(this))
        }

      onMessage(notifications) {
        if (notifications.channel === "vapi_voice_channel" || notifications.channel === "inbound_call_channel") {
            if (notifications?.value?.message?.conversation) {
                const conversation = notifications.value.message.conversation;
                const filteredConversation = conversation.filter(message => message.role !== 'system');
                this.state.conversation = filteredConversation;

            }
        }
        const channelsToMatch = [this.channel, this.inbound_call_channel];
        if (!channelsToMatch.includes(notifications.channel)) {
            console.warn("No notifications for the specified channel.");
            return;
        }
        if (!notifications.value || !Array.isArray(notifications.value)) {
            return;
        }
        const products = notifications.value.map(item => ({
            quantity: item.qty,
            customer: item.customer,
            product: item.product,
            variant: item.variant,
            product_id: item.id
        }));
        if (products.length > 0) {
            this.state.customer = products[0].customer;
            this.state.products = products;
        }
    }
}