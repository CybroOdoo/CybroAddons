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
#############################################################################
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'pos_update_realtime')
class TestPosUpdateRealtime(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test Realtime POS Config',
        })
        cls.pos_session = cls.env['pos.session'].create({
            'config_id': cls.pos_config.id,
            'user_id': cls.env.uid,
            'state': 'opened',
        })
        cls.category = cls.env['product.category'].create({
            'name': 'Realtime Test Category',
        })

    def test_01_template_create_single_notification(self):
        """Creating a product template sends exactly one notification (no duplicates)."""
        with patch.object(
            type(self.env['product.template']),
            '_notify_pos_product_change',
            autospec=True,
        ) as mock_notify:
            template = self.env['product.template'].create({
                'name': 'Realtime Pizza',
                'list_price': 15.0,
                'available_in_pos': True,
                'categ_id': self.category.id,
            })
            self.assertEqual(
                mock_notify.call_count,
                1,
                "Notification must be sent exactly once on template create, not duplicated by variant create",
            )
            variant = template.product_variant_ids[0]
            call_args = mock_notify.call_args[0]
            # mock signature: (self, product, pos_sessions)
            self.assertEqual(call_args[1].id, variant.id)

    def test_02_template_create_not_available_in_pos(self):
        """Creating a product not available in POS should not notify POS sessions."""
        with patch.object(
            type(self.env['product.template']),
            '_notify_pos_product_change',
            autospec=True,
        ) as mock_notify:
            self.env['product.template'].create({
                'name': 'Non POS Item',
                'list_price': 20.0,
                'available_in_pos': False,
            })
            self.assertEqual(
                mock_notify.call_count,
                0,
                "No notification should be sent for products not available in POS",
            )

    def test_03_template_write_pos_relevant_fields(self):
        """Writing to POS-relevant fields triggers notification."""
        template = self.env['product.template'].create({
            'name': 'Realtime Burger',
            'list_price': 10.0,
            'available_in_pos': True,
        })
        with patch.object(
            type(self.env['product.template']),
            '_notify_pos_product_change',
            autospec=True,
        ) as mock_notify:
            template.write({'list_price': 12.5})
            self.assertEqual(
                mock_notify.call_count,
                1,
                "Writing to list_price must trigger a notification",
            )

    def test_04_template_write_unrelated_fields(self):
        """Writing to unrelated fields does not search POS sessions or notify."""
        template = self.env['product.template'].create({
            'name': 'Realtime Salad',
            'list_price': 8.0,
            'available_in_pos': True,
        })
        with patch.object(
            type(self.env['product.template']),
            '_notify_pos_product_change',
            autospec=True,
        ) as mock_notify:
            template.write({'description_sale': 'Fresh garden salad'})
            self.assertEqual(
                mock_notify.call_count,
                0,
                "Writing to non-POS fields must not trigger any notification",
            )

    def test_05_variant_write_relevant_and_unrelated(self):
        """Writing to variant directly behaves correctly for relevant vs non-relevant fields."""
        template = self.env['product.template'].create({
            'name': 'Realtime Soda',
            'list_price': 3.0,
            'available_in_pos': True,
        })
        variant = template.product_variant_ids[0]

        with patch.object(
            type(self.env['product.template']),
            '_notify_pos_product_change',
            autospec=True,
        ) as mock_notify:
            variant.write({'barcode': '998877665544'})
            self.assertEqual(
                mock_notify.call_count,
                1,
                "Updating barcode on variant must trigger a notification",
            )

            mock_notify.reset_mock()
            variant.write({'weight': 0.35})
            self.assertEqual(
                mock_notify.call_count,
                0,
                "Updating weight on variant must not trigger a notification",
            )

    def test_06_notify_payload_and_bus_mixin(self):
        """Payload format is correct and delegates to pos.config._notify via pos.bus.mixin."""
        template = self.env['product.template'].create({
            'name': 'Realtime Juice',
            'list_price': 5.5,
            'standard_price': 2.0,
            'available_in_pos': True,
            'categ_id': self.category.id,
            'barcode': '112233445566',
            'default_code': 'JUICE-01',
        })
        variant = template.product_variant_ids[0]

        with patch.object(
            type(self.pos_config),
            '_notify',
            autospec=True,
        ) as mock_config_notify:
            template._notify_pos_product_change(variant, self.pos_session)

            self.assertEqual(
                mock_config_notify.call_count,
                1,
                "pos.config._notify must be called once for the active config",
            )
            event_name = mock_config_notify.call_args[0][1]
            payload = mock_config_notify.call_args[0][2]

            self.assertEqual(event_name, "PRODUCT_UPDATE")
            self.assertEqual(payload['product_id'], variant.id)
            self.assertEqual(payload['product_tmpl_id'], template.id)
            self.assertEqual(payload['name'], variant.display_name)
            self.assertEqual(payload['tmpl_name'], template.name)
            self.assertEqual(payload['list_price'], 5.5)
            self.assertEqual(payload['standard_price'], 2.0)
            self.assertEqual(payload['barcode'], '112233445566')
            self.assertEqual(payload['default_code'], 'JUICE-01')
            self.assertEqual(payload['categ_id'], self.category.id)
            self.assertTrue(payload['active'])
            self.assertTrue(payload['tmpl_active'])
            self.assertTrue(payload['available_in_pos'])
            self.assertIsInstance(payload['categ_id'], int)
            self.assertIsInstance(payload['taxes_id'], list)

    def test_07_no_open_session_no_notification(self):
        """When no POS session is opened, no notification is sent."""
        self.pos_session.write({'state': 'closed'})
        try:
            template = self.env['product.template'].create({
                'name': 'Realtime Coffee',
                'list_price': 4.0,
                'available_in_pos': True,
            })
            with patch.object(
                type(self.env['product.template']),
                '_notify_pos_product_change',
                autospec=True,
            ) as mock_notify:
                template.write({'list_price': 4.5})
                self.assertEqual(
                    mock_notify.call_count,
                    0,
                    "No notification should be sent if there are no open POS sessions",
                )
        finally:
            self.pos_session.write({'state': 'opened'})

    def test_08_non_pos_user_save_product(self):
        """An inventory or sales user without POS rights can write list_price, name, barcode without AccessError."""
        product_manager_group = self.env.ref('product.group_product_manager')
        sales_group = self.env.ref('sales_team.group_sale_salesman', raise_if_not_found=False)
        groups = [self.env.ref('base.group_user').id, product_manager_group.id]
        if sales_group:
            groups.append(sales_group.id)
        non_pos_user = self.env['res.users'].create({
            'name': 'Non POS Product Manager',
            'login': 'non_pos_user',
            'email': 'nonpos@example.com',
            'group_ids': [(6, 0, groups)],
        })

        pos_user_group = self.env.ref('point_of_sale.group_pos_user', raise_if_not_found=False)
        if pos_user_group:
            self.assertNotIn(pos_user_group, non_pos_user.all_group_ids)

        template = self.env['product.template'].create({
            'name': 'Non POS Editable Product',
            'list_price': 10.0,
            'available_in_pos': True,
        })
        variant = template.product_variant_ids[0]

        with patch.object(
            type(self.env['product.template']),
            '_notify_pos_product_change',
            autospec=True,
        ) as mock_notify:
            template.with_user(non_pos_user).write({
                'name': 'Updated by Sales User',
                'list_price': 14.0,
            })
            self.assertEqual(
                mock_notify.call_count,
                1,
                "Writing list_price/name as non-POS user must succeed and notify without AccessError",
            )

            mock_notify.reset_mock()
            variant.with_user(non_pos_user).write({
                'barcode': '123456789012',
            })
            self.assertEqual(
                mock_notify.call_count,
                1,
                "Writing barcode as non-POS user must succeed and notify without AccessError",
            )

    def test_09_archive_and_pos_unavailability_notifications(self):
        """Archived products or products set to available_in_pos=False send appropriate flags to POS."""
        template = self.env['product.template'].create({
            'name': 'Archivable Product',
            'list_price': 10.0,
            'available_in_pos': True,
        })
        variant = template.product_variant_ids[0]

        with patch.object(
            type(self.pos_config),
            '_notify',
            autospec=True,
        ) as mock_config_notify:
            template.write({'active': False})
            self.assertTrue(mock_config_notify.called)
            payload = mock_config_notify.call_args[0][2]
            self.assertFalse(payload['active'])
            self.assertFalse(payload['tmpl_active'])

        template.write({'active': True})

        with patch.object(
            type(self.pos_config),
            '_notify',
            autospec=True,
        ) as mock_config_notify:
            template.write({'available_in_pos': False})
            self.assertTrue(mock_config_notify.called)
            payload = mock_config_notify.call_args[0][2]
            self.assertFalse(payload['available_in_pos'])

        template.write({'available_in_pos': True})

        with patch.object(
            type(self.pos_config),
            '_notify',
            autospec=True,
        ) as mock_config_notify:
            variant.write({'active': False})
            self.assertTrue(mock_config_notify.called)
            payload = mock_config_notify.call_args[0][2]
            self.assertFalse(payload['active'])

    def test_10_variant_display_name_vs_template_name(self):
        """Notification payload separates tmpl_name from variant display_name."""
        template = self.env['product.template'].create({
            'name': 'Master Template Name',
            'list_price': 25.0,
            'available_in_pos': True,
        })
        variant = template.product_variant_ids[0]
        variant.write({'default_code': 'CODE123'})

        with patch.object(
            type(self.pos_config),
            '_notify',
            autospec=True,
        ) as mock_config_notify:
            template._notify_pos_product_change(variant, self.pos_session)
            payload = mock_config_notify.call_args[0][2]
            self.assertEqual(payload['tmpl_name'], 'Master Template Name')
            self.assertEqual(payload['name'], variant.display_name)
            self.assertIn('[CODE123]', payload['name'])
            self.assertNotIn('[CODE123]', payload['tmpl_name'])

