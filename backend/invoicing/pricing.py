"""Price lookups for invoicing: the price in force on a given date.

Prices come from the simple_history records of the cost models. Every price
change (including the first one) is a history row, so the price in force on a
date is the latest row at or before it. A date before the first row gets the
first row's price: nothing earlier is known, and that is what invoicing used
before history existed. Archived rows are priced 0, as before.
"""

from bisect import bisect_right
from collections import defaultdict

from .models import FixedCosts, LibraryPreparationCosts, SequencingCosts


class _Table:
    """Prices of one cost model, keyed by a tuple of foreign key ids."""

    def __init__(self, model, key_fields):
        # key -> ([history_date, ...], [price, ...]) in time order
        self.history = defaultdict(lambda: ([], []))
        rows = model.history.order_by("history_date", "history_id").values(
            *key_fields, "price", "archived", "history_type", "history_date"
        )
        for row in rows:
            dates, prices = self.history[tuple(row[f] for f in key_fields)]
            dates.append(row["history_date"])
            gone = row["history_type"] == "-" or row["archived"]
            prices.append(0 if gone else row["price"])

        # Rows that have no history at all (fixtures, queryset.update())
        # are priced as they are today, archived or not: nothing in the
        # history ever marked them archived.
        self.current = {}
        rows = model.objects.all().values(*key_fields, "price", "archived")
        for row in rows:
            key = tuple(row[f] for f in key_fields)
            if key not in self.history:
                self.current[key] = 0 if row["archived"] else row["price"]

    def get(self, key, when):
        if when is not None and when.tzinfo is None:
            from datetime import timezone as _tz

            when = when.replace(tzinfo=_tz.utc)
        if key not in self.history:
            return self.current.get(key, 0)
        dates, prices = self.history[key]
        idx = bisect_right(dates, when)
        if idx == 0:
            # Query date is before first history record: return first price.
            return prices[0]
        return prices[idx - 1]


class PriceBook:
    """Prices of all cost models, looked up by key and date."""

    def __init__(self):
        self._fixed = _Table(FixedCosts, ("sequencer_id",))
        self._prep = _Table(LibraryPreparationCosts, ("library_protocol_id",))
        self._seq = _Table(SequencingCosts, ("sequencer_id", "read_length_id"))

    def fixed(self, sequencer_id, when):
        return self._fixed.get((sequencer_id,), when)

    def sequencing(self, sequencer_id, read_length_id, when):
        return self._seq.get((sequencer_id, read_length_id), when)

    def preparation(self, protocol_id, when):
        return self._prep.get((protocol_id,), when)

    def preparation_by_name(self, name, when):
        """Price of the protocol called ``name``; None if it has no price."""
        protocol_id = (
            LibraryPreparationCosts.objects.filter(library_protocol__name=name)
            .values_list("library_protocol_id", flat=True)
            .first()
        )
        if protocol_id is None:
            return None
        return self.preparation(protocol_id, when)
