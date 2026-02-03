import subprocess
import argparse
import shlex
import csv
import os
import sys

import matplotlib.pyplot as plt

# ------------------------
# Register addresses
# ------------------------
CSR_ADDR = 0x0
COEF_ADDR = 0x4
OUTCAP_ADDR = 0x8


# ------------------------
# Register Models
# ------------------------
class Csr:
    def __init__(self, csr_bin):
        self.fen   = (csr_bin >> 0) & 0x1
        self.c0en  = (csr_bin >> 1) & 0x1
        self.c1en  = (csr_bin >> 2) & 0x1
        self.c2en  = (csr_bin >> 3) & 0x1
        self.c3en  = (csr_bin >> 4) & 0x1
        self.halt  = (csr_bin >> 5) & 0x1
        self.sts   = (csr_bin >> 6) & 0x3
        self.ibcnt = (csr_bin >> 8) & 0xff
        self.ibovf = (csr_bin >> 16) & 0x1
        self.ibclr = (csr_bin >> 17) & 0x1
        self.tclr  = (csr_bin >> 18) & 0x1
        self.rnd   = (csr_bin >> 19) & 0x3
        self.icoef = (csr_bin >> 21) & 0x1
        self.icap  = (csr_bin >> 22) & 0x1
        self.rsvd  = (csr_bin >> 23) & 0x1FF

    def encode(self):
        return (
            (self.fen   << 0)  |
            (self.c0en  << 1)  |
            (self.c1en  << 2)  |
            (self.c2en  << 3)  |
            (self.c3en  << 4)  |
            (self.halt  << 5)  |
            (self.sts   << 6)  |
            (self.ibcnt << 8)  |
            (self.ibovf << 16) |
            (self.ibclr << 17) |
            (self.tclr  << 18) |
            (self.rnd   << 19) |
            (self.icoef << 21) |
            (self.icap  << 22)
        )


class Coef:
    def __init__(self, coef_bin):
        self.c0 = (coef_bin >> 0) & 0xff
        self.c1 = (coef_bin >> 8) & 0xff
        self.c2 = (coef_bin >> 16) & 0xff
        self.c3 = (coef_bin >> 24) & 0xff

    def encode(self):
        return (
            (self.c0 << 0) |
            (self.c1 << 8) |
            (self.c2 << 16) |
            (self.c3 << 24)
        )


class Outcap:
    def __init__(self, outcap_bin):
        self.hcap = (outcap_bin >> 0) & 0xff
        self.lcap = (outcap_bin >> 8) & 0xff
        self.rsvd = (outcap_bin >> 16) & 0xffff

    def encode(self):
        return (self.hcap << 0) | (self.lcap << 8)



# ------------------------
# UART Debugger Wrapper
# ------------------------
class Model:
    def __init__(self, path):
        self.path = path

    def cmd(self, args):
        out = subprocess.check_output(
            shlex.split(f"{self.path} {args}")
        ).decode().strip()
        return out

    def reset(self):
        self.cmd("com --action reset")

    def enable(self):
        self.cmd("com --action enable")

    def disable(self):
        self.cmd("com --action disable")

    def read_reg(self, addr):
        return int(self.cmd(f"cfg --address {addr}"), 0)

    def write_reg(self, addr, val):
        self.cmd(f"cfg --address {addr} --data {hex(val)}")

    def drive_signal(self, val):
        return int(self.cmd(f"sig --data {hex(val)}"), 0)

    def get_csr(self):
        return Csr(self.read_reg(CSR_ADDR))

    def set_csr(self, csr):
        self.write_reg(CSR_ADDR, csr.encode())

    def get_coef(self):
        return Coef(self.read_reg(COEF_ADDR))

    def set_coef(self, coef):
        self.write_reg(COEF_ADDR, coef.encode())

    def get_outcap(self):
        return Outcap(self.read_reg(OUTCAP_ADDR))


# ------------------------
# Utilities
# ------------------------
def twos_comp(x):
    return ((x & 0x7F) - (x & 0x80)) / 64


# ------------------------
# Config Loader
# ------------------------
def load_cfg(uad, cfg_file):
    print(f"\n[CFG] Loading {cfg_file}")
    csr = uad.get_csr()
    csr.halt = 1
    uad.set_csr(csr)

    coef = uad.get_coef()

    with open(cfg_file) as f:
        for row in csv.DictReader(f):
            idx = row['coef']
            setattr(csr, f'c{idx}en', int(row['en'], 0))
            setattr(coef, f'c{idx}', int(row['value'], 0))

    uad.set_coef(coef)
    csr.halt = 0
    uad.set_csr(csr)


# ------------------------
# Testcases
# ------------------------
def tc1_global_enable(uad):
    print("\n[TC1] Global Enable / Disable")
    uad.reset()
    uad.disable()

    try:
        uad.read_reg(CSR_ADDR)
        print("FAIL: CSR accessible when disabled")
        return False
    except:
        print("PASS: CSR blocked when disabled")

    uad.enable()
    uad.read_reg(CSR_ADDR)
    print("PASS: CSR accessible after enable")
    return True


def tc2_por(uad, por_file):
    print("\n[TC2] POR Register Values")
    uad.reset()

    csr = uad.get_csr()
    coef = uad.get_coef()
    outcap = uad.get_outcap()

    passed = True
    with open(por_file) as f:
        for row in csv.DictReader(f):
            reg = {'csr': csr, 'coef': coef, 'outcap': outcap}[row['register']]
            act = getattr(reg, row['field'])
            exp = int(row['value'], 0)
            if act != exp:
                print(f"FAIL: {row['register']}.{row['field']} exp={hex(exp)} got={hex(act)}")
                passed = False

    if passed:
        print("PASS: All POR values match")
    return passed


def tc3_input_buffer(uad):
    print("\n[TC3] Input Buffer Overflow & Clear")
    csr = uad.get_csr()
    csr.halt = 1
    uad.set_csr(csr)

    csr = uad.get_csr()
    if csr.sts != 1:
        print("FAIL: IP did not enter HALTED state")
        return False

    for _ in range(300):
        uad.drive_signal(0x10)

    csr = uad.get_csr()
    if csr.ibcnt != 255 or csr.ibovf != 1:
        print("FAIL: Buffer overflow incorrect")
        return False

    csr.ibclr = 1
    uad.set_csr(csr)

    csr = uad.get_csr()
    if csr.ibcnt != 0:
        print("FAIL: Buffer not cleared")
        return False

    print("PASS: Input buffer overflow & clear OK")
    return True


def tc4_bypass(uad):
    print("\n[TC4] Filter Bypass")
    csr = uad.get_csr()
    csr.fen = 0
    uad.set_csr(csr)

    for v in [0x10, 0x20, 0x30]:
        if uad.drive_signal(v) != v:
            print("FAIL: Output does not match input")
            return False

    print("PASS: Bypass works correctly")
    return True


def tc5_signal_processing(uad, vec_file, plot=False):
    print("\n[TC5] Signal Processing")
    csr = uad.get_csr()
    csr.fen = 1
    csr.tclr = 1
    csr.ibclr = 1
    uad.set_csr(csr)

    sig_in, sig_out = [], []
    with open(vec_file) as f:
        for l in f:
            sig_in.append(int(l, 0))

    for s in sig_in:
        sig_out.append(uad.drive_signal(s))

    if plot:
        plt.plot([twos_comp(x) for x in sig_in], label="Input", drawstyle="steps-post")
        plt.plot([twos_comp(x) for x in sig_out], label="Output", drawstyle="steps-post")
        plt.legend()
        plt.title("Signal Input vs Output")
        plt.show()

    print("PASS: Signal processing executed")
    return sig_out


# ------------------------
# Main
# ------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-i', '--instance',
        required=True,
        choices=['golden','impl0','impl1','impl2','impl3','impl4','impl5']
    )
    parser.add_argument(
        '-t', '--test',
        required=True,
        choices=['dump','set','por','config','drive']
    )
    parser.add_argument('-v', '--value', help='value for set/drive')
    parser.add_argument('-f', '--file', help='input file (por.csv, p4.cfg, sqr.vec)')
    parser.add_argument('-p', '--plot', action='store_true')
    args = parser.parse_args()

    exe = f"./{args.instance}.exe"
    if not os.path.exists(exe):
        print(f"ERROR: {exe} not found")
        sys.exit(1)

    uad = Model(exe)

    # -------------------------
    # TEST DISPATCH
    # -------------------------
    if args.test == 'dump':
        csr = uad.get_csr()
        coef = uad.get_coef()
        outcap = uad.get_outcap()
        print("CSR   :", vars(csr))
        print("COEF  :", vars(coef))
        print("OUTCAP:", vars(outcap))

    elif args.test == 'set':
        if args.value is None:
            raise ValueError("set requires -v VALUE")
        uad.drive_signal(int(args.value, 0))

    elif args.test == 'por':
        if args.file is None:
            raise ValueError("por requires -f por.csv")
        tc2_por(uad, args.file)

    elif args.test == 'config':
        if args.file is None:
            raise ValueError("config requires -f pX.cfg")
        load_cfg(uad, args.file)

    elif args.test == 'drive':
        if args.file is None:
            raise ValueError("drive requires -f sqr.vec")
        tc5_signal_processing(uad, args.file, args.plot)

if __name__ == '__main__':
    main()
