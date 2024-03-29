import subprocess

def get_pc_mtu():
    if subprocess.OS.name == 'nt':  # Windows
        try:
            output = subprocess.check_output(["netsh", "interface", "ipv4", "show", "subinterfaces"]).decode()
            for line in output.splitlines():
                if "MTU" in line:
                    return int(line.split(":")[-1].strip())
        except subprocess.CalledProcessError:
            pass
    else:  # Linux/macOS
        try:
            output = subprocess.check_output(["ifconfig"]).decode()
            for line in output.splitlines():
                if "mtu" in line:
                    return int(line.split()[4])
        except subprocess.CalledProcessError:
            pass
    return None

if __name__ == "__main__":
    pc_mtu = get_pc_mtu()
    print("PC MTU:", pc_mtu, "bytes" if pc_mtu else "Not found")
