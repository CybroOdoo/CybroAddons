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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestAiImageGenerationLog(TransactionCase):
    """Test cases for ai.image.generation.log audit trail model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.template'].create({
            'name': 'Smart Watch Pro',
            'list_price': 199.0,
        })
        cls.sample_image_b64 = (
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk'
            '+A8AAQUBAScY42YAAAAASUVORK5CYII='
        )

    def test_log_defaults(self):
        """Test default values when creating an AI image generation log."""
        log = self.env['ai.image.generation.log'].create({
            'product_id': self.product.id,
        })

        self.assertEqual(log.product_id, self.product)
        self.assertEqual(log.user_id, self.env.user)
        self.assertEqual(log.status, 'success')
        self.assertFalse(log.image_applied)
        self.assertFalse(log.enhance_mode)
        self.assertEqual(log.display_name, self.product.name)

    def test_log_create_full(self):
        """Test creating a log record with all fields populated."""
        log = self.env['ai.image.generation.log'].create({
            'product_id': self.product.id,
            'prompt': 'A high-end smartwatch on a sleek reflective surface',
            'ai_provider': 'openai',
            'image_style': 'professional',
            'status': 'success',
            'image_generated': self.sample_image_b64,
            'image_applied': True,
            'enhance_mode': True,
            'error_message': False,
            'num_variants_requested': 3,
            'image_size': '1024x1024',
        })

        self.assertEqual(log.product_id, self.product)
        self.assertEqual(log.prompt, 'A high-end smartwatch on a sleek reflective surface')
        self.assertEqual(log.ai_provider, 'openai')
        self.assertEqual(log.image_style, 'professional')
        self.assertEqual(log.status, 'success')
        self.assertTrue(log.image_applied)
        self.assertTrue(log.enhance_mode)
        self.assertEqual(log.num_variants_requested, 3)
        self.assertEqual(log.image_size, '1024x1024')
        self.assertTrue(bool(log.image_generated))

    def test_log_failed_status(self):
        """Test creating a log record with failed status and error message."""
        log = self.env['ai.image.generation.log'].create({
            'product_id': self.product.id,
            'ai_provider': 'stability',
            'image_style': 'minimal',
            'status': 'failed',
            'error_message': 'Stability AI API quota exceeded.',
            'num_variants_requested': 1,
        })

        self.assertEqual(log.status, 'failed')
        self.assertEqual(log.error_message, 'Stability AI API quota exceeded.')
        self.assertFalse(log.image_applied)

    def test_log_pending_approval_status(self):
        """Test creating a log record with pending_approval status."""
        log = self.env['ai.image.generation.log'].create({
            'product_id': self.product.id,
            'ai_provider': 'gemini',
            'status': 'pending_approval',
        })

        self.assertEqual(log.status, 'pending_approval')

    def test_log_ordering_by_create_date_desc(self):
        """Test log records are ordered descending by create_date."""
        log1 = self.env['ai.image.generation.log'].create({
            'product_id': self.product.id,
            'prompt': 'Prompt 1',
        })
        log2 = self.env['ai.image.generation.log'].create({
            'product_id': self.product.id,
            'prompt': 'Prompt 2',
        })
        self.env.cr.execute(
            "UPDATE ai_image_generation_log SET create_date = %s WHERE id = %s",
            [fields.Datetime.subtract(fields.Datetime.now(), hours=1), log1.id]
        )
        self.env['ai.image.generation.log'].invalidate_model(['create_date'])

        logs = self.env['ai.image.generation.log'].search([
            ('id', 'in', [log1.id, log2.id])
        ])
        self.assertEqual(logs[0].id, log2.id)
        self.assertEqual(logs[1].id, log1.id)

    def test_log_ondelete_product_sets_null(self):
        """Test product deletion sets product_id to null instead of cascading."""
        temp_product = self.env['product.template'].create({
            'name': 'Temporary Product to Delete',
        })
        log = self.env['ai.image.generation.log'].create({
            'product_id': temp_product.id,
            'prompt': 'Temporary prompt',
        })

        temp_product.unlink()
        self.assertTrue(log.exists())
        self.assertFalse(log.product_id)

    def test_log_approve_and_reject_workflow(self):
        """Test manager approval applies image and rejection updates status."""
        manager_group = self.env.ref('smart_product_image_generator.group_ai_image_manager')
        user_group = self.env.ref('smart_product_image_generator.group_ai_image_user')
        regular_user = self.env['res.users'].create({
            'name': 'AI Image User',
            'login': 'ai_image_user_test',
            'group_ids': [(6, 0, [user_group.id])],
        })
        manager_user = self.env['res.users'].create({
            'name': 'AI Image Manager',
            'login': 'ai_image_manager_test',
            'group_ids': [(6, 0, [manager_group.id])],
        })

        product = self.env['product.template'].create({
            'name': 'Approval Test Product',
            'list_price': 100.0,
        })
        log_pending = self.env['ai.image.generation.log'].create({
            'product_id': product.id,
            'ai_provider': 'gemini',
            'image_style': 'professional',
            'status': 'pending_approval',
            'image_generated': self.sample_image_b64,
            'image_size': '1024x1024',
        })

        # Regular user cannot approve or reject
        with self.assertRaises(AccessError):
            log_pending.with_user(regular_user)._check_manager_access()
        with self.assertRaises(AccessError):
            log_pending.with_user(regular_user).action_approve()
        with self.assertRaises(AccessError):
            log_pending.with_user(regular_user).action_reject()

        # Manager and sudo pass _check_manager_access
        log_pending.with_user(manager_user)._check_manager_access()
        log_pending.sudo()._check_manager_access()

        # Missing image raises UserError
        log_no_image = self.env['ai.image.generation.log'].create({
            'product_id': product.id,
            'status': 'pending_approval',
        })
        with self.assertRaises(UserError):
            log_no_image.with_user(manager_user).action_approve()

        # Missing product raises UserError
        log_no_product = self.env['ai.image.generation.log'].create({
            'product_id': False,
            'status': 'pending_approval',
            'image_generated': self.sample_image_b64,
        })
        with self.assertRaises(UserError):
            log_no_product.with_user(manager_user).action_approve()

        # Manager approves pending log
        log_pending.with_user(manager_user).action_approve()
        self.assertEqual(log_pending.status, 'success')
        self.assertTrue(log_pending.image_applied)
        self.assertEqual(log_pending.approved_by_id, manager_user)
        self.assertTrue(bool(log_pending.approved_date))
        self.assertTrue(bool(product.image_1920))
        self.assertEqual(product.ai_generation_count, 1)

        # Approving/rejecting non-pending log raises UserError
        with self.assertRaises(UserError):
            log_pending.with_user(manager_user).action_approve()
        with self.assertRaises(UserError):
            log_pending.with_user(manager_user).action_reject()

        # Manager rejects another pending log
        log_reject = self.env['ai.image.generation.log'].create({
            'product_id': product.id,
            'status': 'pending_approval',
            'image_generated': self.sample_image_b64,
        })
        log_reject.with_user(manager_user).action_reject()
        self.assertEqual(log_reject.status, 'rejected')
        self.assertFalse(log_reject.image_applied)
        self.assertEqual(log_reject.approved_by_id, manager_user)

    def test_log_and_wizard_acl_permissions(self):
        """Test ir.access.csv permissions for base, user, and manager groups."""
        base_user = self.env['res.users'].create({
            'name': 'Plain Internal User',
            'login': 'plain_internal_user_test',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        user_group = self.env.ref('smart_product_image_generator.group_ai_image_user')
        ai_user = self.env['res.users'].create({
            'name': 'AI User ACL',
            'login': 'ai_user_acl_test',
            'group_ids': [(6, 0, [user_group.id])],
        })
        manager_group = self.env.ref('smart_product_image_generator.group_ai_image_manager')
        ai_manager = self.env['res.users'].create({
            'name': 'AI Manager ACL',
            'login': 'ai_manager_acl_test',
            'group_ids': [(6, 0, [manager_group.id])],
        })

        # Plain base.group_user has no access to wizard or log
        with self.assertRaises(AccessError):
            self.env['ai.image.generation.log'].with_user(base_user).search([])
        with self.assertRaises(AccessError):
            self.env['smart.product.image.generator'].with_user(base_user).create({
                'product_id': self.product.id,
            })

        # group_ai_image_user can create wizard/lines and create/read logs, not write/unlink logs
        wizard = self.env['smart.product.image.generator'].with_user(ai_user).create({
            'product_id': self.product.id,
        })
        self.assertTrue(wizard.exists())
        log_as_user = self.env['ai.image.generation.log'].with_user(ai_user).create({
            'product_id': self.product.id,
            'status': 'success',
        })
        self.assertTrue(log_as_user.exists())
        with self.assertRaises(AccessError):
            log_as_user.with_user(ai_user).write({'error_message': 'tamper'})
        with self.assertRaises(AccessError):
            log_as_user.with_user(ai_user).unlink()

        # group_ai_image_manager has full CRUD on logs
        log_as_user.with_user(ai_manager).write({'error_message': 'manager note'})
        log_as_user.with_user(ai_manager).unlink()
        self.assertFalse(log_as_user.exists())
