# -*- coding: utf-8 -*-
from odoo.tests import common
from odoo.exceptions import ValidationError

class TestCustomerSupplierApproval(common.TransactionCase):

    def setUp(self):
        super(TestCustomerSupplierApproval, self).setUp()
        
        self.partner_model = self.env['res.partner']
        self.sale_model = self.env['sale.order']
        self.purchase_model = self.env['purchase.order']
        self.picking_model = self.env['stock.picking']
        
        # Create users
        self.user_base = self.env['res.users'].create({
            'name': 'Base User',
            'login': 'base_user_test',
            'email': 'base_user_test@example.com',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]
        })
        
        self.user_validator = self.env['res.users'].create({
            'name': 'Validator User',
            'login': 'validator_test',
            'email': 'validator_test@example.com',
            'group_ids': [(6, 0, [
                self.env.ref('base.group_user').id, 
                self.env.ref('customer_supplier_approval.customer_supplier_approval_group_validation').id
            ])]
        })
        
        self.user_approver = self.env['res.users'].create({
            'name': 'Approver User',
            'login': 'approver_test',
            'email': 'approver_test@example.com',
            'group_ids': [(6, 0, [
                self.env.ref('base.group_user').id, 
                self.env.ref('customer_supplier_approval.customer_supplier_approval_group_approval').id
            ])]
        })
        
        # Create a test partner
        self.partner = self.partner_model.create({
            'name': 'Test Partner CS',
            'customer_supplier': 'CS-001',
        })

    def test_01_partner_action_validate(self):
        """Test action_validate method"""
        self.assertEqual(self.partner.state, 'draft')
        self.partner.with_user(self.user_validator).action_validate()
        self.assertEqual(self.partner.state, 'validated')
        self.assertTrue(self.partner.is_hide_button_validate)

    def test_02_partner_action_approve(self):
        """Test action_approve method"""
        self.partner.with_user(self.user_validator).action_validate() # Setup state correctly
        self.partner.with_user(self.user_approver).action_approve()
        self.assertEqual(self.partner.state, 'approved')
        self.assertTrue(self.partner.is_hide_button)

    def test_03_partner_write_validation_error_draft_to_validated(self):
        """Test write method raises ValidationError for missing validation group"""
        # Base user tries to change state to validated from draft
        with self.assertRaises(ValidationError):
            self.partner.with_user(self.user_base).write({'state': 'validated'})
            
    def test_04_partner_write_validation_error_validated_to_approved(self):
        """Test write method raises ValidationError for missing approval group"""
        self.partner.with_user(self.user_validator).action_validate() # Setup state correctly
        # Base user tries to change state to approved
        with self.assertRaises(ValidationError):
            self.partner.with_user(self.user_base).write({'state': 'approved'})

        # Validator tries to change state to approved (but lacks approve group)
        with self.assertRaises(ValidationError):
            self.partner.with_user(self.user_validator).write({'state': 'approved'})
            
    def test_05_partner_write_success(self):
        """Test successful state changes with correct groups"""
        self.partner.with_user(self.user_validator).write({'state': 'validated'})
        self.assertEqual(self.partner.state, 'validated')
        
        self.partner.with_user(self.user_approver).write({'state': 'approved'})
        self.assertEqual(self.partner.state, 'approved')

    def test_07_sale_order_partner_domain(self):
        """Test if the partner_id field has the correct domain in sale.order"""
        domain = self.sale_model._fields['partner_id'].domain
        self.assertTrue(domain == "[('state', '=', 'approved')]" or ('state', '=', 'approved') in domain)

    def test_08_purchase_order_partner_domain(self):
        """Test if the partner_id field has the correct domain in purchase.order"""
        domain = self.purchase_model._fields['partner_id'].domain
        self.assertTrue(domain == "[('state', '=', 'approved')]" or ('state', '=', 'approved') in domain)

    def test_09_stock_picking_partner_domain(self):
        """Test if the partner_id field has the correct domain in stock.picking"""
        domain = self.picking_model._fields['partner_id'].domain
        self.assertTrue(domain == "[('state', '=', 'approved')]" or ('state', '=', 'approved') in domain)
