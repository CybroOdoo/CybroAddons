import { Component, useState, onWillStart } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { formatSalonAmount } from "@pos_salon/app/utils/salon_currency";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog, ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { SalonCustomerField } from "@pos_salon/app/components/salon_customer/salon_customer";
import { SalonBookingSummary } from "@pos_salon/app/components/salon_booking_summary/salon_booking_summary"
import { getLocalToday } from "@pos_salon/app/utils/salon_date";

export class BookAppointmentScreen extends Component {
    static template = "pos_salon.BookAppointmentScreen";
    static components = { SalonCustomerField, SalonBookingSummary };

    setup() {
        this.pos = usePos();
        this.dialog = useService("dialog");
        this.orm = useService("orm");
        this.alert = useService("alert");

        this.state = useState({
            selectedServices: [],
            showWizard: false,
            currentCategory: null,
            currentCategoryServices: [],
            showBookingPopup: true,
            bookingType: null,
            showCustomerPopup: false,
            showThankYouPopup: false,
            customerName: '',
            customerPhone: '',
            specialistId: '',
            selectedAmenities: [],
            specialists: [],
            amenities: [],
            partnerId: false,
            customerEmail: '',
            partnerHadPhone: false,
            showCustomerFirstPopup: false,
            bookedToday: [],
            walkinPlan: null,
            walkinStart: null,
            showPlanPopup: false,
            rescheduleRow: null,
            rescheduleOptions: [],
        });

        onWillStart(async () => {
            const options = await this.orm.call(
                "salon.booking", "get_booking_options", [this.pos.config.id]
            );
            this.state.specialists = options.specialists;
            this.state.amenities = options.amenities;
        });

        this.serviceCategories = [
            {
                id: 'hair',
                name: 'Hair Services',
                icon: '✂️',
                description: 'Professional hair care and styling',
                color: '#FF6B6B',
                serviceGroups: [
                    {
                        heading: 'Haircut',
                        services: [
                            { id: 'haircut_men', name: 'Men', price: '500', duration: '30 min' },
                            { id: 'haircut_women', name: 'Women', price: '600', duration: '45 min' },
                            { id: 'haircut_kids', name: 'Kids', price: '300', duration: '20 min' }
                        ]
                    },
                    {
                        heading: 'Hair Coloring',
                        services: [
                            { id: 'hair_coloring', name: 'Full Hair Coloring', price: '2000', duration: '90 min' },
                            { id: 'highlights', name: 'Highlights', price: '2500', duration: '120 min' },
                            { id: 'balayage', name: 'Balayage', price: '3500', duration: '150 min' }
                        ]
                    },
                    {
                        heading: 'Hair Styling',
                        services: [
                            { id: 'blowdry', name: 'Blow Dry', price: '600', duration: '30 min' },
                            { id: 'hair_styling', name: 'Hair Styling (Updo)', price: '1500', duration: '60 min' },
                            { id: 'straightening', name: 'Hair Straightening', price: '1200', duration: '60 min' },
                            { id: 'curling', name: 'Hair Curling', price: '800', duration: '45 min' }
                        ]
                    },
                    {
                        heading: 'Hair Treatment',
                        services: [
                            { id: 'keratin', name: 'Keratin Treatment', price: '4000', duration: '180 min' },
                            { id: 'deep_conditioning', name: 'Deep Conditioning', price: '1000', duration: '45 min' },
                            { id: 'scalp_treatment', name: 'Scalp Treatment', price: '1200', duration: '60 min' }
                        ]
                    },
                    {
                        heading: 'Hair Extensions & Weaving',
                        services: [
                            { id: 'hair_extensions', name: 'Hair Extensions', price: '5000', duration: '120 min' },
                            { id: 'hair_weaving', name: 'Hair Weaving', price: '6000', duration: '150 min' }
                        ]
                    }
                ]
            },
            {
                id: 'skin',
                name: 'Skin & Facial Services',
                icon: '💆',
                description: 'Rejuvenating skin treatments',
                color: '#4ECDC4',
                serviceGroups: [
                    {
                        heading: 'Facial Treatments',
                        services: [
                            { id: 'facial_hydrating', name: 'Hydrating Facial', price: '1500', duration: '60 min' },
                            { id: 'facial_antiaging', name: 'Anti-Aging Facial', price: '2500', duration: '75 min' },
                            { id: 'facial_acne', name: 'Acne Treatment Facial', price: '1800', duration: '60 min' }
                        ]
                    },
                    {
                        heading: 'Advanced Skin Treatments',
                        spaOnly: true,
                        services: [
                            { id: 'skin_peel', name: 'Chemical Peel', price: '2000', duration: '45 min' },
                            { id: 'exfoliation', name: 'Exfoliation Treatment', price: '1200', duration: '30 min' },
                            { id: 'microdermabrasion', name: 'Microdermabrasion', price: '2500', duration: '60 min' }
                        ]
                    },
                    {
                        heading: 'Waxing Services',
                        services: [
                            { id: 'wax_face', name: 'Face Waxing', price: '300', duration: '15 min' },
                            { id: 'wax_arms', name: 'Arms Waxing', price: '400', duration: '20 min' },
                            { id: 'wax_legs', name: 'Legs Waxing', price: '600', duration: '30 min' },
                        ]
                    },
                    {
                        heading: 'Threading & Shaping',
                        services: [
                            { id: 'threading', name: 'Threading', price: '100', duration: '10 min' },
                            { id: 'eyebrow_shaping', name: 'Eyebrow Shaping', price: '200', duration: '15 min' }
                        ]
                    }
                ]
            },
            {
                id: 'nail',
                name: 'Nail Services',
                icon: '💅',
                description: 'Complete nail care',
                color: '#FFD93D',
                serviceGroups: [
                    {
                        heading: 'Manicure',
                        services: [
                            { id: 'manicure_basic', name: 'Basic Manicure', price: '400', duration: '30 min' },
                            { id: 'manicure_spa', name: 'Spa Manicure', spaOnly: true, price: '800', duration: '45 min' },
                            { id: 'manicure_gel', name: 'Gel Manicure', price: '1200', duration: '60 min' }
                        ]
                    },
                    {
                        heading: 'Pedicure',
                        services: [
                            { id: 'pedicure_basic', name: 'Basic Pedicure', price: '500', duration: '40 min' },
                            { id: 'pedicure_spa', name: 'Spa Pedicure', spaOnly: true, price: '1000', duration: '60 min' },
                            { id: 'pedicure_gel', name: 'Gel Pedicure', price: '1500', duration: '75 min' }
                        ]
                    },
                    {
                        heading: 'Nail Art & Extensions',
                        services: [
                            { id: 'nail_art', name: 'Nail Art', price: '600', duration: '30 min' },
                            { id: 'nail_extensions', name: 'Nail Extensions', price: '2000', duration: '90 min' },
                            { id: 'nail_repair', name: 'Nail Repair', price: '300', duration: '20 min' }
                        ]
                    }
                ]
            },
            {
                id: 'massage',
                spaOnly: true,
                name: 'Massage & Body Treatments',
                icon: '💆‍♀️',
                description: 'Relaxing body therapies',
                color: '#A8E6CF',
                serviceGroups: [
                    {
                        heading: 'Massage Therapy',
                        services: [
                            { id: 'swedish_massage', name: 'Swedish Massage', price: '2000', duration: '60 min' },
                            { id: 'deep_tissue', name: 'Deep Tissue Massage', price: '2500', duration: '75 min' },
                            { id: 'aromatherapy', name: 'Aromatherapy Massage', price: '2200', duration: '60 min' }
                        ]
                    },
                    {
                        heading: 'Body Treatments',
                        services: [
                            { id: 'body_scrub', name: 'Body Scrub', price: '1800', duration: '45 min' },
                            { id: 'body_wrap', name: 'Body Wrap', price: '2500', duration: '60 min' }
                        ]
                    }
                ]
            },
            {
                id: 'makeup',
                name: 'Makeup Services',
                icon: '💄',
                description: 'Professional makeup artistry',
                color: '#FF6B9D',
                serviceGroups: [
                    {
                        heading: 'Makeup Application',
                        services: [
                            { id: 'party_makeup', name: 'Party Makeup', price: '2500', duration: '60 min' },
                            { id: 'event_makeup', name: 'Event Makeup', price: '3000', duration: '75 min' },
                            { id: 'bridal_makeup', name: 'Bridal Makeup', price: '8000', duration: '120 min' }
                        ]
                    },
                    {
                        heading: 'Eyelash Services',
                        services: [
                            { id: 'eyelash_extensions', name: 'Eyelash Extensions', price: '2000', duration: '90 min' },
                            { id: 'eyelash_lifting', name: 'Eyelash Lifting', price: '1500', duration: '45 min' }
                        ]
                    },
                    {
                        heading: 'Eyebrow Services',
                        services: [
                            { id: 'eyebrow_tinting', name: 'Eyebrow Tinting', price: '500', duration: '20 min' }
                        ]
                    }
                ]
            },
            {
                id: 'specialty',
                name: 'Specialty Services',
                icon: '⭐',
                description: 'Premium treatments',
                color: '#C7CEEA',
                serviceGroups: [
                    {
                        heading: 'Hair Removal',
                        services: [
                            { id: 'laser_hair_removal', name: 'Laser Hair Removal', price: '3000', duration: '45 min' },
                            { id: 'sugaring', name: 'Sugaring Hair Removal', price: '800', duration: '30 min' }
                        ]
                    },
                    {
                        heading: 'Men\'s Services',
                        services: [
                            { id: 'grooming_package', name: 'Men\'s Grooming Package', price: '2500', duration: '90 min' }
                        ]
                    }
                ]
            }
        ];
    }

    formatAmount(value) {
        return formatSalonAmount(this.pos, value);
    }

    getVisibleGroups(category) {
        const spaEnabled = this.pos.config.is_spa;
        return category.serviceGroups
            .filter((group) => !group.spaOnly || spaEnabled)
            .map((group) => ({
                ...group,
                services: group.services.filter((s) => !s.spaOnly || spaEnabled),
            }))
            .filter((group) => group.services.length > 0);
    }

    get visibleCategories() {
        const spaEnabled = this.pos.config.is_spa;
        return this.serviceCategories.filter(
            (category) => !category.spaOnly || spaEnabled
        );
    }

    async confirmBooking() {
        if (!this.state.customerName.trim()) {
            this.dialog.add(AlertDialog, {
                title: _t("Validation Error"),
                body: _t("Please enter customer name"),
            });
            return;
        }
        if (!this.state.customerPhone.trim()) {
            this.dialog.add(AlertDialog, {
                title: _t("Validation Error"),
                body: _t("Please enter phone number"),
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
            date: getLocalToday(),
            slot: "Walk-in",
            walkin_start: this.labelToMinutes(this.state.walkinStart),
            service_name: services,
            state: 'confirmed',
            specialist_id: this.state.specialistId ? parseInt(this.state.specialistId) : false,
            amenity_ids: [[6, 0, [...this.state.selectedAmenities]]],
            amount_total: this.getTotalPrice(),
            config_id: this.pos.config.id,
        };

        try {
            await this.orm.call("salon.booking", "create_booking", [bookingData, this.getRescheduleList()]);

            this.state.showCustomerPopup = false;
            this.state.showThankYouPopup = true;

            setTimeout(() => {
                this.state.showThankYouPopup = false;
                this.state.customerName = '';
                this.state.customerPhone = '';
                this.state.specialistId = '';
                this.state.selectedAmenities = [];
                this.pos.router.navigate('SalonScreen');
            }, 2000);

        } catch (err) {
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("Could not save booking: ") + (err.data?.message || err.message || _t("Unknown error")),
            });
        }
    }

    nowMinute() {
        const d = new Date();
        return d.getHours() * 60 + d.getMinutes();
    }

    labelToMinutes(label) {
        const m = /^(\d+):(\d+) (AM|PM)$/.exec((label || "").trim());
        if (!m) {
            return null;
        }
        return ((parseInt(m[1]) % 12) + (m[3] === "PM" ? 12 : 0)) * 60 + parseInt(m[2]);
    }

    minutesToLabel(minutes) {
        const h = Math.floor(minutes / 60) % 24;
        const mm = String(minutes % 60).padStart(2, "0");
        return `${((h + 11) % 12) + 1}:${mm} ${h >= 12 ? "PM" : "AM"}`;
    }

    get walkinRange() {
        const start = this.labelToMinutes(this.state.walkinStart);
        if (start === null) {
            return _t("today");
        }
        return `${this.state.walkinStart} - ${this.minutesToLabel(start + this.getTotalDuration())}`;
    }

    lateText(row) {
        if (row.checked_in) {
            return "";
        }
        const late = this.nowMinute() - row.start_minute;
        return late > 0 ? _t("Late by %s min", late) : "";
    }

    showError(err) {
        this.dialog.add(AlertDialog, {
            title: _t("Error"),
            body: err.data?.message || err.message || _t("Something went wrong"),
        });
    }

    async startWalkin() {
        try {
            this.state.walkinPlan = await this.orm.call(
                "salon.booking", "get_walkin_plan",
                [
                    this.pos.config.id,
                    this.todayStr(),
                    this.getTotalDuration(),
                    this.nowMinute(),
                    this.state.specialistId ? parseInt(this.state.specialistId) : false,
                ]
            );
        } catch (err) {
            this.showError(err);
            return;
        }
        if (this.state.walkinPlan.free_now) {
            this.state.showPlanPopup = false;
            this.state.walkinStart = this.state.walkinPlan.start;
            this.state.showCustomerPopup = true;
        } else {
            this.state.showPlanPopup = true;
        }
    }

    closePlanPopup() {
        this.state.showPlanPopup = false;
        this.state.rescheduleRow = null;
        this.state.rescheduleOptions = [];
    }

    pickWalkinTime(label) {
        this.state.walkinStart = label;
        this.closePlanPopup();
        this.state.showCustomerPopup = true;
    }

    async markArrived(row) {
        try {
            await this.orm.call("salon.booking", "action_mark_arrived", [[row.id]]);
            await this.startWalkin();
        } catch (err) {
            this.showError(err);
        }
    }

    async openReschedule(row) {
        try {
            this.state.rescheduleOptions = await this.orm.call(
                "salon.booking", "get_reschedule_options", [row.id, this.nowMinute()]
            );
            this.state.rescheduleRow = row;
        } catch (err) {
            this.showError(err);
        }
    }

    async rescheduleTo(label) {
        const row = this.state.rescheduleRow;
        try {
            await this.orm.call("salon.booking", "reschedule_booking", [row.id, label]);
            this.state.rescheduleRow = null;
            this.state.rescheduleOptions = [];
            await this.startWalkin();
        } catch (err) {
            this.showError(err);
        }
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

    get amenityNames() {
        return this.selectedAmenityList.map((a) => a.name).join(", ");
    }

    get amenitiesTotal() {
        return this.selectedAmenityList.reduce((sum, a) => sum + (Number(a.price) || 0), 0);
    }

    get grandTotal() {
        return this.getTotalPrice() + this.amenitiesTotal;
    }

    get summaryLines() {
        return this.state.selectedServices.map((s) => ({
            name: s.serviceName,
            category: s.category,
            duration: s.duration,
            time: "",
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

    selectBookingType(type) {
        this.state.bookingType = type;
        this.state.showBookingPopup = false;
        if (!this.state.partnerId) {
            this.state.showCustomerFirstPopup = true;
        }
    }

    todayStr() {
        return getLocalToday();
    }

    async confirmCustomer() {
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
        try {
            this.state.bookedToday = await this.orm.call(
                "salon.booking", "get_customer_day_services",
                [this.state.partnerId, this.todayStr()]
            );
        } catch (err) {
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: err.data?.message || err.message || _t("Could not load the customer's bookings"),
            });
            return;
        }
        if (this._previousPartnerId !== this.state.partnerId) {
            this.state.selectedServices = [];
        }
        this.state.showCustomerFirstPopup = false;
    }

    changeCustomer() {
        this._previousPartnerId = this.state.partnerId;
        this.state.showCustomerFirstPopup = true;
    }

    getBookedInfo(service) {
        const match = (b) =>
            b.service_id ? b.service_id === service.id : b.name === service.name;
        return (
            this.state.bookedToday.find((b) => match(b) && b.can_reschedule) ||
            this.state.bookedToday.find(match)
        );
    }

    bookedLabel(service) {
        const b = this.getBookedInfo(service);
        if (!b) {
            return "";
        }
        let when = _t("today");
        if (b.slot === "Walk-in") {
            when = _t("today (walk-in)");
        } else if (b.slot) {
            when = _t("at %s", b.slot);
        }
        const status = b.completed ? _t("Completed") : _t("Booked");
        const pay = b.paid ? _t("Paid") : _t("Unpaid");
        return `${status} ${when} · ${pay}`;
    }

    onServiceClick(service) {
        if (this._rescheduleDialogOpen) {
            return;
        }
        const category = this.state.currentCategory;
        const booked = this.getBookedInfo(service);

        if (!booked || !booked.can_reschedule || this.isSubServiceSelected(service.id)) {
            return this.selectSubService(service, null, category, false);
        }

        const body = booked.paid
            ? _t("%s already has this service booked and paid (%s). Do you want to reschedule it? It will not be charged again.",
                 this.state.customerName, this.bookedLabel(service))
            : _t("%s already has this service booked and not paid yet (%s). Do you want to cancel it and reschedule?",
                 this.state.customerName, this.bookedLabel(service));

        this._rescheduleDialogOpen = true;
        this.dialog.add(
            ConfirmationDialog,
            {
                title: _t("Already booked"),
                body,
                confirmLabel: _t("Yes, reschedule"),
                cancelLabel: _t("Cancel"),
                confirm: () => this.selectSubService(service, booked, category, true),
            },
            {
                onClose: () => {
                    this._rescheduleDialogOpen = false;
                },
            }
        );
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

    getTotalServicesCount(category) {
        return this.getVisibleGroups(category).reduce((total, group) => total + group.services.length, 0);
    }

    openServiceWizard(category) {
        this.state.currentCategory = category;
        this.state.currentCategoryServices = this.getVisibleGroups(category);
        this.state.showWizard = true;
    }

    closeWizard() {
        this.state.showWizard = false;
        this.state.currentCategory = null;
        this.state.currentCategoryServices = [];
    }

    selectSubService(service, booked = null, category = null, forceAdd = false) {
        category = category || this.state.currentCategory;
        if (!category) {
            return;
        }

        const serviceObj = {
            categoryId: category.id,
            category: category.name,
            serviceId: service.id,
            serviceName: service.name,
            price: service.price,
            duration: service.duration,
            icon: category.icon,
            color: category.color,
            reschedule: booked
                ? { booking_id: booked.booking_id, paid: booked.paid, old_slot: booked.slot }
                : null,
        };

        const existingIndex = this.state.selectedServices.findIndex(
            s => s.serviceId === service.id
        );

        if (existingIndex > -1) {
            this.state.selectedServices.splice(existingIndex, 1);
            if (!forceAdd) {
                return;
            }
        }
        this.state.selectedServices.push(serviceObj);
    }

    isSubServiceSelected(serviceId) {
        return this.state.selectedServices.some(s => s.serviceId === serviceId);
    }

    removeService(index) {
        this.state.selectedServices.splice(index, 1);
    }

    clearAllServices() {
        this.state.selectedServices = [];
    }

    getTotalPrice() {
        return this.state.selectedServices.reduce(
            (total, service) => total + this.servicePrice(service), 0
        );
    }

    getTotalDuration() {
        return this.state.selectedServices.reduce((total, service) => {
            const duration = parseInt(service.duration);
            return total + duration;
        }, 0);
    }

    viewAvailableSlots() {
        if (this.state.selectedServices.length === 0) {
            this.alert.add("Please select at least one service");
            return;
        }

        if (this.pos.router) {
            this.pos.router.navigate("SlotBookingScreen", {
                selectedServices: this.state.selectedServices,
                totalPrice: this.getTotalPrice(),
                totalDuration: this.getTotalDuration(),
                customer: {
                    partnerId: this.state.partnerId,
                    customerName: this.state.customerName,
                    customerPhone: this.state.customerPhone,
                    customerEmail: this.state.customerEmail,
                    partnerHadPhone: this.state.partnerHadPhone,
                },
                specialistId: this.state.specialistId,
                selectedAmenities: [...this.state.selectedAmenities],
            });
        }
    }

    back() {
        if (this.pos.router) {
            this.pos.router.navigate("SalonScreen");
        }
    }
}

registry.category("pos_pages").add("BookAppointmentScreen", {
    name: "BookAppointmentScreen",
    component: BookAppointmentScreen,
    route: `/pos/ui/${odoo.pos_config_id}/book-appointment`,
});