class Config:
    _raw_configuration: dict
    _defaults: dict

    def __init__(self):
        self._raw_configuration = {}
        self._defaults = {}

    def __getattr__(self, key):
        try:
            return self._raw_configuration[key]
        except KeyError:
            return self._defaults.get(key)

    def values(self):
        return {**self._defaults, **self._raw_configuration}

    def clone(self):
        clone = Config()
        clone.add_defaults(**self._defaults)
        clone.set_data(self._raw_configuration)
        return clone

    def set_data(self, raw):
        self._raw_configuration = raw

    def add_defaults(self, **kwargs):
        self._defaults = {**self._defaults, **kwargs}
