from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResUsers(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users'].with_context(no_reset_password=True)
        cls.viber_user = Users.create({
            'name': 'Viber Test User',
            'login': 'viber_test_user@example.com',
            'email': 'viber_test_user@example.com',
            'phone': '+911234567890',
        })
        cls.viber_user_without_phone = Users.create({
            'name': 'Viber Test User Without Phone',
            'login': 'viber_test_user_without_phone@example.com',
            'email': 'viber_test_user_without_phone@example.com',
            'phone': False,
        })

    def test_get_users_returns_expected_payload_structure(self):
        data = self.env['res.users'].get_users()

        self.assertIsInstance(data, dict)
        self.assertIn('users', data)
        self.assertIsInstance(data['users'], list)
        self.assertTrue(data['users'])
        for user_values in data['users']:
            self.assertEqual(set(user_values), {'id', 'name', 'phone'})

    def test_get_users_includes_user_contact_details(self):
        data = self.env['res.users'].get_users()
        users_by_id = {
            user_values['id']: user_values for user_values in data['users']
        }

        self.assertEqual(users_by_id[self.viber_user.id], {
            'id': self.viber_user.id,
            'name': self.viber_user.name,
            'phone': self.viber_user.phone,
        })
        self.assertEqual(users_by_id[self.viber_user_without_phone.id], {
            'id': self.viber_user_without_phone.id,
            'name': self.viber_user_without_phone.name,
            'phone': False,
        })
