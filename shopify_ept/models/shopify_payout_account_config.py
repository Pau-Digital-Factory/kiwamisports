# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import models, fields


class ShopifyPaymentReportEpt(models.Model):
    _name = "shopify.payout.account.config.ept"
    _description = "Shopify Account Configurations"

    # Shopify Payout Report
    instance_id = fields.Many2one('shopify.instance.ept', string="Instance")
    account_id = fields.Many2one('account.account', string="Account",
                                 help="The account used for this invoice.")
    transaction_type = fields.Selection(
        [('dispute', 'Dispute'),
         ('reserve', 'Reserve'), ('adjustment', 'Adjustment'), ('credit', 'Credit'),
         ('debit', 'Debit'), ('payout', 'Payout'), ('payout_failure', 'Payout Failure'),
         ('payout_cancellation', 'Payout Cancellation'), ('fees', 'Fees'),
         ('shopify_collective_debit_reversal', 'Shopify Collective Debit Reversal')],
        help="The type of the balance transaction", string="Balance Transaction Type")
