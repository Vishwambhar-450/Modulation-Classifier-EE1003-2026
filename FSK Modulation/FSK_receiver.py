import numpy as np
import adi

# ===================================
# 1. SDR SETUP
# ===================================
sdr = adi.Pluto("ip:192.168.2.1")

sample_rate = 1e6
center_freq = 915e6

sdr.sample_rate = int(sample_rate)
sdr.rx_lo = int(center_freq)
sdr.rx_rf_bandwidth = int(sample_rate)
sdr.rx_buffer_size = 150000
sdr.gain_control_mode_chan0 = "manual"
sdr.rx_hardwaregain_chan0 = 20

print("Receiving...")

# Flush buffer
for _ in range(5):
    sdr.rx()

rx = sdr.rx()

# ===================================
# 2. PARAMETERS
# ===================================
samples_per_bit = 50

preamble = [1,1,1,0,0,0,1,0,1,1,0,1,0,0,1,1]

# ===================================
# 3. DEMODULATION
# ===================================
decoded_bits = []

for i in range(0, len(rx) - samples_per_bit, samples_per_bit):
    chunk = rx[i:i + samples_per_bit]

    spectrum = np.fft.fftshift(np.fft.fft(chunk))
    freqs = np.fft.fftshift(np.fft.fftfreq(len(chunk), 1/sample_rate))

    peak = freqs[np.argmax(np.abs(spectrum))]
    decoded_bits.append(1 if peak > 0 else 0)

# ===================================
# 4. FIND PREAMBLE
# ===================================
sync_found = False

for i in range(len(decoded_bits) - len(preamble)):
    if decoded_bits[i:i + len(preamble)] == preamble:
        sync_found = True

        start = i + len(preamble)

        # ===================================
        # 5. READ LENGTH (8 bits)
        # ===================================
        len_bits = decoded_bits[start:start + 8]

        if len(len_bits) < 8:
            break

        msg_len = int(''.join(map(str, len_bits)), 2)

        # ===================================
        # 6. READ MESSAGE
        # ===================================
        data_start = start + 8
        data_end = data_start + msg_len * 8

        data_bits = decoded_bits[data_start:data_end]

        chars = []
        for j in range(0, len(data_bits), 8):
            byte = data_bits[j:j + 8]
            if len(byte) == 8:
                chars.append(chr(int(''.join(map(str, byte)), 2)))

        received_text = ''.join(chars)

        print("\nReceived Message:")
        print(received_text)

        break  # ✅ only one message

if not sync_found:
    print("Sync not found")
