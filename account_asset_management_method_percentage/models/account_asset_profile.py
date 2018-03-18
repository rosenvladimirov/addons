# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _


class AccountAssetProfile(models.Model):
    _inherit = 'account.asset.profile'

    method_time = fields.Selection(
        help="Choose the method to use to compute the dates and "
             "number of depreciation lines.\n"
             "  * Number of Years: Specify the number of years "
             "for the depreciation.\n"
             "  * Number of Depreciations: Fix the number of "
             "depreciation lines and the time between 2 depreciations.\n"
             "  * Ending Date: Choose the time between 2 depreciations "
             "and the date the depreciations won't go beyond.")

    @api.model
    def _selection_method_time(self):
        res = super(AccountAssetProfile, self)._selection_method_time()
        res += [('percentage', _('Fixed percentage'))]
        mode = list(map(lambda x: x[0], res))
        mode = self._context.get('mode', mode)
        return filter(lambda x: x[0] in mode, res)
