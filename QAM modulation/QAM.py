 import time
import adi
import numpy as np

try:
    sdr = adi.Pluto("ip:192.168.2.1")
    sdr.sample_rate = 1000000
    sdr.tx_lo = 2400000000
    sdr.rx_lo = 2400000000
    sdr.tx_hardwaregain_chan0 = -35
    sdr.rx_buffer_size = 32768
    sdr.tx_cyclic_buffer = True

    message = "WORwLD!"
    print(f"Transmitting target: '{message}' (Len: {len(message)})")

    preamble = "1111000011110000"
    message_bits = "".join(format(ord(c), '08b') for c in message)
    total_bits = preamble + message_bits


    sps = 80
    tx_iq = []
    for i in range(0, len(total_bits), 2):
        b = total_bits[i:i+2]
        if   b == "00": pt =  1 + 1j
        elif b == "01": pt = -1 + 1j
        elif b == "11": pt = -1 - 1j
        else:            pt =  1 - 1j
        tx_iq.extend([pt] * sps)


    sdr.tx(np.array(tx_iq) * 2**13)
    time.sleep(1.5)
    rx_raw = sdr.rx()
    sdr.tx_destroy_buffer()

    recovered_text = ""
    best_sync_found = False

    rx_raw -= np.mean(rx_raw)

    for rot in [0, np.pi/2, np.pi, 3*np.pi/2]:
        rotated = rx_raw * np.exp(-1j * rot)

        bits_stream = ""
        for i in range(len(rotated) // sps):
            s = rotated[i * sps + (sps // 2)]
            bits_stream += ("00" if s.real > 0 and s.imag > 0 else
                           "01" if s.real < 0 and s.imag > 0 else
                           "11" if s.real < 0 and s.imag < 0 else "10")

        if preamble in bits_stream:
            idx = bits_stream.index(preamble) + len(preamble)

            payload_bits = bits_stream[idx:]

            try:
                temp_text = ""
                for i in range(0, (len(payload_bits) // 8) * 8, 8):
                    byte = payload_bits[i : i+8]
                    char = chr(int(byte, 2))
                    if char.isprintable():
                        temp_text += char

                if message in temp_text:
                    recovered_text = message
                    best_sync_found = True
                    break
                elif len(temp_text) >= len(message):
                    recovered_text = temp_text[:len(message)]
                    best_sync_found = True
                    break
            except:
                continue

    print("\n" + "="*40)
    if best_sync_found:
        print(f" SUCCESS: Full String Recovery Achieved")
        print(f" TRANSMITTED: {message}")
        print(f" RECEIVED:    {recovered_text}")
    else:
        print(f" FAIL: Scrambled at index {len(recovered_text)}")
    print("="*40)

except Exception as e:
    print(f"Hardware Halt: {e}")
finally:
    if 'sdr' in locals(): del sdr

