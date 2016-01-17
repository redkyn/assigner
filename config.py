import yaml
from collections import UserDict


def config(filename):
    """Get you a brand new config manager"""
    return _Config(filename)


class _Config(UserDict):
    """Context manager for config; automatically saves changes"""
    def __init__(self, filename):
        super().__init__()
        self._filename = filename
        try:
            with open(filename) as f:
                self.data = yaml.safe_load(f)
        except FileNotFoundError:
            pass  # Just make an empty config; create on __exit__()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        with open(self._filename, 'w') as f:
            yaml.dump(self.data, f, indent=2, default_flow_style=False)

        return False  # propagate exceptions from the calling context
