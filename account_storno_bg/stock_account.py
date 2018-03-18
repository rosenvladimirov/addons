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
from openerp.tools import float_compare, float_round
from openerp.tools.translate import _
from openerp import SUPERUSER_ID, api
from openerp import tools
import logging

_logger = logging.getLogger(__name__)

#----------------------------------------------------------
# Quants
#----------------------------------------------------------
class stock_quant(osv.osv):
    _inherit = "stock.quant"

    def _storno_prepare_account_move_line(self, cr, uid, move, qty, cost, credit_account_id, debit_account_id, tax_id, context=None):
        """
        Generate the account.move.line values to post to track the stock valuation difference due to the
        processing of the given quant.
        """
        if context is None:
            context = {}
        currency_obj = self.pool.get('res.currency')
        # revert supplier refund
        if move.location_id.usage in ('internal', 'pos') and move.location_dest_id.usage == 'supplier':
            tmp_credit_account_id = credit_account_id
            tmp_debit_account_id = debit_account_id
            credit_account_id = tmp_debit_account_id
            debit_account_id = tmp_credit_account_id

        if context.get('force_valuation_amount'):
            valuation_amount = context.get('force_valuation_amount')
        else:
            if move.product_id.cost_method == 'average':
                valuation_amount = cost if move.location_id.usage not in ('internal', 'pos') and move.location_dest_id.usage in ('internal', 'pos') else move.product_id.standard_price
            else:
                valuation_amount = cost if move.product_id.cost_method == 'real' else move.product_id.standard_price
        #the standard_price of the product may be in another decimal precision, or not compatible with the coinage of
        #the company currency... so we need to use round() before creating the accounting entries.
        acc_obj = self.pool.get('account.account')
        #_logger.info("Prepare move lines %s::%s/%s::%s:%s" % (tax_id,credit_account_id,debit_account_id,acc_obj.browse(cr,uid,credit_account_id,context=context).name,acc_obj.browse(cr,uid,debit_account_id,context=context).name))
        valuation_amount = currency_obj.round(cr, uid, move.company_id.currency_id, valuation_amount * qty)
        partner_id = (move.picking_id.partner_id and self.pool.get('res.partner')._find_accounting_partner(move.picking_id.partner_id).id) or False
        debit_line_vals = {
                    'name': move.name,
                    'product_id': move.product_id.id,
                    'quantity': qty,
                    'product_uom_id': move.product_id.uom_id.id,
                    'ref': move.picking_id and move.picking_id.name or False,
                    'date': move.date,
                    'partner_id': partner_id,
                    'debit': valuation_amount > 0 and -valuation_amount or 0,
                    'credit': valuation_amount < 0 and valuation_amount or 0,
                    'account_id': debit_account_id,
        }
        credit_line_vals = {
                    'name': move.name,
                    'product_id': move.product_id.id,
                    'quantity': qty,
                    'product_uom_id': move.product_id.uom_id.id,
                    'ref': move.picking_id and move.picking_id.name or False,
                    'date': move.date,
                    'partner_id': partner_id,
                    'credit': valuation_amount > 0 and -valuation_amount or 0,
                    'debit': valuation_amount < 0 and valuation_amount or 0,
                    'account_id': credit_account_id,
        }
        # Create taxes when debit
        if tax_id:
            tax_obj = self.pool.get('account.tax')
            ret = [(0, 0, credit_line_vals)]
            total = 0
            base_code = 'base_code_id'
            tax_code = 'tax_code_id'
            account_id = 'account_collected_id'
            base_sign = 'base_sign'
            tax_sign = 'tax_sign'
            for tax in tax_obj.compute_all(cr, uid, [tax_id], valuation_amount, 1.00, force_excluded=False).get('taxes'):
                #create the Tax movement
                if not tax['amount'] and not tax[tax_code]:
                    continue
                #FORWARD-PORT UPTO SAAS-6
                tax_analytic = (tax_code == 'tax_code_id' and tax.get('account_analytic_collected_id'))

                data = {
                    'name': tools.ustr(move.name or '') + ' ' + tools.ustr(tax['name'] or ''),
                    'date': move.date,
                    'partner_id': partner_id,
                    'ref': move.picking_id and move.picking_id.name or False,
                    'account_tax_id': False,
                    'tax_code_id': tax[tax_code],
                    'tax_amount': tax[tax_sign] * tax['amount'],
                    'account_id': tax[account_id],
                    'credit': tax['amount'] < 0 and tax['amount'] or 0.0,
                    'debit': tax['amount'] < 0 and tax['amount'] or 0.0,
                    'analytic_account_id': tax_analytic,
                }
                total = total + tax['amount']
                ret.append((0, 0, data))
            debit_line_vals['debit'] = debit_line_vals['debit']+total
            ret.append((0, 0, debit_line_vals))
            return ret

        return [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]

    def _create_account_move_line(self, cr, uid, quants, move, credit_account_id, debit_account_id, tax_id, journal_id, context=None):
        #group quants by cost
        quant_cost_qty = {}
        for quant in quants:
            if quant_cost_qty.get(quant.cost):
                quant_cost_qty[quant.cost] += quant.qty
            else:
                quant_cost_qty[quant.cost] = quant.qty
        move_obj = self.pool.get('account.move')
        journal = self.pool.get('account.journal').browse(cr, uid, [journal_id], context=context)
        #_logger.info("Create move start %s:%s" % (context, journal.name))
        for cost, qty in quant_cost_qty.items():
            if ((qty < 0 or cost < 0) or context.get('force_refund', False)) and (journal and journal.posting_policy == 'storno'):
                # _logger.info("Create move storno %s:%s:%s" % (context, journal, journal_id))
                journal_id = journal.refund_journal_id.id
                move_lines = self._storno_prepare_account_move_line(cr, uid, move, qty, -cost, credit_account_id, debit_account_id, tax_id, context=context)
            else:
                move_lines = self._prepare_account_move_line(cr, uid, move, qty, cost, credit_account_id, debit_account_id, tax_id, context=context)

            period_id = context.get('force_period', self.pool.get('account.period').find(cr, uid, context=context)[0])
            move_obj.create(cr, uid, {'journal_id': journal_id,
                                      'line_id': move_lines,
                                      'period_id': period_id,
                                      'date': fields.date.context_today(self, cr, uid, context=context),
                                      'ref': move.picking_id.name}, context=context)
