# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Dhanya B(<https://www.cybrosys.com>)
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
import xml.etree.ElementTree as xee
from ast import literal_eval
from odoo import models, api, fields


class ResConfigSettings(models.TransientModel):
    """
    Settings for handling duplicate records in Odoo.
    """
    _inherit = 'res.config.settings'

    company_id = fields.Many2one('res.company',
                                 'Company',
                                 help='Name of the company.')
    opportunity_duplicates = fields.Boolean(
        'Consider only Opportunity as Duplicates', help='Enable this'
                                                        'boolean for to display'
                                                        'the duplicates in '
                                                        'opportunities.')
    leads_duplicates = fields.Boolean('Consider only Opportunity '
                                      'as Leads', help='Enable this'
                                                       'boolean for to display'
                                                       'the duplicates in '
                                                       'leads.')
    duplicate_count_tree_kanban = fields.Boolean(string='Duplicates Count',
                                                 help='To show the duplicates'
                                                      'count in tree and kanban'
                                                      ' view.')
    duplicate_count_form = fields.Boolean(string='Duplicates Count in Form',
                                          help='To show the duplicates'
                                               'count in form'
                                               ' view.')

    def set_domain_crm(self):
        """Return the domain for CRM fields."""
        crm_view_id = self.env.ref('crm.crm_lead_view_form')
        view_arch = str(crm_view_id.arch_base)
        doc = xee.fromstring(view_arch)
        field_list = []
        for tag in doc.findall('.//field'):
            field_list.append(tag.attrib['name'])
        crm_lead_fields = self.env['crm.lead']._fields
        filtered_field_list = [
            field for field in field_list
            if not isinstance(crm_lead_fields[field], (
                fields.Many2one, fields.One2many, fields.Many2many))
        ]
        model_id = self.env['ir.model'].sudo().search(
            [('model', '=', 'crm.lead')])
        return [('model_id', '=', model_id.id), ('state', '=', 'base'),
                ('name', 'in', filtered_field_list)]

    def set_domain_partner(self):
        """Return the domain for partner fields."""
        partner_view_id = self.env.ref('base.view_partner_form')
        view_arch = str(partner_view_id.arch_base)
        doc = xee.fromstring(view_arch)
        field_list = []
        for tag in doc.findall('.//field'):
            field_list.append(tag.attrib['name'])
        partner_fields = self.env['res.partner']._fields
        filtered_field_list = [
            field for field in field_list
            if not isinstance(partner_fields[field],
                              (fields.Many2one, fields.One2many,
                               fields.Many2many))
        ]
        model_id = self.env['ir.model'].sudo().search(
            [('model', '=', 'res.partner')])

        return [('model_id', '=', model_id.id), ('state', '=', 'base'),
                ('name', 'in', filtered_field_list)]

    partner_fields_soft_ids = fields.Many2many('ir.model.fields',
                                               'partner_fields_rel',
                                               domain=set_domain_partner,
                                               help='Soft fields in partner '
                                                    'model.')
    partner_fields_rigid_ids = fields.Many2many('ir.model.fields',
                                                'partner_fields_rigid_rel',
                                                domain=set_domain_partner,
                                                help='Rigid fields in partner '
                                                     'model.')
    crm_fields_soft_ids = fields.Many2many('ir.model.fields',
                                           'crm_fields_rel',
                                           domain=set_domain_crm,
                                           help='Soft fields in CRM model.'
                                           )
    crm_fields_rigid_ids = fields.Many2many('ir.model.fields',
                                            'crm_fields_rigid_rel',
                                            domain=set_domain_crm,
                                            help='Rigid fields in CRM model.'
                                            )

    @api.model
    def get_values(self):
        """Get values for the settings."""
        icp_sudo = self.env['ir.config_parameter'].sudo()
        crm_soft_parameter = icp_sudo.get_param(
            'crm_duplicates_real_time_search.crm_fields_soft_ids')
        crm_rigid_parameter = icp_sudo.get_param(
            'crm_duplicates_real_time_search.crm_fields_rigid_ids')
        partner_soft_parameter = icp_sudo.get_param(
            'crm_duplicates_real_time_search.partner_fields_soft_ids')
        partner_rigid_parameter = icp_sudo.get_param(
            'crm_duplicates_real_time_search.partner_fields_rigid_ids')
        opportunity_duplicates_parameter = icp_sudo.get_param(
            'crm_duplicates_real_time_search.opportunity_duplicates')
        leads_duplicates_parameter = icp_sudo.get_param(
            'crm_duplicates_real_time_search.leads_duplicates')
        duplicate_count_tree_kanban_parameter = icp_sudo.get_param(
            'crm_duplicates_real_time_search.duplicate_count_tree_kanban')
        duplicate_count_form_parameter = icp_sudo.get_param(
            'crm_duplicates_real_time_search.duplicate_count_form')
        res = super(ResConfigSettings, self).get_values()
        res.update(opportunity_duplicates=opportunity_duplicates_parameter,
                   leads_duplicates=leads_duplicates_parameter,
                   duplicate_count_tree_kanban=duplicate_count_tree_kanban_parameter,
                   duplicate_count_form=duplicate_count_form_parameter,
                   crm_fields_soft_ids=[(6, 0, literal_eval(crm_soft_parameter))
                                        ] if crm_soft_parameter else False,
                   crm_fields_rigid_ids=[
                       (6, 0, literal_eval(crm_rigid_parameter))
                   ] if crm_rigid_parameter else False,
                   partner_fields_soft_ids=[
                       (6, 0, literal_eval(partner_soft_parameter))
                   ] if partner_soft_parameter else False,
                   partner_fields_rigid_ids=[
                       (6, 0, literal_eval(partner_rigid_parameter))
                   ] if partner_rigid_parameter else False,
                   )
        return res

    def set_values(self):
        """Set values for the settings."""
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'crm_duplicates_real_time_search.crm_fields_soft_ids',
            self.crm_fields_soft_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param(
            'crm_duplicates_real_time_search.crm_fields_rigid_ids',
            self.crm_fields_rigid_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param(
            'crm_duplicates_real_time_search.partner_fields_soft_ids',
            self.partner_fields_soft_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param(
            'crm_duplicates_real_time_search.partner_fields_rigid_ids',
            self.partner_fields_rigid_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param(
            'crm_duplicates_real_time_search.opportunity_duplicates',
            self.opportunity_duplicates)
        self.env['ir.config_parameter'].sudo().set_param(
            'crm_duplicates_real_time_search.leads_duplicates',
            self.leads_duplicates)
        self.env['ir.config_parameter'].sudo().set_param(
            'crm_duplicates_real_time_search.duplicate_count_tree_kanban',
            self.duplicate_count_tree_kanban)
        self.env['ir.config_parameter'].sudo().set_param(
            'crm_duplicates_real_time_search.duplicate_count_form',
            self.duplicate_count_form)
        return res
