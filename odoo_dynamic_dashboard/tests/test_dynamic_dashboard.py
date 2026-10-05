from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestDynamicDashboard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_owner = new_test_user(
            cls.env, login='dashboard_owner', groups='odoo_dynamic_dashboard.odoo_dynamic_dashboard_group_user',
        )
        cls.user_other = new_test_user(
            cls.env, login='dashboard_other', groups='odoo_dynamic_dashboard.odoo_dynamic_dashboard_group_user',
        )
        cls.partner_model = cls.env['ir.model']._get('res.partner')
        cls.partners = cls.env['res.partner'].create([
            {'name': 'Dashboard Invoice A', 'type': 'invoice', 'color': 3},
            {'name': 'Dashboard Invoice B', 'type': 'invoice', 'color': 4},
            {'name': 'Dashboard Contact', 'type': 'contact', 'color': 5},
        ])
        cls.domain = str([('id', 'in', cls.partners.ids)])
        cls.dashboard = cls.env['dynamic.dashboard'].with_user(cls.user_owner).create({'name': 'Partners'})

    def _field(self, name):
        return self.env['ir.model.fields']._get('res.partner', name)

    def _create_block(self, **values):
        return self.env['dynamic.dashboard.block'].with_user(self.user_owner).create({
            'name': 'Block',
            'dashboard_id': self.dashboard.id,
            'model_id': self.partner_model.id,
            'domain': self.domain,
            **values,
        })

    def test_tile_aggregates(self):
        self._create_block(name='Count')
        self._create_block(name='Sum', aggregate='sum', measure_field_id=self._field('color').id)
        data = self.dashboard.with_user(self.user_owner).get_dashboard_data()
        self.assertTrue(data['can_edit'])
        self.assertEqual([block['value'] for block in data['blocks']], [3, 12])

    def test_chart_groups(self):
        self._create_block(block_type='bar', group_by_field_id=self._field('type').id)
        [block] = self.dashboard.with_user(self.user_owner).get_dashboard_data()['blocks']
        self.assertFalse(block['error'])
        [serie] = block['series']
        self.assertEqual(dict(zip(block['labels'], serie['values'])), {'Invoice': 2, 'Contact': 1})
        invoice_domain = serie['domains'][block['labels'].index('Invoice')]
        self.assertEqual(self.env['res.partner'].search(invoice_domain), self.partners[:2])

    def test_chart_requires_group_by(self):
        with self.assertRaises(ValidationError):
            self._create_block(block_type='pie')

    def test_misconfigured_domain(self):
        self._create_block(domain="[('no_such_field', '=', 1)]")
        [block] = self.dashboard.with_user(self.user_owner).get_dashboard_data()['blocks']
        self.assertTrue(block['error'])

    def test_access_rights(self):
        self._create_block()
        Dashboard = self.env['dynamic.dashboard'].with_user(self.user_other)
        self.assertFalse(Dashboard.search([('id', '=', self.dashboard.id)]))
        self.dashboard.is_shared = True
        shared = Dashboard.browse(self.dashboard.id)
        data = shared.get_dashboard_data()
        self.assertFalse(data['can_edit'])
        self.assertEqual(data['blocks'][0]['value'], 3)
        with self.assertRaises(AccessError):
            shared.name = 'Hijacked'
