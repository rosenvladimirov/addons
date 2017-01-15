# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

from openerp import models, fields, api, _
from openerp.tools.amount_to_text import amount_to_text

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.one
    @api.depends('amount_total')
    def _compute_text(self):
        self.amount_in_word = amount_to_text(self.amount_total, self.currency_id.name)

    amount_in_word = fields.Char(string='Verbally: ', readonly=True,
        default=False, copy=False,  compute='_compute_text'
        )
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
