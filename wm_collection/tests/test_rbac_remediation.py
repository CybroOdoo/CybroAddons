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
import logging

from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'wm_security')
class TestRbacRemediation(TransactionCase):
    """Unit tests verifying role-based security access rights across collection models."""

    _user_count = 0

    def _create_user_with_group(self, group_xml_id):
        """
        Helper: creates a test res.users with only the specified group
        (plus base.group_user, implied).
        """
        TestRbacRemediation._user_count += 1
        cnt = TestRbacRemediation._user_count
        group_rec = self.env.ref(group_xml_id)
        user = self.env['res.users'].create({
            'name': f'Test User {group_xml_id} {cnt}',
            'login': f'test_{group_xml_id.replace(".", "_")}_{cnt}@example.com',
            'email': f'test_{group_xml_id.replace(".", "_")}_{cnt}@example.com',
        })
        group_rec.write({'user_ids': [(4, user.id)]})
        return user

    def test_rbac01_finance_cannot_write_collection_order(self):
        """
        Finance role has read access but NOT write access to collection orders.
        """
        finance_user = self._create_user_with_group('wm_base.group_wm_finance')
        partner = self.env['res.partner'].create({'name': 'Test Partner RBAC1'})
        order = self.env['wm.collection.order'].sudo().create({
            'name': 'COL-RBAC1-01',
            'partner_id': partner.id,
        })
        with self.assertRaises(AccessError):
            order.with_user(finance_user).write({'notes': 'Unauthorized write'})
        _logger.info('PASS: test_rbac01_finance_cannot_write_collection_order')

    def test_rbac01_recycler_read_only(self):
        """
        Recycling Specialist can read but not create collection orders.
        """
        recycler_user = self._create_user_with_group('wm_base.group_wm_recycler')
        partner = self.env['res.partner'].create({'name': 'Test Partner RBAC1 Recycler'})
        order = self.env['wm.collection.order'].sudo().create({
            'name': 'COL-RBAC1-02',
            'partner_id': partner.id,
        })
        # Can read
        orders = self.env['wm.collection.order'].with_user(recycler_user).search([('id', '=', order.id)])
        self.assertIn(order, orders)
        # Cannot create
        with self.assertRaises(AccessError):
            self.env['wm.collection.order'].with_user(recycler_user).create({
                'name': 'COL-RBAC1-03',
                'partner_id': partner.id,
            })
        _logger.info('PASS: test_rbac01_recycler_read_only')

    def test_rbac02_sort_toggle_actually_controls_access(self):
        """
        Switching the 'Sort Based On' Settings option toggles the implied
        sort groups on base.group_user (and the inventory operator group),
        so a plain internal user gains/loses group_sort_by_material.
        """
        base_user_group = self.env.ref('base.group_user')
        operator_group = self.env.ref('wm_base.group_wm_inventory_operator')
        sort_material_group = self.env.ref('wm_collection.group_sort_by_material')
        sort_category_group = self.env.ref('wm_collection.group_sort_by_category')
        plain_user = self.env['res.users'].create({
            'name': 'Plain User RBAC2',
            'login': 'plain_user_rbac2@example.com',
            'email': 'plain_user_rbac2@example.com',
        })

        def apply_sort_mode(mode):
            # Mirror the form onchange: the mode drives both implied-group toggles.
            self.env['res.config.settings'].create({
                'wm_sort_based_on': mode,
                'group_sort_by_material': mode == 'material',
                'group_sort_by_category': mode == 'category_and_material',
            }).execute()
            self.env.invalidate_all()

        apply_sort_mode('category_and_material')
        self.assertNotIn(sort_material_group, base_user_group.implied_ids)
        self.assertIn(sort_category_group, base_user_group.implied_ids)
        self.assertNotIn(sort_material_group, operator_group.implied_ids)
        self.assertFalse(plain_user.has_group('wm_collection.group_sort_by_material'))
        self.assertTrue(plain_user.has_group('wm_collection.group_sort_by_category'))

        apply_sort_mode('material')
        self.assertIn(sort_material_group, base_user_group.implied_ids)
        self.assertNotIn(sort_category_group, base_user_group.implied_ids)
        self.assertIn(sort_material_group, operator_group.implied_ids)
        self.assertTrue(plain_user.has_group('wm_collection.group_sort_by_material'))
        self.assertFalse(plain_user.has_group('wm_collection.group_sort_by_category'))
        _logger.info('PASS: test_rbac02_sort_toggle_actually_controls_access')

    def test_rbac03_no_duplicate_acl_rows(self):
        """
        Only one ir.model.access row exists for (wm.waste.category.sort.config,
        base.group_user).
        """
        access_recs = self.env['ir.model.access'].search([
            ('model_id.model', '=', 'wm.waste.category.sort.config'),
            ('group_id', '=', self.env.ref('base.group_user').id),
        ])
        self.assertEqual(len(access_recs), 1)
        self.assertFalse(access_recs.perm_write)
        _logger.info('PASS: test_rbac03_no_duplicate_acl_rows')

    def test_rbac04_sort_wizard_requires_inventory_operator(self):
        """
        A plain internal user (no waste management group) cannot access the
        sort wizard model.
        """
        plain_user = self.env['res.users'].create({
            'name': 'Plain User RBAC4',
            'login': 'plain_user_rbac4@example.com',
            'email': 'plain_user_rbac4@example.com',
        })
        with self.assertRaises(AccessError):
            self.env['waste.batch.sort.wizard'].with_user(plain_user).create({})
        _logger.info('PASS: test_rbac04_sort_wizard_requires_inventory_operator')

    def test_rbac06_driver_loses_access_after_reassignment(self):
        """
        Driver A creates an unassigned order (sees it), order gets assigned to
        Driver B, Driver A can no longer see it.
        """
        driver_a = self._create_user_with_group('wm_base.group_wm_driver')
        driver_b = self._create_user_with_group('wm_base.group_wm_driver')
        partner = self.env['res.partner'].create({'name': 'Partner RBAC6'})

        # Driver A creates unassigned order
        order = self.env['wm.collection.order'].with_user(driver_a).create({
            'name': 'COL-RBAC6-01',
            'partner_id': partner.id,
        })
        self.assertIn(order, self.env['wm.collection.order'].with_user(driver_a).search([('id', '=', order.id)]))

        # Assign to Driver B
        order.sudo().write({'driver_id': driver_b.partner_id.id})

        # Driver A can no longer see it; Driver B can see it
        self.assertNotIn(order, self.env['wm.collection.order'].with_user(driver_a).search([('id', '=', order.id)]))
        self.assertIn(order, self.env['wm.collection.order'].with_user(driver_b).search([('id', '=', order.id)]))
        _logger.info('PASS: test_rbac06_driver_loses_access_after_reassignment')

    def test_rbac09_checklist_requires_dispatcher(self):
        """
        A plain internal user can read but not write vehicle maintenance
        checklists.
        """
        plain_user = self.env['res.users'].create({
            'name': 'Plain User RBAC9',
            'login': 'plain_user_rbac9@example.com',
            'email': 'plain_user_rbac9@example.com',
        })
        brand = self.env['fleet.vehicle.model.brand'].sudo().create({'name': 'Brand RBAC9'})
        model_id = self.env['fleet.vehicle.model'].sudo().create({
            'name': 'Model RBAC9',
            'brand_id': brand.id,
        })
        vehicle = self.env['fleet.vehicle'].sudo().create({
            'license_plate': 'TEST-RBAC9',
            'model_id': model_id.id,
        })
        checklist = self.env['wm.vehicle.maintenance.checklist'].sudo().create({
            'name': 'Checklist RBAC9',
            'vehicle_id': vehicle.id,
            'checklist_type': 'pre_trip',
        })
        # Plain user can read
        checklists = self.env['wm.vehicle.maintenance.checklist'].with_user(plain_user).search([('id', '=', checklist.id)])
        self.assertIn(checklist, checklists)
        # Plain user cannot write
        with self.assertRaises(AccessError):
            checklist.with_user(plain_user).write({'notes': 'Unauthorized edit'})
        _logger.info('PASS: test_rbac09_checklist_requires_dispatcher')

    def test_rbac11_driver_reads_only_own_route_lines(self):
        """
        A driver can read the stops of routes assigned to them, but not the
        stops of another driver's route.
        """
        driver_a = self._create_user_with_group('wm_base.group_wm_driver')
        driver_b = self._create_user_with_group('wm_base.group_wm_driver')
        point = self.env['wm.collection.point'].create({'name': 'Point RBAC11'})
        route_a = self.env['wm.route'].create({
            'name': 'Route RBAC11 A',
            'driver_id': driver_a.partner_id.id,
            'line_ids': [(0, 0, {'collection_point_id': point.id, 'sequence': 10})],
        })
        route_b = self.env['wm.route'].create({
            'name': 'Route RBAC11 B',
            'driver_id': driver_b.partner_id.id,
            'line_ids': [(0, 0, {'collection_point_id': point.id, 'sequence': 10})],
        })
        visible = self.env['wm.route.line'].with_user(driver_a).search([
            ('id', 'in', (route_a.line_ids | route_b.line_ids).ids),
        ])
        self.assertEqual(visible, route_a.line_ids)
        _logger.info('PASS: test_rbac11_driver_reads_only_own_route_lines')
