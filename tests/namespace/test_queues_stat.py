import os
import sys
import importlib

# noinspection PyUnresolvedReferences
import tests.mock_tables.dbconnector

modules_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(modules_path, 'src'))

from unittest import TestCase

from ax_interface import ValueType
from ax_interface.pdu_implementations import GetPDU, GetNextPDU
from ax_interface.encodings import ObjectIdentifier
from ax_interface.constants import PduTypes
from ax_interface.pdu import PDU, PDUHeader
from ax_interface.mib import MIBTable
from sonic_ax_impl.mibs.vendor.cisco import ciscoSwitchQosMIB
from sonic_ax_impl import mibs

class TestQueueCounters(TestCase):
    @classmethod
    def setUpClass(cls):
        tests.mock_tables.dbconnector.load_namespace_config()
        importlib.reload(ciscoSwitchQosMIB)
        cls.lut = MIBTable(ciscoSwitchQosMIB.csqIfQosGroupStatsTable)

        # Update MIBs
        for updater in cls.lut.updater_instances:
            updater.reinit_data()
            updater.update_data()

    def test_getQueueCounters(self):
        for counter_id in range(1, 8):
            oid = ObjectIdentifier(8, 0, 0, 0, (1, 3, 6, 1, 4, 1, 9, 9, 580, 1, 5, 5, 1, 4, 1, 2, 1, 1))
            get_pdu = GetPDU(
                header=PDUHeader(1, PduTypes.GET, 16, 0, 42, 0, 0, 0),
                oids=[oid]
            )

            encoded = get_pdu.encode()
            response = get_pdu.make_response(self.lut)
            print(response)

            value0 = response.values[0]
            self.assertEqual(value0.type_, ValueType.COUNTER_64)
            self.assertEqual(str(value0.name), str(oid))
            self.assertEqual(value0.data, 1)


    # Test issue https://github.com/sonic-net/sonic-buildimage/issues/17448
    # In this Scenario not all counters are created.
    # Ethernet24 is created on mock_tables\asic0\counters_db.json with only counters for UC 0,1,2,3,4,6
    # Ethernet32 is created on mock_tables\asic1\counters_db.json with only counters for MC 0,2,3,5,6,7
    # Ethernet40 is created on mock_tables\asic2\counters_db.json with only counters for UC 1,2,4,6,7 and MC 0,1,3,5,6
    def test_getQueueCountersForPortWithAllCounters(self):
        tested_ports_counters_data = {
            25: { 1: {1:1, 2:23492723984237432, 5:3,6:0}, 2: {1:1, 2:2, 5:3, 6:0},
                  3: {1:1, 2:2, 5:3, 6:0}, 4: {1:1, 2:2, 5:3, 6:0},
                  5: {1:1, 2:2, 5:3, 6:0}, 7: {1:1, 2:2, 5:3, 6:0}
                  },
            33: { 1: {3:1, 4:2, 7:3, 8:0}, 3: {3:1, 4:2, 7:3, 8:0},
                  4: {3:1, 4:2, 7:3, 8:0}, 6: {3:1, 4:2, 7:3, 8:0},
                  7: {3:1, 4:2, 7:3, 8:0}, 8: {3:1, 4:2, 7:3, 8:0}
                  },
            41: { 1: {3:123459, 4:23492723984237432, 7:3, 8:0}, 2: {1:1, 2:2, 3:1, 4:2, 5:3, 6:0, 7:3,8:0},
                  3: {1:1, 2:2, 5:3, 6:0}, 4: {3:1, 4:2, 7:3, 8:0},
                  5: {1:1, 2:2, 5:3, 6:0}, 6: {3:1, 4:2, 7:3, 8:0},
                  7: {1:1, 2:2, 3:1, 4:2, 5:3, 6:0, 7:3,8:0}, 8: {1:1, 2:2, 5:3, 6:0}
                  }
        }

        for port, configured_queues in tested_ports_counters_data.items():
            for queue_id in range(1, 8):
                for counter_id in range(1, 8):
                    oid = ObjectIdentifier(8, 0, 0, 0, (1, 3, 6, 1, 4, 1, 9, 9, 580, 1, 5, 5, 1, 4, port, 2, queue_id, counter_id))
                    get_pdu = GetPDU(
                        header=PDUHeader(1, PduTypes.GET, 16, 0, 42, 0, 0, 0),
                        oids=[oid]
                    )

                    encoded = get_pdu.encode()
                    response = get_pdu.make_response(self.lut)
                    print(response)
                    value0 = response.values[0]
                    if queue_id in configured_queues.keys() and counter_id in configured_queues[queue_id]:
                        self.assertEqual(value0.type_, ValueType.COUNTER_64)
                        self.assertEqual(str(value0.name), str(oid))
                        self.assertEqual(value0.data, configured_queues[queue_id][counter_id])
                    else:
                        self.assertEqual(value0.type_, ValueType.NO_SUCH_INSTANCE)
                        self.assertEqual(str(value0.name), str(oid))
                        self.assertEqual(value0.data, None)


    def test_getNextPduForQueueCounter(self):
        oid = ObjectIdentifier(8, 0, 0, 0, (1, 3, 6, 1, 4, 1, 9, 9, 580, 1, 5, 5, 1, 4, 1, 2, 1, 1))
        expected_oid = ObjectIdentifier(8, 0, 0, 0, (1, 3, 6, 1, 4, 1, 9, 9, 580, 1, 5, 5, 1, 4, 1, 2, 1, 2))
        get_pdu = GetNextPDU(
            header=PDUHeader(1, PduTypes.GET_NEXT, 16, 0, 42, 0, 0, 0),
            oids=[oid]
        )

        encoded = get_pdu.encode()
        response = get_pdu.make_response(self.lut)
        print(response)

        value0 = response.values[0]
        self.assertEqual(value0.type_, ValueType.COUNTER_64)
        self.assertEqual(str(value0.name), str(expected_oid))
        self.assertEqual(value0.data, 23492723984237432 % pow(2, 64)) # Test integer truncation

    def test_getNextPduForQueueCounter_asic2(self):
        oid = ObjectIdentifier(8, 0, 0, 0, (1, 3, 6, 1, 4, 1, 9, 9, 580, 1, 5, 5, 1, 4, 9016, 2, 1, 1))
        expected_oid = ObjectIdentifier(8, 0, 0, 0, (1, 3, 6, 1, 4, 1, 9, 9, 580, 1, 5, 5, 1, 4, 9016, 2, 1, 2))
        get_pdu = GetNextPDU(
            header=PDUHeader(1, PduTypes.GET_NEXT, 16, 0, 42, 0, 0, 0),
            oids=[oid]
        )

        encoded = get_pdu.encode()
        response = get_pdu.make_response(self.lut)
        print(response)

        value0 = response.values[0]
        self.assertEqual(value0.type_, ValueType.COUNTER_64)
        self.assertEqual(str(value0.name), str(expected_oid))
        self.assertEqual(value0.data, 24) # Test integer truncation

    def test_getNextPduForQueueCounter_wrapped(self):
        oid = ObjectIdentifier(8, 0, 0, 0, (1, 3, 6, 1, 4, 1, 9, 9, 580, 1, 5, 5, 1, 4, 1, 2, 1, 2))
        expected_oid = ObjectIdentifier(8, 0, 0, 0, (1, 3, 6, 1, 4, 1, 9, 9, 580, 1, 5, 5, 1, 4, 1, 2, 1, 3))
        get_pdu = GetNextPDU(
            header=PDUHeader(1, PduTypes.GET_NEXT, 16, 0, 42, 0, 0, 0),
            oids=[oid]
        )

        encoded = get_pdu.encode()
        response = get_pdu.make_response(self.lut)
        print(response)

        value0 = response.values[0]
        self.assertEqual(value0.type_, ValueType.COUNTER_64)
        self.assertEqual(str(value0.name), str(expected_oid))
        self.assertEqual(value0.data, 123459) # Test integer truncation

    def test_getIngressQueueCounters(self):
        oid = ObjectIdentifier(8, 0, 0, 0, (1, 3, 6, 1, 4, 1, 9, 9, 580, 1, 5, 5, 1, 4, 1, 1, 1, 1))
        get_pdu = GetPDU(
            header=PDUHeader(1, PduTypes.GET, 16, 0, 42, 0, 0, 0),
            oids=[oid]
        )

        encoded = get_pdu.encode()
        response = get_pdu.make_response(self.lut)
        print(response)

        value0 = response.values[0]
        self.assertEqual(value0.type_, ValueType.NO_SUCH_INSTANCE)
        self.assertEqual(str(value0.name), str(oid))
        self.assertEqual(value0.data, None)

    def test_getMulticastQueueCountersWrapped(self):
        oid = ObjectIdentifier(8, 0, 0, 0, (1, 3, 6, 1, 4, 1, 9, 9, 580, 1, 5, 5, 1, 4, 1, 2, 1, 3))
        get_pdu = GetPDU(
            header=PDUHeader(1, PduTypes.GET, 16, 0, 42, 0, 0, 0),
            oids=[oid]
        )

        encoded = get_pdu.encode()
        response = get_pdu.make_response(self.lut)
        print(response)

        value0 = response.values[0]
        self.assertEqual(value0.type_, ValueType.COUNTER_64)
        self.assertEqual(str(value0.name), str(oid))
        self.assertEqual(value0.data, 123459)

    def test_getMulticastQueueCountersWrapped_asic1(self):
        oid = ObjectIdentifier(8, 0, 0, 0, (1, 3, 6, 1, 4, 1, 9, 9, 580, 1, 5, 5, 1, 4, 9, 2, 1, 3))
        get_pdu = GetPDU(
            header=PDUHeader(1, PduTypes.GET, 16, 0, 42, 0, 0, 0),
            oids=[oid]
        )

        encoded = get_pdu.encode()
        response = get_pdu.make_response(self.lut)
        print(response)

        value0 = response.values[0]
        self.assertEqual(value0.type_, ValueType.COUNTER_64)
        self.assertEqual(str(value0.name), str(oid))
        self.assertEqual(value0.data, 10)

    def test_getMulticastQueueCounters(self):
        oid = ObjectIdentifier(8, 0, 0, 0, (1, 3, 6, 1, 4, 1, 9, 9, 580, 1, 5, 5, 1, 4, 5, 2, 1, 9))
        get_pdu = GetPDU(
            header=PDUHeader(1, PduTypes.GET, 16, 0, 42, 0, 0, 0),
            oids=[oid]
        )

        encoded = get_pdu.encode()
        response = get_pdu.make_response(self.lut)
        print(response)

        value0 = response.values[0]
        self.assertEqual(value0.type_, ValueType.NO_SUCH_INSTANCE)
        self.assertEqual(str(value0.name), str(oid))
        self.assertEqual(value0.data, None)

    def test_getSubtreeForQueueCounters(self):
        oid = ObjectIdentifier(8, 0, 0, 0, (1, 3, 6, 1, 4, 1, 9, 9, 580, 1, 5, 5))
        expected_oid = ObjectIdentifier(8, 0, 0, 0, (1, 3, 6, 1, 4, 1, 9, 9, 580, 1, 5, 5, 1, 4, 1, 2, 1, 1))
        get_pdu = GetNextPDU(
            header=PDUHeader(1, PduTypes.GET_NEXT, 16, 0, 42, 0, 0, 0),
            oids=[oid]
        )

        encoded = get_pdu.encode()
        response = get_pdu.make_response(self.lut)

        value0 = response.values[0]
        self.assertEqual(value0.type_, ValueType.COUNTER_64)
        self.assertEqual(str(value0.name), str(expected_oid))
        self.assertEqual(value0.data, 1)
