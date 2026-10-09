# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import json

from odoo.tests import new_test_user, tagged

from .common import AiAccountingCommon


@tagged('post_install', '-at_install')
class TestQueryTools(AiAccountingCommon):
    """Generic read-only queries: results, limits and security."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        (cls.partner_a + cls.partner_b).customer_rank = 1
        cls.partner_a.country_id = cls.env.ref('base.be')
        cls.partner_b.country_id = cls.env.ref('base.us')
        cls.inv_1 = cls.init_invoice('out_invoice', cls.partner_a, '2026-10-05', post=True,
                                     amounts=[1000.0], taxes=[])
        cls.inv_2 = cls.init_invoice('out_invoice', cls.partner_a, '2026-09-05', post=True,
                                     amounts=[500.0], taxes=[])

    def query(self, user=None, **arguments):
        toolkit = self.toolkit.with_user(user) if user else self.toolkit
        return toolkit._ai_run_tool('query_records', arguments)

    def ok(self, **arguments):
        output = self.query(**arguments)
        self.assertFalse(output.get('error'), output['model'])
        return output

    def test_count_customers(self):
        output = self.ok(model='res.partner', domain='[["customer_rank", ">", 0]]', fields=['name', 'country_id'])
        expected = self.env['res.partner'].search_count([('customer_rank', '>', 0)])
        self.assertEqual(output['model']['count'], expected)
        names = [row[0] for row in output['model']['rows']]
        self.assertIn(self.partner_a.name, names)
        row = output['blocks'][0]['rows'][0]
        self.assertEqual(row['res_model'], 'res.partner')

    def test_group_by_and_sum(self):
        output = self.ok(model='res.partner', domain='[["customer_rank", ">", 0], ["id", "in", %s]]'
                         % json.dumps((self.partner_a + self.partner_b).ids), group_by=['country_id'])
        counts = {row[0]: row[1] for row in output['model']['rows']}
        self.assertEqual(counts, {'Belgium': 1, 'United States': 1})
        output = self.ok(model='account.move', domain=json.dumps([['id', 'in', (self.inv_1 + self.inv_2).ids]]),
                         group_by=['partner_id'], aggregate='amount_total:sum')
        self.assertEqual(output['model']['rows'], [[self.partner_a.display_name, 1500.0]])
        output = self.ok(model='account.move', domain=json.dumps([['id', 'in', (self.inv_1 + self.inv_2).ids]]),
                         group_by=['invoice_date:month'], aggregate='amount_total:sum', chart='bar')
        self.assertEqual([row[1] for row in output['model']['rows']], [500.0, 1000.0])
        self.assertEqual(output['blocks'][1]['type'], 'chart')

    def test_order_and_limit(self):
        output = self.ok(model='account.move', domain=json.dumps([['id', 'in', (self.inv_1 + self.inv_2).ids]]),
                         fields=['name', 'amount_total'], order='amount_total asc', limit=1)
        self.assertEqual(output['model']['count'], 2)
        self.assertEqual(output['model']['rows'], [[self.inv_2.name, 500.0]])

    def test_denied_models(self):
        for model in ('res.users', 'ir.config_parameter', 'ai.accounting.api.key', 'res.groups',
                      'mail.message', 'no.such.model'):
            output = self.query(model=model)
            self.assertTrue(output.get('error'), model)

    def test_secret_fields_are_blocked(self):
        output = self.query(model='account.move', fields=['name', 'access_token'])
        self.assertTrue(output.get('error'))
        output = self.query(model='account.move', domain='[["access_token", "!=", false]]')
        self.assertTrue(output.get('error'))
        output = self.query(model='account.move', domain='[["partner_id.signup_token", "!=", false]]')
        self.assertTrue(output.get('error'))

    def test_invalid_input(self):
        self.assertTrue(self.query(model='res.partner', domain='not json').get('error'))
        self.assertTrue(self.query(model='res.partner', domain='[["nope", "=", 1]]').get('error'))
        self.assertTrue(self.query(model='res.partner', domain='[["name", "=", "x", "y"]]').get('error'))
        self.assertTrue(self.query(model='res.partner', group_by=['name'], aggregate='name:drop').get('error'))
        self.assertTrue(self.query(model='res.partner', order='name; drop table').get('error'))

    def test_access_rights_apply(self):
        employee = new_test_user(self.env, login='ai_employee', groups='base.group_user')
        output = self.query(user=employee, model='account.move')
        self.assertTrue(output.get('error'))

    def test_records_without_related_records(self):
        """'Products never invoiced' is one call with the related filter."""
        product_invoice = self.init_invoice('out_invoice', self.partner_a, '2026-10-06', post=True,
                                            products=self.product_a)
        products = self.product_a + self.product_b
        related = {'mode': 'without', 'model': 'account.move.line', 'field': 'product_id',
                   'domain': json.dumps([['move_id.move_type', 'in', ['out_invoice', 'out_refund']]])}
        output = self.ok(model='product.product', domain=json.dumps([['id', 'in', products.ids]]),
                         related=related, fields=['display_name'])
        self.assertEqual(output['model']['ids'], self.product_b.ids)
        self.assertEqual(output['model']['count'], 1)
        output = self.ok(model='product.product', domain=json.dumps([['id', 'in', products.ids]]),
                         related=dict(related, mode='with'))
        self.assertEqual(output['model']['ids'], self.product_a.ids)
        self.assertTrue(product_invoice)

    def test_related_filter_errors_come_with_a_hint(self):
        output = self.query(model='product.product', related={
            'mode': 'without', 'model': 'account.move.line', 'field': 'partner_id'})
        self.assertTrue(output.get('error'))
        self.assertIn('related', output['model']['hint'])
        output = self.query(model='product.product', related={
            'mode': 'without', 'model': 'res.users', 'field': 'partner_id'})
        self.assertTrue(output.get('error'))

    def test_ids_and_display_flag(self):
        output = self.ok(model='res.partner', domain=json.dumps([['id', '=', self.partner_a.id]]), display=False)
        self.assertEqual(output['model']['ids'], self.partner_a.ids)
        self.assertEqual(output['blocks'], [])
        output = self.ok(model='account.move', domain=json.dumps([['id', 'in', (self.inv_1 + self.inv_2).ids]]),
                         group_by=['partner_id'])
        self.assertEqual(output['model']['group_ids'], self.partner_a.ids)

    def _products_created_at(self, *utc_datetimes):
        products = self.env['product.product'].create([{'name': 'AI tz %s' % index}
                                                      for index in range(len(utc_datetimes))])
        for product, moment in zip(products, utc_datetimes):
            self.env.cr.execute("UPDATE product_product SET create_date = %s WHERE id = %s",
                                (moment, product.id))
        products.invalidate_recordset(['create_date'])
        return products

    def test_gpt_style_empty_arguments(self):
        """Exact call that failed in production: every optional parameter
        sent, with an empty 'related' object."""
        output = self.ok(**{
            "chart": "none", "limit": 10, "model": "product.product", "order": "",
            "domain": '[["create_date",">=","2026-10-01"],["create_date","<=","2026-10-31"]]',
            "fields": ["id"], "display": False,
            "related": {"mode": "without", "field": "", "model": "", "domain": ""},
            "group_by": [], "aggregate": "count"})
        self.assertIn('count', output['model'])

    def test_empty_arguments_on_dedicated_tools(self):
        output = self.toolkit._ai_run_tool('get_top_partners', {
            'kind': 'customer', 'period': '', 'date_from': '', 'date_to': '', 'chart': 'none', 'limit': None})
        self.assertFalse(output.get('error'), output['model'])

    def test_related_needs_model_and_field(self):
        output = self.query(model='product.product', related={'mode': 'without', 'model': 'account.move.line'})
        self.assertIn('related needs both', output['model']['error'])

    def test_period_on_datetime_field_uses_whole_local_days(self):
        self.env.user.tz = 'UTC'
        products = self._products_created_at('2026-10-31 20:00:00', '2026-11-01 00:30:00', '2026-10-01 00:00:00')
        output = self.ok(model='product.product', domain=json.dumps([['id', 'in', products.ids]]),
                         period='custom', date_from='2026-10-01', date_to='2026-10-31', date_field='create_date')
        self.assertEqual(sorted(output['model']['ids']), sorted((products[0] + products[2]).ids))

    def test_period_follows_user_time_zone(self):
        self.env.user.tz = 'Asia/Kolkata'  # UTC+05:30
        products = self._products_created_at('2026-09-30 20:00:00', '2026-10-31 20:00:00')
        output = self.ok(model='product.product', domain=json.dumps([['id', 'in', products.ids]]),
                         period='custom', date_from='2026-10-01', date_to='2026-10-31', date_field='create_date')
        # Oct 1 01:30 local is in October, Nov 1 01:30 local is not.
        self.assertEqual(output['model']['ids'], products[0].ids)

    def test_period_needs_a_date_field(self):
        output = self.query(model='res.partner', period='this_month', date_field='name')
        self.assertTrue(output.get('error'))

    def test_describe_data(self):
        output = self.toolkit._ai_run_tool('describe_data', {'search': 'journal entry'})
        self.assertIn('account.move', [model for model, _name in output['model']['models']])
        self.assertFalse([model for model, _name in output['model']['models'] if model.startswith('ir.')])
        output = self.toolkit._ai_run_tool('describe_data', {'model': 'res.partner'})
        fields_info = output['model']['fields']
        self.assertIn('customer_rank:integer', fields_info)
        self.assertFalse([spec for spec in fields_info if 'token' in spec])
        output = self.toolkit._ai_run_tool('describe_data', {'model': 'res.users'})
        self.assertTrue(output.get('error'))
