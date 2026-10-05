import re
from pathlib import Path

from odoo.tests import TransactionCase, new_test_user, tagged
from odoo.tools.translate import PoFileReader, code_translations

I18N = Path(__file__).parent.parent / 'i18n'
PLACEHOLDER = re.compile(r'%\([a-z_]+\)s|%s')
LANGUAGES = {'es': 'es_ES', 'ar': 'ar_001'}


def read_po(path):
    with path.open('rb') as f:
        return list(PoFileReader(f))


@tagged('post_install', '-at_install')
class TestDynamicDashboardTranslations(TransactionCase):

    def test_po_files_are_complete(self):
        """ Every term of the template is translated, with the same placeholders. """
        template = {entry['src'] for entry in read_po(I18N / 'odoo_dynamic_dashboard.pot')}
        self.assertGreater(len(template), 300)
        for lang in LANGUAGES:
            with self.subTest(lang=lang):
                entries = {entry['src']: entry['value'] for entry in read_po(I18N / f'{lang}.po')}
                self.assertEqual(set(entries), template, "the .po file follows the template")
                for source, translation in entries.items():
                    self.assertTrue(translation, f"untranslated: {source!r}")
                    self.assertEqual(
                        sorted(PLACEHOLDER.findall(translation)), sorted(PLACEHOLDER.findall(source)),
                        f"placeholders differ: {source!r} -> {translation!r}",
                    )

    def test_translations_are_loaded(self):
        for code in LANGUAGES.values():
            self.env['res.lang']._activate_lang(code)
        self.env['ir.module.module']._load_module_terms(['odoo_dynamic_dashboard'], list(LANGUAGES.values()))

        # menus, models and fields
        root = self.env.ref('odoo_dynamic_dashboard.odoo_dynamic_dashboard_menu_root')
        self.assertEqual(root.with_context(lang='es_ES').name, "Estudio de tableros dinámicos")
        self.assertEqual(root.with_context(lang='ar_001').name, "استوديو لوحات البيانات الديناميكية")
        Block = self.env['dynamic.dashboard.block']
        self.assertEqual(
            Block.with_context(lang='es_ES').fields_get(['block_type'])['block_type']['string'], "Tipo",
        )
        selection = dict(Block.with_context(lang='ar_001').fields_get(['block_type'])['block_type']['selection'])
        self.assertEqual(selection['pie'], "مخطط دائري")

        # messages of the server, in the language of the user (sent by the web client)
        user = new_test_user(
            self.env, login='translated_user', lang='es_ES',
            groups='odoo_dynamic_dashboard.odoo_dynamic_dashboard_group_user',
        )
        Block = self.env['dynamic.dashboard.block'].with_user(user).with_context(lang=user.lang)
        data = Block.preview_block({'block_type': 'bar', 'model': 'res.partner'})
        self.assertIn("necesita un campo para agrupar", data['error'])
        data = Block.preview_block({'block_type': 'bar', 'model': 'res.partner', 'group_by': 'type'})
        self.assertTrue(data['name'].startswith("Número de "), data['name'])
        self.assertIn(" por ", data['name'])

        # terms of the web client (JavaScript and templates)
        for code, expected in (('es_ES', "Generar con IA"), ('ar_001', "إنشاء بالذكاء الاصطناعي")):
            web_terms = code_translations.get_web_translations('odoo_dynamic_dashboard', code)
            values = {message['id']: message['string'] for message in web_terms['messages']}
            self.assertEqual(values.get("Generate with AI"), expected, code)
            self.assertGreater(len(values), 200, "the terms of the JavaScript code and templates are sent")
