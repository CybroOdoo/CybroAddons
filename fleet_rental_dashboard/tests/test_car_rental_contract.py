from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestFleetRentalDashboard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dashboard = cls.env['car.rental.contract'].sudo()
        cls.brand = cls.env['fleet.vehicle.model.brand'].sudo().create({
            'name': 'Dashboard Test Brand',
        })
        cls.model = cls.env['fleet.vehicle.model'].sudo().create({
            'name': 'Dashboard Test Model',
            'brand_id': cls.brand.id,
        })
        cls.customer = cls.env['res.partner'].sudo().create({
            'name': 'Dashboard Rental Customer',
            'email': 'dashboard.customer@example.com',
            'phone': '+911111111111',
        })
        cls.top_customer = cls.env['res.partner'].sudo().create({
            'name': 'Dashboard Top Customer',
            'email': 'dashboard.top.customer@example.com',
            'phone': '+912222222222',
        })
        cls.available_vehicle = cls._create_vehicle(
            'Dashboard Available Vehicle',
            rental_check_availability=True,
        )
        cls.running_vehicle = cls._create_vehicle(
            'Dashboard Running Vehicle',
            rental_check_availability=False,
        )
        cls.done_vehicle = cls._create_vehicle(
            'Dashboard Done Vehicle',
            rental_check_availability=False,
        )
        cls.running_contract = cls._create_contract(
            cls.running_vehicle,
            cls.customer,
            'running',
            '2026-01-01',
            '2026-01-10',
        )
        cls.done_contract = cls._create_contract(
            cls.done_vehicle,
            cls.customer,
            'done',
            '2026-01-02',
            '2026-01-11',
        )
        for day in range(1, 13):
            cls._create_contract(
                cls.done_vehicle,
                cls.top_customer,
                'done',
                f'2026-02-{day:02d}',
                f'2026-03-{day:02d}',
            )

    @classmethod
    def _create_vehicle(cls, name, rental_check_availability):
        return cls.env['fleet.vehicle'].sudo().create({
            'model_id': cls.model.id,
            'license_plate': name.upper().replace(' ', '-'),
            'rental_check_availability': rental_check_availability,
            'plan_to_change_car': False,
        })

    @classmethod
    def _create_contract(cls, vehicle, customer, state, start_date, end_date):
        return cls.env['car.rental.contract'].sudo().create({
            'customer_id': customer.id,
            'vehicle_id': vehicle.id,
            'cost': 100.0,
            'rent_start_date': start_date,
            'rent_end_date': end_date,
            'cost_frequency': 'no',
            'first_payment': 0.0,
            'state': state,
        })

    def test_vehicle_most_rented_returns_done_vehicle_counts(self):
        result = self.dashboard.vehicle_most_rented(False, False)

        self.assertIn(self.done_vehicle.name, result['name'])
        vehicle_index = result['name'].index(self.done_vehicle.name)
        self.assertGreaterEqual(result['num'][vehicle_index], 13)
        self.assertNotIn(self.running_vehicle.name, result['name'])

    def test_cars_availability_returns_available_and_running_counts(self):
        result = self.dashboard.cars_availability()

        self.assertGreaterEqual(result['available_cars'], 1)
        self.assertGreaterEqual(result['cars_running'], 1)

    def test_car_details_returns_running_and_available_vehicle_data(self):
        result = self.dashboard.car_details()

        running_details = [
            details for details in result['running_details']
            if details['vehicle'] == self.running_vehicle.name
        ]
        available_details = [
            details for details in result['available_cars']
            if details['available_car'] == self.available_vehicle.name
        ]
        self.assertEqual(running_details, [{
            'vehicle': self.running_vehicle.name,
            'start_date': self.running_contract.rent_start_date,
            'end_date': self.running_contract.rent_end_date,
            'customer': self.customer.name,
            'phone': self.customer.phone,
        }])
        self.assertEqual(available_details, [{
            'available_car': self.available_vehicle.name,
        }])

    def test_top_customers_returns_customer_details_ordered_by_rentals(self):
        result = self.dashboard.top_customers()

        self.assertTrue(result)
        self.assertEqual(result[0]['id'], self.top_customer.id)
        self.assertEqual(result[0]['name'], self.top_customer.name)
        self.assertEqual(result[0]['email'], self.top_customer.email)
        self.assertEqual(result[0]['image'], self.top_customer.image_1920)
