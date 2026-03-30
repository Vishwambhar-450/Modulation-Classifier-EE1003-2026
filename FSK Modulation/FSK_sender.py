import time
import numpy as np
import adi

# ===================================
# 1. SDR TRANSMITTER SETUP
# ===================================
sdr = adi.Pluto("ip:192.168.2.1")

sample_rate = 1e6
center_freq = 915e6

sdr.sample_rate = int(sample_rate)
sdr.tx_lo = int(center_freq)
sdr.tx_rf_bandwidth = int(sample_rate)
sdr.tx_hardwaregain_chan0 = -10

# ===================================
# 2. MESSAGE
# ===================================
message = "Hello from Plusdnkcshgfiudysgvjcdzxgfdsbfvudegvueftscgdsuyfgdsuhgsdhfgsdyufhdsufgwdyusfgsdfsdhfgsdytufsdbkfguesyfgsdjyfsgdfhygsduyggsyufgsdfgedsyfgsdugfsdybgyuwayfhsjiggtyfsudjkghsduiyhjdksgesuifhgsduirfgdkjgyersuighdfuigtdfxjghrdugheuogh"

# ✅ Better preamble (non-repetitive)
preamble = [1,1,1,0,0,0,1,0,1,1,0,1,0,0,1,1]

# Convert message to bits
msg_bits = [int(b) for b in ''.join(format(ord(c), '08b') for c in message)]

# ✅ Add LENGTH field (8 bits → max 255 chars)
msg_len = len(message)
len_bits = [int(b) for b in format(msg_len, '08b')]

# Final bit stream
bits = preamble + len_bits + msg_bits

# ===================================
# 3. 2-FSK MODULATION
# ===================================
samples_per_bit = 50
f_dev = 60e3

t = np.arange(samples_per_bit) / sample_rate
signal = []

for bit in bits:
    freq = f_dev if bit == 1 else -f_dev
    tone = np.exp(1j * 2 * np.pi * freq * t)
    signal.extend(tone)

tx_signal = np.array(signal)

# Scale for Pluto
tx_signal *= 0.7 * (2**14)

# ===================================
# 4. TRANSMIT CONTINUOUSLY
# ===================================
sdr.tx_cyclic_buffer = True
sdr.tx(tx_signal)

print("Transmitting:")
print(message)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass

sdr.tx_destroy_buffer()
print("Transmission stopped")
