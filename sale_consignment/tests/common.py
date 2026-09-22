# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from datetime import date, timedelta


class TestConsignmentCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Company
        cls.company = cls.env.company

        # Config parameters settings
        cls.env['ir.config_parameter'].set_param('sale_consignment.consignment_customer_only', 'True')
        cls.env['ir.config_parameter'].set_param('sale_consignment.consignment_product_only', 'True')

        # Partner
        cls.partner_consignment = cls.env['res.partner'].create({
            'name': 'Consignment Partner',
            'is_consignment': True,
        })
        cls.partner_normal = cls.env['res.partner'].create({
            'name': 'Normal Partner',
            'is_consignment': False,
        })

        # Product
        cls.product_consignment = cls.env['product.product'].create({
            'name': 'Consignment Product',
            'is_consignment': True,
            'list_price': 100.0,
            'type': 'consu',
        })
        cls.product_normal = cls.env['product.product'].create({
            'name': 'Normal Product',
            'is_consignment': False,
            'list_price': 50.0,
            'type': 'consu',
        })

        # Warehouse and Locations
        cls.warehouse = cls.env['stock.warehouse'].search([('company_id', '=', cls.company.id)], limit=1)
        cls.location_src = cls.warehouse.lot_stock_id

        # Parent location for transit location
        parent_loc = cls.env.ref('stock.stock_location_locations', raise_if_not_found=False)
        cls.location_dest = cls.env['stock.location'].create({
            'name': 'Consignment Transit Location',
            'usage': 'transit',
            'company_id': cls.company.id,
            'location_id': parent_loc.id if parent_loc else False,
        })

        # Set location_dest_id configuration parameter
        cls.env['ir.config_parameter'].set_param('sale_consignment.location_dest_id', str(cls.location_dest.id))

        # Create picking type to match internal transit operation
        cls.picking_type = cls.env['stock.picking.type'].create({
            'name': 'Consignment Internal Transfer',
            'code': 'internal',
            'warehouse_id': cls.warehouse.id,
            'company_id': cls.company.id,
            'default_location_src_id': cls.location_src.id,
            'default_location_dest_id': cls.location_dest.id,
            'sequence_code': 'CINT',
        })
