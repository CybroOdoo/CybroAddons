# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

class TestMondayModels(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestMondayModels, cls).setUpClass()
        cls.board = cls.env['monday.board'].create({
            'name': 'Test Board',
            'board_reference': 'B001',
            'owner': 'Test Owner',
            'description': 'A board for testing'
        })
        cls.group = cls.env['monday.group'].create({
            'name': 'Test Group',
            'group': 'G001',
            'board_id': cls.board.id
        })
        cls.item = cls.env['monday.item'].create({
            'name': 'Test Item',
            'board_id': cls.board.id,
            'column_value_ids': [(0, 0, {
                'title': 'Test Column',
                'text': 'Test Text'
            })]
        })

    def test_board_creation(self):
        """Test board creation and fields"""
        self.assertEqual(self.board.name, 'Test Board')
        self.assertEqual(self.board.board_reference, 'B001')

    def test_group_creation(self):
        """Test group creation and relationship to board"""
        self.assertEqual(self.group.name, 'Test Group')
        self.assertEqual(self.group.board_id, self.board)
        self.assertIn(self.group, self.board.group_ids)

    def test_item_creation(self):
        """Test item creation and relationship to board and columns"""
        self.assertEqual(self.item.name, 'Test Item')
        self.assertEqual(self.item.board_id, self.board)
        self.assertIn(self.item, self.board.item_ids)
        self.assertEqual(len(self.item.column_value_ids), 1)
        self.assertEqual(self.item.column_value_ids[0].title, 'Test Column')
        self.assertEqual(self.item.column_value_ids[0].text, 'Test Text')

    def test_partner_monday_reference(self):
        """Test partner monday reference field"""
        partner = self.env['res.partner'].create({
            'name': 'Monday Partner',
            'monday_reference': True
        })
        self.assertTrue(partner.monday_reference)

    def test_user_monday_reference(self):
        """Test user monday reference field"""
        user = self.env['res.users'].create({
            'name': 'Monday User',
            'login': 'mondayuser',
            'monday_reference': 'U001'
        })
        self.assertEqual(user.monday_reference, 'U001')
