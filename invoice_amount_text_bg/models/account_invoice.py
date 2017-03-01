# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

from openerp import models, fields, api, _
from openerp.tools.amount_to_text import amount_to_text
from openerp.tools.amount_to_text_bg import add_lang_bg
from openerp.tools.amount_to_text_en_en import add_lang_en

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    add_lang_bg()
    add_lang_en()

    @api.one
    @api.depends('amount_total')
    def _compute_text(self):
        self.amount_in_word = amount_to_text(self.amount_total, self.partner_id.lang, self.currency_id.symbol)

    amount_in_word = fields.Char(string='Verbally: ', readonly=True,
        default=False, copy=False,  compute='_compute_text'
        )

    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
