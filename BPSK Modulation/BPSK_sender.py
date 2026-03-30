import time

import adi
import numpy as np

PLUTO_TX_URI = "usb:1.6.5"
PLUTO_RX_URI = "usb:7.3.5"
SAMPLE_RATE = 1_000_000
CENTER_FREQ = 915_000_000
SAMPLES_PER_SYMBOL = 100
PREAMBLE = "11111111000000001111000000001111"
MAX_MESSAGE_CHARS = 300
REPETITION = 3
TEST_MESSAGE = "HELLejejefjiehfihhhfeuhfuehfrydyrytd6dtye65dyte56ddSK"


def text_to_bits(text: str) -> str:
    return "".join(format(ord(ch), "08b") for ch in text)


def repeat_encode(bits: str, factor: int) -> str:
    return "".join(bit * factor for bit in bits)


def build_bitstream(message: str) -> str:
    if len(message) > MAX_MESSAGE_CHARS:
        raise ValueError(f"Message length {len(message)} exceeds {MAX_MESSAGE_CHARS} characters")
    payload_bits = text_to_bits(message)
    length_bits = format(len(message), "016b")
    return PREAMBLE + repeat_encode(length_bits, REPETITION) + repeat_encode(payload_bits, REPETITION)


def bpsk_modulate(bitstream: str, sps: int) -> np.ndarray:
    phase = 1 + 0j
    symbols = []
    for bit in bitstream:
        if bit == "1":
            phase *= -1
        symbols.append(phase)
    return np.repeat(np.array(symbols, dtype=np.complex64), sps) * (2**13)


def main() -> None:
    sdr = adi.Pluto(PLUTO_TX_URI)
    sdr.sample_rate = SAMPLE_RATE
    sdr.tx_lo = CENTER_FREQ
    sdr.tx_rf_bandwidth = SAMPLE_RATE
    sdr.tx_hardwaregain_chan0 = -10
    sdr.tx_cyclic_buffer = True

    tx_signal = bpsk_modulate(build_bitstream(TEST_MESSAGE), SAMPLES_PER_SYMBOL)
    sdr.tx(tx_signal)

    print(f"Transmitted message: {TEST_MESSAGE}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    sdr.tx_destroy_buffer()


if __name__ == "__main__":
    main()
