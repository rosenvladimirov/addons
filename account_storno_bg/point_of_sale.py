# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    Copyright (C) 2013-Today GRAP (http://www.grap.coop)
#    @author Julien WESTE
#    Copyright (C) 2014 Akretion (<http://www.akretion.com>).
#    @author Sylvain LE GAL (https://twitter.com/legalsylvain)
#    @author Sylvain Calador (sylvain.calador@akretion.com).
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
import logging

from openerp.osv import osv, fields
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)

import openerp.addons.decimal_precision as dp


class pos_order(osv.osv):
    _inherit = 'pos.order'

    def line_get_convert(self, cr, uid, mode, line, part, date, account, tax, tax_code_id, amount_total, journal_id, is_refund, context=None):
        #'product',
        if is_refund and (amount_total < 0 or line.price_subtotal < 0) and journal_id.posting_policy == 'storno':
            if mode == 'product':
                amount = line.price_subtotal
                return {
                        'name': line.product_id.name,
                        'quantity': line.qty,
                        'date': date,
                        #'amount_currency': amount,
                        #'currency_id': order.company_id.currency_id.id,
                        'product_id': line.product_id.id,
                        'account_id': account,
                        'analytic_account_id': self._prepare_analytic_account(cr, uid, line, context=context),
                        'credit': ((amount<0) and amount) or 0.0,
                        'debit': ((amount>0) and -amount) or 0.0,
                        'tax_code_id': tax_code_id,
                        'tax_amount': amount_total,
                        'partner_id': part and self.pool.get("res.partner")._find_accounting_partner(part).id or False
                        }
            elif mode == 'tax':
                return {
                        'name': _('Tax') + ' ' + tax.name,
                        'quantity': line.qty,
                        'product_id': line.product_id.id,
                        'account_id': account,
                        'credit': ((amount_total<0) and amount_total) or 0.0,
                        'debit': ((amount_total>0) and -amount_total) or 0.0,
                        'tax_code_id': tax_code_id,
                        'tax_amount': abs(amount_total) * tax.tax_sign if amount_total>=0 else abs(amount_total) * tax.ref_tax_sign,
                        'partner_id': part and self.pool.get("res.partner")._find_accounting_partner(part).id or False
                        }
            elif mode == 'counter_part':
                return {
                        'name': _("Trade Receivables from POS"), #order.name,
                        'account_id': account,
                        'credit': ((amount_total>0) and -amount_total) or 0.0,
                        'debit': ((amount_total<0) and amount_total) or 0.0,
                        'partner_id': part and self.pool.get("res.partner")._find_accounting_partner(part).id or False
                        }
        else:
            return super(pos_order,self).line_get_convert(cr, uid, mode, line, part, date, account, tax, tax_code_id, amount_total, journal_id, is_refund, context=context)
