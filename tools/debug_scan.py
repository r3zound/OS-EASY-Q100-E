import sys
sys.path.insert(0, 'tools')
from port_microcode_v2 import find_microcodes_in_data
data = open(r'third-party-bios/bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin', 'rb').read()
mcs = find_microcodes_in_data(data)
print(f'找到 {len(mcs)} 个 microcode')
for m in mcs[:5]:
    print(f'  0x{m["offset"]:08x}: CPUID {m["cpuid"]} rev={m["revision"]} size={m["aligned_size"]} data={m["data_size"]}')
