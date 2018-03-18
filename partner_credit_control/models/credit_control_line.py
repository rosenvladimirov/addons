# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import time

from openerp import models, fields, api, _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as dt

_logger = logging.getLogger('credit.line.control')

class CreditControlLine(models.Model):
    _inherit = "credit.control.line"

    last_date = fields.Datetime(string='Controlling date',
                                 default=lambda *a: time.strftime(dt))
    pos_order_id = fields.Many2one('pos.order',
                                 string='Pos order',
                                 readonly=True)
    state = fields.Selection(selection_add=[('temporary_permit', 'Agree temporary permit')])
    channel = fields.Selection(selection_add=[('internal_letter', 'internal letter for temporary permit'), ('phone', 'Phone Call')])

    @api.model
    def create(self, vals):
        if not vals.get('last_date', False):
            vals['last_date'] = time.strftime(dt)
        if 'date' and 'partner_id' in vals:
            _logger.info("Vals %s" % vals)
            partner = self.env['res.partner'].browse(vals['partner_id'])
            partner.write({'last_credit_control_date': vals['last_date']})
        return super(CreditControlLine, self).create(vals)
