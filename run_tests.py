import os
import sys
import pytest


def main():
    script_dir = os.path.dirname(__file__)
    args = [script_dir] + sys.argv[1:]
    pytest.main(args)


if __name__ == "__main__":
    sys.exit(main())
