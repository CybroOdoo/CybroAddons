from odoo import models, fields, api


class AiFetchModelWizard(models.TransientModel):
    """Wizard that fetches available models from a live provider API and lets the user import them."""

    _name = 'ai.fetch.model.wizard'
    _description = 'Fetch Models Wizard'

    provider_id = fields.Many2one('ai.provider', string='Provider', required=True)
    model_line_ids = fields.One2many(
        'ai.fetch.model.wizard.line', 'wizard_id', string='Discovered Models'
    )

    @api.model
    def default_get(self, fields_list: list) -> dict:
        """Pre-populate provider_id from the active record context."""
        res = super().default_get(fields_list)
        if self._context.get('active_id'):
            res['provider_id'] = self._context.get('active_id')
        return res

    def action_fetch(self) -> dict:
        """Fetch available models live from the provider API and populate the line list."""
        self.ensure_one()
        models_data = self.provider_id.fetch_available_models()
        self.model_line_ids = [
            (0, 0, {'name': m['name'], 'model_use': m['model_use'], 'selected': True})
            for m in models_data
        ]
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ai.fetch.model.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def action_confirm(self) -> dict:
        """Import all selected model lines as ai.model records (skip existing ones)."""
        self.ensure_one()
        ai_model = self.env['ai.model'].sudo()
        for line in self.model_line_ids.filtered('selected'):
            if not ai_model.search([
                ('name', '=', line.name),
                ('provider_id', '=', self.provider_id.id),
            ], limit=1):
                ai_model.create({
                    'name': line.name,
                    'provider_id': self.provider_id.id,
                    'model_use': line.model_use,
                    'active': True,
                })
        return {'type': 'ir.actions.act_window_close'}


class AiFetchModelWizardLine(models.TransientModel):
    """One discovered model entry inside the Fetch Models wizard."""

    _name = 'ai.fetch.model.wizard.line'
    _description = 'Fetch Models Wizard Line'

    wizard_id = fields.Many2one('ai.fetch.model.wizard')
    name = fields.Char(string='Model ID', required=True)
    model_use = fields.Selection([
        ('chat', 'Chat Completion'),
        ('embedding', 'Text Embedding'),
        ('multimodal', 'Multimodal / Vision'),
    ], string='Use', default='chat')
    selected = fields.Boolean(string='Import', default=True)
