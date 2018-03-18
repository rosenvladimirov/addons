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
    "name" : "Bulgaria - Fiscal printer expert version",
    "version" : "1.0",
    "author" : "Rosen Vladimirov",
    "website": "http://www.prodax.bg",
    "category" : "Localization/Account Charts",
    "depends" : ['account','account_chart','base_vat'],
    "description": """
This is the module to manage the Fiscal Position for fiscal printer and configure
for pos.
=================================================================================

Bulgarian fiscal printer configurations.
    """,
    'depends': [
        'base_vat',
        'l10n_multilang',
        'point_of_sale'
    ],
    "demo" : [],
    "data" : [
              'views/pos_box.xml',
              'views/point_of_sale.xml',
              'views/account_view.xml'
              ],
    "license": "AGPL-3",
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
