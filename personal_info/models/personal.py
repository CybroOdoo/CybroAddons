# -*- coding: utf-8 -*-

from odoo import api, models, fields

class FirstNameLastName(models.Model):
    _inherit = 'res.partner'

    dob = fields.Date(string="Date of Birth")
    nationality = fields.Char(string="Nationality")
    personal_number = fields.Char(string="Personal Number")
    personal_email = fields.Char(string="Email")
    marital = fields.Selection([
                                ('single', 'Single'),
                                ('married', 'Married'),
                                ('cohabitant', 'Legal Cohabitant'),
                                ('widower', 'Widower'),
                                ('divorced', 'Divorced')], string='Marital Status')
    social_twitter = fields.Char('Twitter Account')
    social_facebook = fields.Char('Facebook Account')
    social_github = fields.Char('GitHub Account')
    social_linkedin = fields.Char('LinkedIn Account')
    social_youtube = fields.Char('Youtube Account')