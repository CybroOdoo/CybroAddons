from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    session_expire_time = fields.Integer('Session Expire time In Minutes',
                                         config_parameter='restrict_logins.session_expire_time')
