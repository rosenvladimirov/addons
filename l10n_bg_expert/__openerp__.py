# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo Bulgaria Accounting, Open Source Accounting and Invoiceing Module
#    Copyright (C) 2016 Rosen Vladimirov, Prodax LTD
#    (vladimirov.rosen@gmail.com, http://www.prodax.bg)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name" : "Bulgaria - Accounting expert version",
    "version" : "1.0",
    "author" : "Rosen Vladimirov",
    "website": "http://www.prodax.bg",
    "category" : "Localization/Account Charts",
    "depends" : ['account','account_chart','base_vat'],
    "description": """
This is the module to manage the Accounting Chart, VAT structure, Fiscal Position
and Tax Mapping. It also adds the Registration Number for Bulgaria in OpenERP.
This is special version of l10n_bg module. Inside is add special links and many
other configuration only for special version of odoo.
=================================================================================

Bulgarian accounting chart and localization.
    """,
    'conflicts': ['l10n_bg'],
    'depends': [
        'account',
        'base_vat',
        'base_iban',
        'account_chart',
        'l10n_multilang',
        'base_bg',
        'report_qweb_element_page_visibility',
        'partner_identification_bg',
        'partner_fr_person'
    ],
    "demo" : [],
    "data" : [
              'data/account_chart.xml',
              'data/account_tax_code_template.xml',
              'data/account_chart_template.xml',
              'data/account_chart_template.yml',
              'data/account_tax_template.xml',
              'data/account_view.xml',
              'data/fiscal_position_template.xml',
              'data/res.country.state.csv',
              'data/res.bank.csv',
              'views/report_invoice.xml',
              'views/account_view.xml',
              'security/ir.model.access.csv',
              'wizard/l10n_chart_bg_wizard.xml'
              ],
    "license": "AGPL-3",
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
