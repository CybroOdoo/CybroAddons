    # -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import os
import io
import logging
import concurrent.futures

try:
    import polib
except ImportError:
    polib = None

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None

from odoo import models, fields, _
from odoo.exceptions import UserError
from odoo.tools.translate import trans_export
from odoo.modules import get_module_path

_logger = logging.getLogger(__name__)


class AutomaticTranslationWizard(models.TransientModel):
    """
    Wizard to automatically translate module terms.
    Extracts translatable terms from the selected custom module and
    translates them into the target language using deep_translator.
    """
    _name = 'automatic.translation.wizard'
    _description = 'Automatic Translation Wizard'

    language_id = fields.Many2one(
        'res.lang',
        string='Language',
        required=True,
        help="Select the language you want to translate the module into."
    )
    module_id = fields.Many2one(
        'ir.module.module',
        string='App To Translate',
        required=True,
        domain=[('state', '=', 'installed')],
        help="Select the installed module you want to translate."
    )
    overwrite_existing_terms = fields.Boolean(
        string="Overwrite Existing Terms",
        default=False,
        help="If checked, existing translations will be overwritten by the automatic translator."
    )

    def action_translate(self):
        """
        Translates translatable strings of the selected module to the selected language.
        Generates/Updates PO file in the module's i18n directory.
        Uses concurrent translation to avoid HTTP timeout while showing the loading screen.
        """
        if not GoogleTranslator:
            raise UserError(_("Please install 'deep_translator' to use this feature: pip3 install deep_translator"))
        if not polib:
            raise UserError(_("Please install 'polib' to use this feature: pip3 install polib"))

        self.ensure_one()
        module_name = self.module_id.name
        lang_code = self.language_id.code

        # Get language code suitable for GoogleTranslator (usually first part, e.g. 'ar' from 'ar_001')
        target_lang = lang_code.split('_')[0]
        try:
            translator = GoogleTranslator(source='auto', target=target_lang)
        except Exception as e:
            raise UserError(_("Invalid language code for translation: %s") % target_lang)

        # 1. Export current PO file content for the module in the target language
        buf = io.BytesIO()
        try:
            trans_export(lang_code, [module_name], buf, 'po', self.env.cr)
        except Exception as e:
            raise UserError(_("Failed to export module translations: %s") % str(e))

        po_content = buf.getvalue().decode('utf-8')
        
        # 2. Parse PO content using polib
        try:
            po = polib.pofile(po_content)
        except Exception as e:
            raise UserError(_("Failed to parse PO content: %s") % str(e))

        # 3. Translate terms concurrently
        entries_to_translate = []
        for entry in po:
            if not entry.msgid:
                continue
            
            # If there's an existing translation and we're not overwriting, skip
            if entry.msgstr and not self.overwrite_existing_terms:
                continue
            
            entries_to_translate.append(entry)

        translated_count = 0

        if entries_to_translate:
            # Helper function for concurrent translation
            def _translate_entry(entry):
                try:
                    # Create a new translator instance per thread to avoid potential thread-safety issues
                    thread_translator = GoogleTranslator(source='auto', target=target_lang)
                    translated_text = thread_translator.translate(entry.msgid)
                    return entry, translated_text
                except Exception as e:
                    return entry, None

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                for entry, translated_text in executor.map(_translate_entry, entries_to_translate):
                    if translated_text:
                        entry.msgstr = translated_text
                        translated_count += 1

        if translated_count == 0 and not self.overwrite_existing_terms:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Info'),
                    'message': _('No new terms to translate.'),
                    'type': 'info',
                    'sticky': False,
                }
            }

        # 4. Save the generated PO file to the module's i18n directory
        mod_path = get_module_path(module_name)
        if not mod_path:
            raise UserError(_("Module path not found for %s") % module_name)

        i18n_dir = os.path.join(mod_path, 'i18n')
        if not os.path.exists(i18n_dir):
            try:
                os.makedirs(i18n_dir)
            except Exception as e:
                raise UserError(_("Could not create i18n directory. Permission denied: %s") % str(e))

        po_file_path = os.path.join(i18n_dir, f"{lang_code}.po")
        try:
            po.save(po_file_path)
        except Exception as e:
            raise UserError(_("Could not save the PO file. Permission denied: %s") % str(e))

        # Load the newly generated translations into the DB
        try:
            if hasattr(self.module_id, '_update_translations'):
                self.module_id._update_translations(filter_lang=lang_code, overwrite=self.overwrite_existing_terms)
            elif hasattr(self.env['ir.module.module'], '_load_module_terms'):
                self.env['ir.module.module']._load_module_terms([module_name], [lang_code], overwrite=self.overwrite_existing_terms)
            elif hasattr(self.env['ir.translation'], '_load_module_terms'):
                self.env['ir.translation']._load_module_terms([module_name], [lang_code])
        except Exception as e:
            _logger.warning("Failed to load newly generated translations into the database: %s", str(e))

        # Signal Odoo to reload the registry to apply field and view translation changes
        self.env.registry.clear_cache()
        if hasattr(self.env.registry, 'registry_invalidated'):
            self.env.registry.registry_invalidated = True
        if hasattr(self.env.registry, 'signal_changes'):
            self.env.registry.signal_changes()

        # Reload the client browser to immediately show translated labels
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
