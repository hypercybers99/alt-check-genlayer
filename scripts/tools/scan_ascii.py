import sys
import os

def check_ascii(filepath):
    with open(filepath, "rb") as f:
        data = f.read()
    non_ascii = []
    for idx, b in enumerate(data):
        if b > 127:
            non_ascii.append((idx, b))
    return non_ascii

def main():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    contracts_dir = os.path.join(root, "contracts")
    failed = False
    for fname in os.listdir(contracts_dir):
        if fname.endswith(".py"):
            fpath = os.path.join(contracts_dir, fname)
            bad = check_ascii(fpath)
            if bad:
                print(f"FAILED ASCII check: {fname} has {len(bad)} non-ASCII bytes. First 5: {bad[:5]}")
                failed = True
            else:
                print(f"PASSED ASCII check: {fname}")
    if failed:
        sys.exit(1)

if __name__ == "__main__":
    main()
