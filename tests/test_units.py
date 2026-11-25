import unittest
from unittest import mock

import olca_schema as o

from olca_ipc.ipc import Client
from olca_ipc.rest import RestClient


def _unit_groups() -> list[o.UnitGroup]:
    mass = o.UnitGroup(
        id="mass",
        name="Units of mass",
        units=[
            o.Unit(id="kg", name="kg", conversion_factor=1.0, is_ref_unit=True),
            o.Unit(id="t", name="t", conversion_factor=1000.0),
        ],
    )
    empty = o.UnitGroup(id="empty", name="Empty", units=None)
    items = o.UnitGroup(
        id="items",
        name="Units of items",
        units=[
            o.Unit(id="item", name="Item(s)", is_ref_unit=True),
            # a second unit with the name `t`; the first one wins
            o.Unit(id="t2", name="t"),
        ],
    )
    return [mass, empty, items]


class UnitTest(unittest.TestCase):
    """Checks the unit lookups of both clients; needs no server."""

    def clients(self):
        return [Client(), RestClient("http://localhost:8080/")]

    def test_get_unit(self):
        cases = [
            ({"name": "kg"}, "kg"),
            ({"name": "Item(s)"}, "item"),
            ({"name": "t"}, "t"),
            ({"uid": "t2"}, "t2"),
            # the ID has precedence over the name
            ({"uid": "t2", "name": "kg"}, "t2"),
            ({"name": "m3"}, None),
            ({"uid": "m3"}, None),
        ]
        for client in self.clients():
            for args, uid in cases:
                with self.subTest(client=type(client).__name__, args=args):
                    with mock.patch.object(
                        type(client), "get_all", return_value=_unit_groups()
                    ) as get_all:
                        unit = client.get_unit(**args)
                    get_all.assert_called_once_with(o.UnitGroup)
                    self.assertEqual(uid, unit.id if unit else None)

    def test_get_unit_without_id_or_name(self):
        for client in self.clients():
            with self.subTest(client=type(client).__name__):
                with mock.patch.object(type(client), "get_all") as get_all:
                    with self.assertLogs(level="ERROR"):
                        self.assertIsNone(client.get_unit())
                get_all.assert_not_called()

    def test_find_unit(self):
        for client in self.clients():
            with self.subTest(client=type(client).__name__):
                with mock.patch.object(
                    type(client), "get_all", return_value=_unit_groups()
                ):
                    ref = client.find_unit("t")
                    missing = client.find_unit("m3")
                assert ref is not None
                self.assertEqual("t", ref.id)
                self.assertEqual("t", ref.name)
                self.assertEqual(o.RefType.Unit, ref.ref_type)
                self.assertIsNone(missing)


if __name__ == "__main__":
    unittest.main()
