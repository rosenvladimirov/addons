# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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


from openerp.osv import fields, osv
from openerp.tools.translate import _


#in this file, we mostly add the tag translate=True on existing fields that we now want to be translated

class ResPartner(osv.osv):
    _inherit = 'res.partner'
    _columns = {
        'name': fields.char('Name', required=True, translate=True),
        'street': fields.char('Street', required=False, translate=True),
        'street2': fields.char('Street 2', required=False, translate=True),
        'city': fields.char('City', required=False, translate=True),
        'function': fields.char('Function', required=False, translate=True),
    }
class ResBank(osv.osv):
    _inherit = 'res.bank'
    _columns = {
        'name': fields.char('Name ', required=True, translate=True),
        'street': fields.char('Street', required=False, translate=True),
        'street2': fields.char('Street 2', required=False, translate=True),
        'city': fields.char('City', required=False, translate=True),
        'bank_name': fields.char('Bank Name ', required=False, translate=True),
    }
class ResCompany(osv.Model):
    _inherit = 'res.company'
    _columns = {
        'rml_header1': fields.text('Company Tagline', required=False, translate=True),
        'rml_header2': fields.text('RML Internal Header', required=False, translate=True),
        'rml_header3': fields.text('RML Internal Header for Landscape Reports', required=False, translate=True),
        'rml_header': fields.text('RML Header', required=False, translate=True),
        'rml_footer': fields.text('Report Footer', required=False, translate=True),
        'name': fields.char('Name', required=True, translate=True),
        'street': fields.char('Street', required=False, translate=True),
        'street2': fields.char('Street2', required=False, translate=True),
        'city': fields.char('City', required=False, translate=True),
}

