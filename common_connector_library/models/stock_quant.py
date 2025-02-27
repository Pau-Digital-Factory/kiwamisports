# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
import logging
from odoo import models

logger = logging.getLogger(__name__)


class StockQuant(models.Model):
    _inherit = "stock.quant"

    def create_inventory_adjustment_ept(self, product_qty_data, location_id, auto_apply=False, name=""):
        """
        Define this method for create or update product inventory.
        :param: product_qty_data: Dictionary with product and it's quantity. like {'product_id':Qty,52:20, 53:60, 89:23}
        :param: location_id: stock.location()
        :param: auto_apply: True/False
        :param: name: str
        :return: stock.quant()
        """
        quant_list = self.env['stock.quant']
        if product_qty_data and location_id:
            for product_id, product_qty in product_qty_data.items():
                val = self.prepare_vals_for_inventory_adjustment(location_id, product_id, product_qty)
                logger.info("Product ID: %s and its Qty: %s" % (product_id, product_qty))
                quant_list += self.with_context(inventory_mode=True).create(val)
            if auto_apply and quant_list:
                quant_list.filtered(
                    lambda x: x.product_id.tracking not in ['lot', 'serial'] and x.product_id.type not in [
                        'service', 'combo'] and x.product_id.is_storable == True).with_context(
                    inventory_name=name).action_apply_inventory()
        return quant_list

    def prepare_vals_for_inventory_adjustment(self, location_id, product_id, product_qty):
        """
        Define this method prepare a vals for the inventory adjustment record.
        :param: location_id: stock.location()
        :parm: product_id: product.product() id
        :param: product_qty: float
        :return: dict {}
        """
        return {'location_id': location_id.id,
                'product_id': product_id,
                'inventory_quantity': product_qty}
