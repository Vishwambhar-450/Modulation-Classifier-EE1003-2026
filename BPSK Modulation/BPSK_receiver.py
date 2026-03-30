import numpy as np
import adi


PLUTO_RX_URI = "ip:192.168.2.1"
SAMPLE_RATE = 1_000_000
CENTER_FREQ = 915_000_000
SAMPLES_PER_SYMBOL = 100
PREAMBLE = "11111111000000001111000000001111"
MAX_MESSAGE_CHARS = 300
REPETITION = 3

# ===================================
# 1. SDR SETUP
# ===================================
sdr = adi.Pluto(PLUTO_RX_URI)

sample_rate = SAMPLE_RATE
center_freq = CENTER_FREQ

sdr.sample_rate = int(sample_rate)
sdr.rx_lo = int(center_freq)
sdr.rx_rf_bandwidth = int(sample_rate)
sdr.gain_control_mode_chan0 = "manual"
sdr.rx_hardwaregain_chan0 = 40

# ===================================
# 2. BPSK PARAMETERS
# ===================================
samples_per_symbol = SAMPLES_PER_SYMBOL
repeat = REPETITION
preamble = PREAMBLE

sync_bits = preamble + ("0" * (16 * repeat))
sdr.rx_buffer_size = 300000

print("Receiving...")

def decode_capture(rx):
    best_text = None
    best_score = -1.0
    coded_length_size = 16 * repeat
    needed_symbols = len(sync_bits)
    preamble_score_min = max(20, len(preamble) - 4)

    for offset in range(samples_per_symbol):
        usable = (len(rx) - offset) // samples_per_symbol
        if usable < needed_symbols:
            continue

        symbol_stream = rx[offset:offset + usable * samples_per_symbol].reshape(-1, samples_per_symbol).mean(axis=1)
        diff = symbol_stream[1:] * np.conj(symbol_stream[:-1])
        bits = "".join("1" if sample.real < 0 else "0" for sample in diff)
        best_start = -1
        best_local = -1

        for i in range(len(bits) - len(preamble)):
            local = sum(bits[i + j] == preamble[j] for j in range(len(preamble)))
            if local > best_local:
                best_local = local
                best_start = i

        if best_local < preamble_score_min:
            continue

        score = float(best_local)
        decoded_bits = bits[best_start:]
        coded_len_bits = decoded_bits[len(preamble):len(preamble) + coded_length_size]
        length_bits = []
        for i in range(0, len(coded_len_bits), repeat):
            group = coded_len_bits[i:i + repeat]
            length_bits.append("1" if group.count("1") > repeat // 2 else "0")

        msg_len = int("".join(length_bits), 2)
        if msg_len <= 0 or msg_len > MAX_MESSAGE_CHARS:
            continue

        data_start = len(preamble) + coded_length_size
        data_end = data_start + (msg_len * 8 * repeat)
        if len(decoded_bits) < data_end:
            continue
        coded_data_bits = decoded_bits[data_start:data_end]

        data_bits = []
        for i in range(0, len(coded_data_bits), repeat):
            group = coded_data_bits[i:i + repeat]
            data_bits.append("1" if group.count("1") > repeat // 2 else "0")

        chars = []
        raw_bits = "".join(data_bits)
        for i in range(0, msg_len * 8, 8):
            byte = raw_bits[i:i + 8]
            if len(byte) == 8:
                chars.append(chr(int(byte, 2)))

        text = "".join(chars)
        if text.isprintable() and score > best_score:
            best_text = text
            best_score = score

    return best_text


# Flush buffer
for _ in range(5):
    sdr.rx()

best_text = None
for _ in range(8):
    rx = np.concatenate((np.asarray(sdr.rx()), np.asarray(sdr.rx())))
    best_text = decode_capture(rx)
    if best_text is not None:
        break

# ===================================
# 4. PRINT MESSAGE
# ===================================
if best_text is None:
    print("Sync not found")
else:
    print("\nReceived Message:")
    print(best_text)
