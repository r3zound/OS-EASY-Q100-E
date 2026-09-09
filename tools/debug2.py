import sys
sys.path.insert(0, 'tools')
import importlib
import port_microcode_v2
importlib.reload(port_microcode_v2)
from port_microcode_v2 import find_microcodes_in_data

data_q = open(r'third-party-bios/bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin', 'rb').read()
mcs = find_microcodes_in_data(data_q)
print(f'Q100-E: found {len(mcs)} microcodes')
for m in mcs:
    print(f'  0x{m["offset"]:08x}: CPUID {m["cpuid"]} size={m["data_size"]}')
