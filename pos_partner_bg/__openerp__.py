# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2016 Vertel AB (<http://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
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
    'name': 'POS Partner',
    'version': '0.1',
    'category': 'pos',
    'summary': 'Connect Partner to POS-orders',
    'licence': 'AGPL-3',
    'description': """
        Adds POS Order button to Partner
""",
    'author': 'Vertel AB',
    'website': 'http://www.vertel.se',
    'depends': ['point_of_sale',],
    #~ 'external_dependencies': {
        #~ 'python': ['jsonrpclib'],
    #~ },
    'data': ['res_partner_view.xml'],
    'qweb': ['static/src/xml/*.xml'],
    'application': False,
    'installable': True,
    'demo': [],
}
# vim:expandtab:smartindent:tabstop=4s:softtabstop=4:shiftwidth=4:
