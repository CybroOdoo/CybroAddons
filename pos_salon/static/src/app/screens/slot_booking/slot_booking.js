import { Component, useState, onWillStart } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { formatSalonAmount } from "@pos_salon/app/utils/salon_currency";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { SalonCustomerField } from "@pos_salon/app/components/salon_customer/salon_customer";
import { SalonBookingSummary } from "@pos_salon/app/components/salon_booking_summary/salon_booking_summary";
import { getLocalToday } from "@pos_salon/app/utils/salon_date";

export class SlotBookingScreen extends Component {
    static template = "pos_salon.SlotBookingScreen";
    static components = { SalonCustomerField, SalonBookingSummary };

    setup() {
        this.pos = usePos();
        this.dialog = useService("dialog");
        this.orm = useService("orm");

        const {
            selectedServices = [], totalPrice = 0, totalDuration = 0, customer = {},
            specialistId = '', selectedAmenities = [],
        } = this.props || {};
        const today = getLocalToday();

        this.state = useState({
            selectedServices,
            totalPrice,
            totalDuration,
            selectedSlots: {},
            bookedSlots: {},
            selectedDate: today,
            showCustomerPopup: false,
            showThankYouPopup: false,
            partnerId: customer.partnerId || false,
            customerName: customer.customerName || '',
            customerPhone: customer.customerPhone || '',
            customerEmail: customer.customerEmail || '',
            partnerHadPhone: customer.partnerHadPhone || false,
            specialistId: specialistId ? String(specialistId) : "",
            selectedAmenities: [...selectedAmenities],
            specialists: [],
            amenities: [],
        });

        onWillStart(async () => {
            const options = await this.orm.call(
                "salon.booking", "get_booking_options", [this.pos.config.id]
            );
            this.state.specialists = options.specialists;
            this.state.amenities = options.amenities;
            await this.loadUnavailableSlots();
        });

        this.startTime = 10;
        this.endTime = 20;
        this.slotInterval = 30;
        this.pastCutoffMinutes = 5;
        this.allSlots = this.generateSlots();

    }

    generateSlots() {
        const slots = [];
        let start = this.startTime * 60;
        const end = this.endTime * 60;
        while (start < end) {
            const hours = Math.floor(start / 60);
            const minutes = start % 60;
            slots.push(this.formatTime(hours, minutes));
            start += this.slotInterval;
        }
        return slots;
    }

    formatAmount(value) {
        return formatSalonAmount(this.pos, value);
    }

    formatTime(hours, minutes) {
        const suffix = hours >= 12 ? "PM" : "AM";
        const displayHour = ((hours + 11) % 12) + 1;
        const displayMinute = minutes.toString().padStart(2, "0");
        return `${displayHour}:${displayMinute} ${suffix}`;
    }

    isSlotBooked(slot) {
        const booked = this.state.bookedSlots[this.state.selectedDate] || [];
        return booked.includes(slot);
    }

    selectSlot(serviceId, slot) {
        const service = this.state.selectedServices.find(s => s.serviceId === serviceId);
        if (!service) return;

        const duration = parseInt(service.duration);
        const slotsNeeded = Math.ceil(duration / this.slotInterval);
        const startIndex = this.allSlots.indexOf(slot);
        if (startIndex === -1) return;

        const newSlots = [];
        for (let i = 0; i < slotsNeeded; i++) {
            const nextSlot = this.allSlots[startIndex + i];
            if (!nextSlot) break;
            if (this.isSlotBooked(nextSlot)) {
                this.dialog.add(AlertDialog, {
                    title: _t("Slot Unavailable"),
                    body: _t("Slot is already booked!"),
                });
                return;
            }
            newSlots.push(nextSlot);
        }

        this.state.selectedSlots[serviceId] = newSlots;
    }

    isSlotSelected(serviceId, slot) {
        return this.state.selectedSlots[serviceId]?.includes(slot);
    }

    async changeDate(ev) {
        this.state.selectedDate = ev.target.value;
        this.state.selectedSlots = {};   // slots chosen for another date are not valid here
        await this.loadUnavailableSlots();
    }

    // Slots that cannot be booked: all seats taken, or the chosen specialist is busy
    async loadUnavailableSlots() {
        try {
            this.state.bookedSlots[this.state.selectedDate] = await this.orm.call(
                "salon.booking", "get_unavailable_slots",
                [
                    this.pos.config.id,
                    this.state.selectedDate,
                    this.state.specialistId ? parseInt(this.state.specialistId) : false,
                    this.getRescheduleList().map((r) => r.booking_id),
                ]
            );
        } catch (err) {
            this.state.bookedSlots[this.state.selectedDate] = [];
        }
    }

    isSlotPast(slot) {
        const now = new Date();
        const todayLocal = [
            now.getFullYear(),
            String(now.getMonth() + 1).padStart(2, "0"),
            String(now.getDate()).padStart(2, "0"),
        ].join("-");
        if (this.state.selectedDate !== todayLocal) {
            return false;   // other dates keep every slot
        }
        const index = this.allSlots.indexOf(slot);
        if (index === -1) {
            return false;
        }
        const slotStart = this.startTime * 60 + index * this.slotInterval;
        const nowMinutes = now.getHours() * 60 + now.getMinutes();
        return nowMinutes >= slotStart + this.slotInterval - this.pastCutoffMinutes;
    }

    isSlotUnavailable(service, slot) {
        if (this.isSlotPast(slot)) {
            return true;
        }
        const needed = Math.ceil(parseInt(service.duration) / this.slotInterval);
        const start = this.allSlots.indexOf(slot);
        if (start === -1 || start + needed > this.allSlots.length) {
            return true;
        }
        for (let i = 0; i < needed; i++) {
            if (this.isSlotBooked(this.allSlots[start + i])) {
                return true;
            }
        }
        return false;
    }

    hasFreeSlot(service) {
        return this.allSlots.some((slot) => !this.isSlotUnavailable(service, slot));
    }

    get allSlotsSelected() {
        return (
            this.state.selectedServices.length > 0 &&
            this.state.selectedServices.every(
                (s) => (this.state.selectedSlots[s.serviceId] || []).length > 0
            )
        );
    }

    async confirmBooking() {
        const unbooked = this.state.selectedServices.filter(
            s => !(this.state.selectedSlots[s.serviceId] || []).length
        );
        if (unbooked.length > 0) {
            this.dialog.add(AlertDialog, {
                title: _t("Missing Slots"),
                body: _t("Please select a slot for all services."),
            });
            return;
        }

        if (!this.state.selectedDate) {
            this.dialog.add(AlertDialog, {
                title: _t("Missing Date"),
                body: _t("Please select a booking date."),
            });
            return;
        }

        this.state.showCustomerPopup = true;
    }

    async saveCustomerInfo() {
        // Validate inputs
        if (!this.state.partnerId) {
            this.dialog.add(AlertDialog, {
                title: _t("Validation Error"),
                body: _t("Please select a customer"),
            });
            return;
        }
        if (!this.state.customerPhone.trim()) {
            this.dialog.add(AlertDialog, {
                title: _t("Validation Error"),
                body: _t("This customer has no phone number. Please fill in the phone number"),
            });
            return;
        }

        const services = this.state.selectedServices.map(s => s.serviceName).join(', ');

        const bookingData = {
            partner_id: this.state.partnerId,
            customer_name: this.state.customerName,
            customer_phone: this.state.customerPhone,
            customer_email: this.state.customerEmail,
            service_lines: JSON.stringify(this.state.selectedServices.map((s) => ({
                id: s.serviceId,
                name: s.serviceName,
                category: s.category,
                duration: s.duration,
                price: this.servicePrice(s),
            }))),
            date: this.state.selectedDate,
            slot: JSON.stringify(this.state.selectedSlots),
            service_name: services,
            state: 'confirmed',
            specialist_id: this.state.specialistId ? parseInt(this.state.specialistId) : false,
            amenity_ids: [[6, 0, [...this.state.selectedAmenities]]],
            amount_total: this.state.totalPrice,
            config_id: this.pos.config.id,
        };

        try {
            await this.orm.call("salon.booking", "create_booking", [bookingData, this.getRescheduleList()]);

            this.state.showCustomerPopup = false;
            this.state.partnerId = false;
            this.state.customerName = '';
            this.state.customerPhone = '';
            this.state.customerEmail = '';
            this.state.partnerHadPhone = false;
            this.state.specialistId = '';
            this.state.selectedAmenities = [];

            this.pos.router.navigate('SalonScreen');

        } catch (err) {
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("Could not save booking: ") + (err.data?.message || err.message || _t("Unknown error")),
            });
        }
    }

    servicePrice(service) {
        if (service.reschedule && service.reschedule.paid) {
            return 0;
        }
        return parseInt(String(service.price).replace(/[^0-9]/g, "")) || 0;
    }

    getRescheduleList() {
        return this.state.selectedServices
            .filter((s) => s.reschedule)
            .map((s) => ({
                booking_id: s.reschedule.booking_id,
                service_id: s.serviceId,
                name: s.serviceName,
            }));
    }

    get specialistName() {
        const specialist = this.state.specialists.find(
            (s) => String(s.id) === String(this.state.specialistId)
        );
        return specialist ? specialist.name : "";
    }

    get selectedAmenityList() {
        return this.state.amenities.filter((a) => this.state.selectedAmenities.includes(a.id));
    }

    get amenitiesTotal() {
        return this.selectedAmenityList.reduce((sum, a) => sum + (Number(a.price) || 0), 0);
    }

    get grandTotal() {
        return this.state.totalPrice + this.amenitiesTotal;
    }

    slotRange(serviceId) {
        const slots = this.state.selectedSlots[serviceId] || [];
        if (!slots.length) {
            return "";
        }
        const lastIndex = this.allSlots.indexOf(slots[slots.length - 1]);
        const endMinutes = this.startTime * 60 + (lastIndex + 1) * this.slotInterval;
        return `${slots[0]} - ${this.formatTime(Math.floor(endMinutes / 60), endMinutes % 60)}`;
    }

    get summaryLines() {
        return this.state.selectedServices.map((s) => ({
            name: s.serviceName,
            category: s.category,
            duration: s.duration,
            time: this.slotRange(s.serviceId),
            paid: !!(s.reschedule && s.reschedule.paid),
            price: this.servicePrice(s),
        }));
    }

    toggleAmenity(amenityId) {
        const index = this.state.selectedAmenities.indexOf(amenityId);
        if (index > -1) {
            this.state.selectedAmenities.splice(index, 1);
        } else {
            this.state.selectedAmenities.push(amenityId);
        }
    }

    closeCustomerPopup() {
        this.state.showCustomerPopup = false;
    }

    closeThankYouAndNavigate() {
        this.state.showThankYouPopup = false;
        this.pos.router.navigate('SalonScreen');
    }

    back() {
        this.pos.router.navigate("SalonScreen");
    }
}

registry.category("pos_pages").add("SlotBookingScreen", {
    name: "SlotBookingScreen",
    component: SlotBookingScreen,
    route: `/pos/ui/${odoo.pos_config_id}/slot-booking`,
});