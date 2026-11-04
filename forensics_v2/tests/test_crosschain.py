"""Real public transaction of 2024-12-13, leaving Solana through Wormhole's token bridge, kept as a fixture: no network here."""

import base64
import copy
import json
from pathlib import Path

from forensics_v2 import crosschain as X
from forensics_v2 import decode as D

F = json.loads((Path(__file__).parent / "fixtures/wormhole_portal_tx.json").read_text())


def test_bridge_programs_seen_in_the_transaction():
    d = D.decode(F["tx"])
    assert {"wormhole_core", "wormhole_token_bridge"} <= set(X.bridges_in(d.programs))
    assert X.bridges_in(["11111111111111111111111111111111"]) == []


def test_vaa_layout_gives_the_message_identity():
    v = X.parse_vaa(base64.b64decode(F["operation"]["vaa"]["raw"]))
    assert "%d/%s/%d" % (v["emitter_chain"], v["emitter_hex"], v["sequence"]) == F["operation"]["id"]
    assert v["signatures"] >= 13


def test_source_proof_needs_the_message_in_the_transaction_itself():
    assert X.source_proof(F["tx"], F["operation"])["evidence"] == X.ONCHAIN
    wrong = copy.deepcopy(F["operation"])
    wrong["sequence"] = "1"
    assert X.source_proof(F["tx"], wrong)["evidence"] == X.INDEXER
    other = copy.deepcopy(F["operation"])
    other["emitterAddress"] = "ab" * 32
    assert X.source_proof(F["tx"], other)["evidence"] == X.INDEXER


def test_no_arrival_is_not_found_and_an_unknown_chain_stays_with_the_indexer():
    assert X.destination_proof(2, None)["evidence"] == X.NOT_FOUND
    assert X.destination_proof(999, "0xabc")["evidence"] == X.INDEXER
