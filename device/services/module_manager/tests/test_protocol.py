from __future__ import annotations

from device.services.module_manager.protocol import IdentifyRequest, IdentifyResponse


def test_identify_request_json() -> None:
    req = IdentifyRequest()
    assert req.to_json()["type"] == "identify_request"


def test_identify_response_from_json() -> None:
    data = {
        "type": "identify_response",
        "module_id": "mod-0",
        "module_type": "mock",
        "hardware_version": "1.0",
        "firmware_version": "1.0.0",
    }
    resp = IdentifyResponse.from_json(data)
    assert resp.module_id == "mod-0"
    assert resp.type == "identify_response"
