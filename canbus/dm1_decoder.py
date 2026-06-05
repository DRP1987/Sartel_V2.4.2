"""DM1 (Active Diagnostic Trouble Codes) decoder for J1939 CAN bus."""

from typing import Dict, List, Any, Tuple

# J1939 PGN for DM1 — Active Diagnostic Trouble Codes
DM1_PGN = 0xFECA

# Human-readable descriptions for each 2-bit lamp value
_LAMP_STATUS: Dict[int, str] = {
    0b00: "Off",
    0b01: "On",
    0b10: "Fast Flash",
    0b11: "Slow Flash",
}

# J1939 Failure Mode Identifier descriptions
FMI_DESCRIPTIONS: Dict[int, str] = {
    0:  "Data valid but above normal operational range — most severe",
    1:  "Data valid but below normal operational range — most severe",
    2:  "Data erratic, intermittent or incorrect",
    3:  "Voltage above normal, or shorted high",
    4:  "Voltage below normal, or shorted low",
    5:  "Current below normal or open circuit",
    6:  "Current above normal or grounded circuit",
    7:  "Mechanical system not responding properly",
    8:  "Abnormal frequency, pulse width or period",
    9:  "Abnormal update rate",
    10: "Abnormal rate of change",
    11: "Root cause not known",
    12: "Bad intelligent device or component",
    13: "Out of calibration",
    14: "Special instructions",
    15: "Data valid but above normal operating range — least severe",
    16: "Data valid but above normal operating range — moderately severe",
    17: "Data valid but below normal operating range — least severe",
    18: "Data valid but below normal operating range — moderately severe",
    19: "Received network data in error",
    31: "Condition exists",
}


# ---------------------------------------------------------------------------
# SPN + FMI → human-readable error description lookup table.
#
# Key   : (spn: int, fmi: int)
# Value : str  — short error description shown to the operator
#
# Add new entries here by following the same pattern.  Any SPN/FMI pair that
# is not listed will automatically be displayed as "Unknown".
# ---------------------------------------------------------------------------
SPN_FMI_DESCRIPTIONS: Dict[Tuple[int, int], str] = {
    # ── Example entries – replace / extend these with your actual fault codes ──

    # SPN 100 – Engine Oil Pressure
    (100, 1): "Engine oil pressure too low",
    (100, 3): "Engine oil pressure sensor voltage high",
    (100, 4): "Engine oil pressure sensor voltage low",

    # SPN 110 – Engine Coolant Temperature
    (110, 0): "Engine coolant temperature above normal range",
    (110, 3): "Engine coolant temperature sensor voltage high",
    (110, 4): "Engine coolant temperature sensor voltage low",

    # SPN 190 – Engine Speed
    (190, 0): "Engine speed above normal operating range",
    (190, 8): "Engine speed signal abnormal frequency",

    # SPN 91 – Accelerator Pedal Position
    (91, 2):  "Accelerator pedal signal erratic or intermittent",
    (91, 3):  "Accelerator pedal sensor voltage high",
    (91, 4):  "Accelerator pedal sensor voltage low",

    # SPN 1569 – Engine Protection Torque Derate
    (1569, 31): "Engine protection derate active – condition exists",
}


def get_dtc_description(spn: int, fmi: int) -> str:
    """Return the error description for a given SPN/FMI pair, or 'Unknown'."""
    return SPN_FMI_DESCRIPTIONS.get((spn, fmi), "Unknown")


def _lamp_status(byte: int, shift: int) -> str:
    """Extract a 2-bit lamp status field and return its human-readable string."""
    return _LAMP_STATUS.get((byte >> shift) & 0x03, "Off")


def decode_dm1(data: List[int]) -> Dict[str, Any]:
    """
    Decode a DM1 (Active DTCs) J1939 message from PGN 0xFECA.

    Message byte layout (0-indexed, little-endian SPNs):
    • Byte 0  — Lamp status overview
                  bits 1-0 : Red Stop Lamp  (0=off, 1=on, 2=fast-flash, 3=slow-flash)
                  bits 3-2 : Amber Warning Lamp
                  bits 5-4 : Protect Lamp
                  bits 7-6 : Aftertreatment Lamp (AdBlue / exhaust indicator)
    • Byte 1  — Flash lamp status (same bit layout as byte 0); retained but not displayed
    • First DTC (bytes 2–4):
                  bytes 2-3: SPN bits  0-15 (little-endian)
                  byte  4  : bits 7-5 = SPN bits 18-16 ; bits 4-0 = FMI
    • Each additional DTC (5 bytes each, starting at byte 5):
                  bytes +0,+1 : lamp status (same layout as byte 0)
                  bytes +2,+3 : SPN bits 0-15
                  byte  +4   : SPN bits 18-16 (bits 7-5) + FMI (bits 4-0)

    Args:
        data: Raw CAN message bytes as a list of ints.

    Returns:
        Dict with keys:
        • 'lamps'  — dict of lamp names → status strings
        • 'dtcs'   — list of dicts, each with 'spn', 'fmi', 'fmi_desc'
    """
    result: Dict[str, Any] = {
        'lamps': {
            'red_stop':        'Off',
            'amber_warning':   'Off',
            'protect':         'Off',
            'aftertreatment':  'Off',
        },
        'dtcs': [],
    }

    if not data:
        return result

    # --- Lamp status (byte 0) ---
    lamp_byte = data[0]
    result['lamps']['red_stop']       = _lamp_status(lamp_byte, 0)
    result['lamps']['amber_warning']  = _lamp_status(lamp_byte, 2)
    result['lamps']['protect']        = _lamp_status(lamp_byte, 4)
    result['lamps']['aftertreatment'] = _lamp_status(lamp_byte, 6)

    # --- First DTC at bytes 2-4 (need at least 5 bytes total) ---
    idx = 2
    if len(data) >= idx + 3:
        spn_byte0 = data[idx]
        spn_byte1 = data[idx + 1]
        fmi_byte  = data[idx + 2]
        spn = spn_byte0 | (spn_byte1 << 8) | ((fmi_byte >> 5) << 16)
        fmi = fmi_byte & 0x1F
        result['dtcs'].append({
            'spn':        spn,
            'fmi':        fmi,
            'fmi_desc':   FMI_DESCRIPTIONS.get(fmi, f'FMI {fmi}'),
            'error_desc': get_dtc_description(spn, fmi),
        })
        idx += 3  # advance past first DTC

    # --- Additional DTCs: 5-byte groups [2 lamp bytes, 2 SPN bytes, 1 FMI byte] ---
    while idx + 5 <= len(data):  # need bytes idx … idx+4 inclusive (5 bytes total)
        # Bytes idx and idx+1 are per-DTC lamp status — skip them
        spn_byte0 = data[idx + 2]
        spn_byte1 = data[idx + 3]
        fmi_byte  = data[idx + 4]
        spn = spn_byte0 | (spn_byte1 << 8) | ((fmi_byte >> 5) << 16)
        fmi = fmi_byte & 0x1F
        result['dtcs'].append({
            'spn':        spn,
            'fmi':        fmi,
            'fmi_desc':   FMI_DESCRIPTIONS.get(fmi, f'FMI {fmi}'),
            'error_desc': get_dtc_description(spn, fmi),
        })
        idx += 5

    return result
