import collections

from . import time

Tax = collections.namedtuple('Tax', ['name', 'base_points'])
UnitPrice = collections.namedtuple(
    'Unit Price',
    ['quantity', 'base_quantity', 'price'])


class Item(object):
    """An item that can be priced (i.e. sold to a customer)
    """
    def __init__(self, reference, label, **kwargs):
        self.reference = reference
        self.label = label
        self.taxes_included = kwargs.get('taxes_included', True)
        self.taxes = kwargs.get('taxes', [])  # list of tax names
        self.unit = kwargs.get('unit', '')
        self.min_units = kwargs.get('min_quantity', 1)
        self.unit_price = UnitPrice(kwargs.get('unit_price', [1, 1, 0]))
        self.recurring = time.delta(kwargs.get('recurring'))
        self.aggregate = time.delta(kwargs.get('aggregate'))
        self.slide = time.delta(kwargs.get('slide'))
        self.interval = time.delta(kwargs.get('interval'))
        self.single_line = kwargs.get('single_line', '{label}')
        self.grouped_line = kwargs.get('grouped_line', '{count} {label}')
        self.refund_line = kwargs.get('refund_line', '{label}')

    def validate(self, config):
        assert set(self.taxes) <= set(t.name for t in config.taxes)
        assert not self.sliding_aggregate or self.aggregate_period


class Accounting(object):
    """Accounting rules
    """
    def __init__(self, **kwargs):
        freeze_interval = time.delta(kwargs.get('freeze_interval', "M"))
        rollover = time.delta(kwargs.get('rollover'))
        loss_cutoff = time.delta(kwargs.get('loss_cutoff', "1Y"))
        anonymization_cutoff = time.delta(
            kwargs.get('anonymization_cutoff', "1Y"))
        purge_cutoff = time.delta(kwargs.get('purge_cutoff', "10Y"))

    def validate(self):
        assert self.loss_cutoff <= self.anonymization_cutoff
        assert self.anonymization_cutoff <= self.purge_cutoff


class Config(object):
    """Full configuration for a firm
    """
    def __init__(self, **kwargs):
        taxes = [Tax(o) for o in kwargs.get('taxes', [])]
        items = {o['reference']: Item(o) for o in kwargs.get('items', [])}
