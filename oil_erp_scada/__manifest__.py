# -*- coding: utf-8 -*-
#############################################################################
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
{
    'name': 'Oil & Gas SCADA Integration',
    'version': '19.0.1.0.0',
    'category': 'Oil ERP/Integration',
    'summary': 'Real-time Ignition SCADA ↔ Odoo Oil ERP bidirectional API integration',
    'description': """SCADA Integration module for the Oil & Gas ERP system.""",
    'author': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'oil_erp_base',
        'oil_erp_equipment',
        'oil_erp_hse',
        'oil_erp_pipeline',
        'oil_erp_reservoir',
        'oil_erp_royalty',
        'maintenance',
        'mrp',
        'mail',
        'sms',
        'stock',
        'oil_erp_project',
    ],
    'data': [
        'views/scada_menus.xml',
        'security/scada_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'views/scada_tag_views.xml',
        'views/scada_reading_views.xml',
        'views/scada_threshold_views.xml',
        'views/maintenance_equipment_views.xml',
        'views/oil_tank_views.xml',
        'views/oil_reservoir_views_scada.xml',
        'views/delivery_carrier_views_scada.xml',
        'views/stock_location_views.xml',
        'views/oil_daily_production_views.xml',
        'views/production_wizard_views.xml',
        'views/mrp_workcenter_views.xml',
        'views/res_config_settings_views.xml',
        'views/product_template_views.xml',
        'views/scada_reading_product_views.xml',
        'wizard/scada_reading_wizard_views.xml',
    ],
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
    'post_init_hook': 'post_init_hook',
}
