# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def prepare_payment_dict(self, work_flow_process_record):
        """
        Define this method for prepare a vals dictionary for payment.
        :param: sale.workflow.process.ept()
        :return: dict {}
        """
        return {
            'journal_id': work_flow_process_record.journal_id.id,
            'memo': self.payment_reference,
            'currency_id': self.currency_id.id,
            'payment_type': 'inbound',
            'date': self.date,
            'partner_id': self.commercial_partner_id.id,
            'amount': self.amount_residual,
            'payment_method_id': work_flow_process_record.inbound_payment_method_id.id,
            'partner_type': 'customer',
            "write_off_line_vals": []
        }
