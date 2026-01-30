import subprocess
import argparse
import shlex
import csv
import os

import numpy as np
import matplotlib.pyplot as plt

CSR_ADDR = 0x0
COEF_ADDR = 0x4
OUTCAP_ADDR = 0x8

UAD_PATH = './uad'

class Csr():
    def __init__(self, csr_bin):
        self.fen = (csr_bin >> 0) & 0x1
        self.c0en = (csr_bin >> 1) & 0x1
        self.c1en = (csr_bin >> 2) & 0x1
        self.c2en = (csr_bin >> 3) & 0x1
        self.c3en = (csr_bin >> 4) & 0x1
        self.halt = (csr_bin >> 5) & 0x1
        self.sts = (csr_bin >> 6) & 0x3
        self.ibcnt = (csr_bin >> 8) & 0xff
        self.ibovf = (csr_bin >> 16) & 0x1
        self.ibclr = (csr_bin >> 17) & 0x1
        self.tclr = (csr_bin >> 18) & 0x1
        self.rnd = (csr_bin >> 19) & 0x3
        self.icoef = (csr_bin >> 21) & 0x1
        self.icap = (csr_bin >> 22) & 0x1
        self.rsvd = (csr_bin >> 23) & 0xffff

    def encode(self):
        return (
            ((self.fen & 0x1) << 0) |
            ((self.c0en & 0x1) << 1) |
            ((self.c1en & 0x1) << 2) |
            ((self.c2en & 0x1) << 3) |
            ((self.c3en & 0x1) << 4) |
            ((self.halt & 0x1) << 5) |
            ((self.sts & 0x3) << 6) |
            ((self.ibcnt & 0xff) << 8) |
            ((self.ibovf & 0x1) << 16) |
            ((self.ibclr & 0x1) << 17) |
            ((self.tclr & 0x1) << 18) |
            ((self.rnd & 0x3) << 19) |
            ((self.icoef & 0x1) << 21) |
            ((self.icap & 0x1) << 22) |
            ((self.rsvd & 0x3ff) << 23)
        )
    
    def __str__(self):
        str_rep = "CSR Register Content\n"
        str_rep += f"fen   : {hex(self.fen)}\n"
        str_rep += f"c0en  : {hex(self.c0en)}\n"
        str_rep += f"c1en  : {hex(self.c1en)}\n"
        str_rep += f"c2en  : {hex(self.c2en)}\n"
        str_rep += f"c3en  : {hex(self.c3en)}\n"
        str_rep += f"halt  : {hex(self.halt)}\n"
        str_rep += f"sts   : {hex(self.sts)}\n"
        str_rep += f"ibcnt : {hex(self.ibcnt)}\n"
        str_rep += f"ibovf : {hex(self.ibovf)}\n"
        str_rep += f"ibclr : {hex(self.ibclr)}\n"
        str_rep += f"tclr  : {hex(self.tclr)}\n"
        str_rep += f"rnd   : {hex(self.rnd)}\n"
        str_rep += f"icoef : {hex(self.icoef)}\n"
        str_rep += f"icap  : {hex(self.icap)}\n"
        str_rep += f"rsvd  : {hex(self.rsvd)}"
        return str_rep
    
class Coef():
    def __init__(self, coef_bin):
        self.c0 = (coef_bin >> 0) & 0xff
        self.c1 = (coef_bin >> 8) & 0xff
        self.c2 = (coef_bin >> 16) & 0xff
        self.c3 = (coef_bin >> 24) & 0xff

    def encode(self):
        return (
            ((self.c0 & 0xff) << 0) |
            ((self.c1 & 0xff) << 8) |
            ((self.c2 & 0xff) << 16) |
            ((self.c3 & 0xff) << 24)
        )
    
    def __str__(self):
        str_rep = "COEF Register Content\n"
        str_rep += f"c0 : {hex(self.c0)}\n"
        str_rep += f"c1 : {hex(self.c1)}\n"
        str_rep += f"c2 : {hex(self.c2)}\n"
        str_rep += f"c3 : {hex(self.c3)}"
        return str_rep
    
class Outcap():
    def __init__(self, outcap_bin):
        self.hcap = (outcap_bin >> 0) & 0xff
        self.lcap = (outcap_bin >> 8) & 0xff
        self.rsvd = (outcap_bin >> 16) & 0xffff

    def encode(self):
        return (
            ((self.hcap & 0xff) << 0) |
            ((self.lcap & 0xff) << 8) |
            ((self.rsvd & 0xff) << 16)
        )
    
    def __str__(self):
        str_rep = "OUTCAP Register Content\n"
        str_rep += f"hcap : {hex(self.hcap)}\n"
        str_rep += f"lcap : {hex(self.lcap)}\n"
        str_rep += f"rsvd : {hex(self.rsvd)}"
        return str_rep

class Uad():
    def __init__(self):
        self.csr = None
        self.coef = None
        self.outcap = None

    def reset(self):
        return os.system(f'{UAD_PATH} com --action reset')

    def disable(self):
        return os.system(f'{UAD_PATH} com --action disable')

    def enable(self):
        return os.system(f'{UAD_PATH} com --action enable')
    
    def drive_signal(self, sig_in):
        sig_out = subprocess.check_output(shlex.split(f'{UAD_PATH} sig --data {hex(sig_in)}')).decode()
        return int(sig_out, 0)

    def get_csr(self):
        csr_bin = subprocess.check_output(shlex.split(f'{UAD_PATH} cfg --address {CSR_ADDR}')).decode()
        csr_bin = int(csr_bin, 0)
        self.csr = Csr(csr_bin)
        return self.csr

    def get_coef(self):
        coef_bin = subprocess.check_output(shlex.split(f'{UAD_PATH} cfg --address {COEF_ADDR}')).decode()
        coef_bin = int(coef_bin, 0)
        self.coef = Coef(coef_bin)
        return self.coef

    def get_outcap(self):
        outcap_bin = subprocess.check_output(shlex.split(f'{UAD_PATH} cfg --address {OUTCAP_ADDR}')).decode()
        outcap_bin = int(outcap_bin, 0)
        self.outcap = Outcap(outcap_bin)
        return self.outcap

    def set_csr(self):
        exit_code = os.system(f'{UAD_PATH} cfg --address {CSR_ADDR} --data {hex(self.csr.encode())}')
        self.get_csr()
        return exit_code

    def set_coef(self):
        exit_code = os.system(f'{UAD_PATH} cfg --address {COEF_ADDR} --data {hex(self.coef.encode())}')
        self.get_coef()
        return exit_code

    def set_outcap(self):
        exit_code = os.system(f'{UAD_PATH} cfg --address {OUTCAP_ADDR} --data {hex(self.outcap.encode())}')
        self.get_outcap()
        return exit_code
    
    def get_reg(self, reg_name):
        if reg_name == 'csr':
            return self.get_csr()

        elif reg_name == 'coef':
            return self.get_coef()

        elif reg_name == 'outcap':
            return self.get_outcap()
        
    def set_reg(self, reg_name):
        if reg_name == 'csr':
            return self.set_csr()

        elif reg_name == 'coef':
            return self.set_coef()

        elif reg_name == 'outcap':
            return self.set_outcap()
        
def twos_comp(num):
    return ((num & 0x7F) + (-128 if num >> 7 == 0x1 else 0)) / 64
    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--instance', choices=['golden', 'impl0', 'impl1', 'impl2', 'impl3', 'impl4'])
    parser.add_argument('-t', '--test', choices=['dump', 'set', 'por', 'config', 'drive'], help='the tests that can be run with this script')
    parser.add_argument('-v', '--value', help='register field value to set')
    parser.add_argument('-f', '--file', help='path to csv file with the expected por register values')
    parser.add_argument('-p', '--plot', action='store_true', help='include this flag to plot when driving')
    args = parser.parse_args()

    UAD_PATH = f'./insts/{args.instance}'
    uad = Uad()

    if args.test == 'dump':
        print(uad.get_csr(), end='\n\n')
        print(uad.get_coef(), end='\n\n')
        print(uad.get_outcap(), end='\n\n')

    elif args.test == 'set':
        temp = args.value.split('=')
        reg_path = temp[0].split('.')
        value = temp[1]
        
        reg = uad.get_reg(reg_path[0])
        setattr(reg, reg_path[1], int(value, 0))
        uad.set_reg(reg_path[0])
        
        print(reg)

    elif args.test == 'config':
        csr = uad.get_csr()
        csr.halt=1
        uad.set_csr()

        with open(args.file, 'r') as f:
            coef = uad.get_coef()
            csr = uad.get_csr()

            for row in csv.DictReader(f):
                setattr(csr, f'c{row["coef"]}en', int(row['en'], 0))
                setattr(coef, f'c{row["coef"]}', int(row['value'], 0))

        csr.halt=0
        uad.set_coef()
        uad.set_csr()

    elif args.test == 'drive':
        csr = uad.get_csr()
        csr.fen=1
        csr.tclr=1
        csr.ibclr=1
        uad.set_csr()

        sig_in = []
        sig_out = []
        with open(args.file, 'r') as f:
            for line in f.readlines():
                sig_in.append(int(line, 0))
        
        for samp_in in sig_in:
            sig_out.append(uad.drive_signal(samp_in))

        with open('output.vec', 'w') as f:
            for samp_out in sig_out:
                f.write(f'{twos_comp(samp_out)}\n')

        if args.plot:
            plt.plot([i for i in range(len(sig_in))], [twos_comp(samp) for samp in sig_in], label='Input', drawstyle='steps-post')
            plt.plot([i for i in range(len(sig_in))], [twos_comp(samp) for samp in sig_out], label='Output', drawstyle='steps-post')
            plt.xlabel('Sample')
            plt.ylabel('Value')
            plt.title('Signal Input and Output')
            plt.legend()
            plt.show()
    
    elif args.test == 'por':
        uad.reset()
        csr = uad.get_csr()
        coef = uad.get_coef()
        outcap = uad.get_outcap()

        with open(args.file, 'r') as f:
            for row in csv.DictReader(f):
                reg = None
                if row['register'] == 'csr':
                    reg = csr

                elif row['register'] == 'coef':
                    reg = coef

                elif row['register'] == 'outcap':
                    reg = outcap

                actual_value = getattr(reg, row['field'])
                expected_value = int(row['value'], 0)
                if actual_value != expected_value:
                    print(f'field {row["register"]}.{row["field"]} does not match. expected: {hex(expected_value)}, got {hex(actual_value)}')

if __name__ == '__main__':
    main()
