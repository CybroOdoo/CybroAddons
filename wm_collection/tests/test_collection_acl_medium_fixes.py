#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
import base64

from lxml import etree

from odoo.tests import TransactionCase, tagged

# 1x1 transparent PNG
_PNG = base64.b64encode(base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
))


@tagged('post_install', '-at_install', 'wm_security')
class TestCollectionAclMediumFixes(TransactionCase):
    """Regression tests for the medium-severity ACL / view / report fixes."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.users = {}
        for key, xmlid in (
            ('internal', 'base.group_user'),
            ('driver', 'wm_base.group_wm_driver'),
            ('dispatcher', 'wm_base.group_wm_dispatcher'),
            ('inventory', 'wm_base.group_wm_inventory_operator'),
            ('finance', 'wm_base.group_wm_finance'),
        ):
            user = cls.env['res.users'].create({
                'name': 'ACL medium %s' % key,
                'login': 'acl_medium_%s@example.com' % key,
            })
            cls.env.ref(xmlid).write({'user_ids': [(4, user.id)]})
            cls.users[key] = user

    def _can(self, user, model, mode):
        return self.env[model].with_user(user).has_access(mode)

    # V-08 ---------------------------------------------------------------
    def test_internal_user_read_only_on_operational_models(self):
        """Plain internal users can only read signatures; finance can read, but
        not edit, missed collections and gate entries (and their lines)."""
        for model in ('wm.signature',):
            self.assertTrue(self._can(self.users['internal'], model, 'read'), model)
            self.assertFalse(self._can(self.users['internal'], model, 'write'), model)
            self.assertFalse(self._can(self.users['internal'], model, 'create'), model)
        models = (
            'wm.signature', 'wm.missed.collection', 'wm.facility.gate.entry',
            'wm.facility.gate.entry.line', 'wm.facility.gate.entry.rejection.line',
        )
        for model in models:
            self.assertTrue(self._can(self.users['finance'], model, 'read'), model)
            self.assertFalse(self._can(self.users['finance'], model, 'write'), model)
            self.assertFalse(self._can(self.users['finance'], model, 'create'), model)
        for model in models[1:]:
            self.assertFalse(self._can(self.users['internal'], model, 'read'), model)

    def test_operational_roles_keep_write_access(self):
        """Roles running the flows keep create/write rights."""
        expected = {
            'driver': ('wm.signature', 'wm.missed.collection'),
            'dispatcher': ('wm.signature', 'wm.missed.collection', 'wm.facility.gate.entry',
                           'wm.facility.gate.entry.line', 'wm.facility.gate.entry.rejection.line'),
            'inventory': ('wm.facility.gate.entry', 'wm.facility.gate.entry.line',
                          'wm.facility.gate.entry.rejection.line'),
        }
        for key, models in expected.items():
            for model in models:
                for mode in ('read', 'write', 'create'):
                    self.assertTrue(self._can(self.users[key], model, mode), (key, model, mode))
        # Pure drivers do not manage facility gate entries.
        self.assertFalse(self._can(self.users['driver'], 'wm.facility.gate.entry', 'create'))

    # V-07 ---------------------------------------------------------------
    def test_company_rules_exist(self):
        for model in ('wm.container', 'wm.facility.gate.entry', 'wm.collection.report',
                      'wm.route.efficiency.report', 'wm.driver.performance.report',
                      'wm.fleet.expiry.report', 'wm.maintenance.history.report'):
            rules = self.env['ir.rule'].search([
                ('model_id.model', '=', model), ('global', '=', True),
                ('domain_force', 'ilike', 'company_ids'),
            ])
            self.assertTrue(rules, 'Missing multi-company rule on %s' % model)

    # V-06 ---------------------------------------------------------------
    def test_driver_does_not_see_start_route_or_map_buttons(self):
        def buttons(user):
            arch = self.env['wm.route'].with_user(user).get_views([(False, 'form')])['views']['form']['arch']
            return {b.get('name') for b in etree.fromstring(arch).iter('button')}

        driver_buttons = buttons(self.users['driver'])
        self.assertNotIn('action_start_route', driver_buttons)
        self.assertNotIn('action_view_route_map', driver_buttons)
        dispatcher_buttons = buttons(self.users['dispatcher'])
        self.assertIn('action_start_route', dispatcher_buttons)
        self.assertIn('action_view_route_map', dispatcher_buttons)

    # V-20 ---------------------------------------------------------------
    def test_report_action_default_filter_exists(self):
        action = self.env.ref('wm_collection.action_wm_collection_report_analysis')
        search_arch = self.env.ref('wm_collection.view_wm_collection_report_search').arch
        self.assertIn("search_default_completed", action.context)
        self.assertIn('name="completed"', search_arch)

    # V-10 ---------------------------------------------------------------
    def test_collection_order_report_renders_signature(self):
        partner = self.env['res.partner'].create({'name': 'ACL medium partner'})
        signature = self.env['wm.signature'].create({'name': 'Sig', 'signature': _PNG})
        order = self.env['wm.collection.order'].create({
            'partner_id': partner.id,
            'signature_id': signature.id,
        })
        html, _type = self.env['ir.actions.report']._render_qweb_html(
            'wm_collection.report_collection_order_document', [order.id])
        self.assertIn(b'data:image/png;base64', html)
