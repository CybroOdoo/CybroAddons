from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    report_background = fields.Char(string="Report Background", default="rgba(255,255,255,1)")
    header_background = fields.Char(string="Header Background", default="rgba(255,255,255,1)")
    address_color = fields.Char(string="Company Address Colour")
    table_header_background = fields.Char(string="Table Header Background", default="rgba(255,255,255,1)")
    table_header_color = fields.Char(string="Table Header Color")
    table_header_font = fields.Char(string="Table Header Size")
    table_data_background = fields.Char(string="Table Data Background", default="rgba(255,255,255,1)")
    table_data_color = fields.Char(string="Table Data Colour")
    table_data_font = fields.Char(string="Table Data Size")
    header_color = fields.Char(string="Header Colour")
    header_alignment = fields.Selection([('center', 'Center'),
                                         ('left', 'Left'),
                                         ('right', 'Right'),
                                         ], string="Header Alignment")
    logo_alignment = fields.Selection([('center', 'Center'),
                                       ('left', 'Left'),
                                       ('right', 'Right'),
                                       ], string="Logo Alignment")
    address_alignment = fields.Selection([('center', 'Center'),
                                          ('left', 'Left'),
                                          ('right', 'Right'),
                                          ], string="Company Address Alignment")
    table_header_alignment = fields.Selection([('center', 'Center'),
                                          ('left', 'Left'),
                                          ('right', 'Right'),
                                          ], string="Table Header Alignment")
    table_data_alignment = fields.Selection([('center', 'Center'),
                                          ('left', 'Left'),
                                          ('right', 'Right'),
                                          ], string="Table Data Alignment")


class CustomReportConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    report_background = fields.Char(related="company_id.report_background", string="Report Background", default="rgba(255,255,255,1)")
    header_background = fields.Char(related="company_id.header_background", string="Header Background", default="rgba(255,255,255,1)")
    header_alignment = fields.Selection(related="company_id.header_alignment", string="Header Alignment")
    header_color = fields.Char(related="company_id.header_color")
    logo_alignment = fields.Selection(related="company_id.logo_alignment")
    address_alignment = fields.Selection(related="company_id.address_alignment")
    address_color = fields.Char(related="company_id.address_color")
    table_header_background = fields.Char(related="company_id.table_header_background", default="rgba(255,255,255,1)")
    table_header_color = fields.Char(related="company_id.table_header_color")
    table_header_font = fields.Char(related="company_id.table_header_font")
    table_data_background = fields.Char(related="company_id.table_data_background", default="rgba(255,255,255,1)")
    table_data_color = fields.Char(related="company_id.table_data_color")
    table_data_font = fields.Char(related="company_id.table_data_font")
    table_header_alignment = fields.Selection(related="company_id.table_header_alignment")
    table_data_alignment = fields.Selection(related="company_id.table_data_alignment")
