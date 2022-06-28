class Config:
    _initialized = False

    _raw_configuration: dict
    _defaults: dict

    def __init__(self):
        self._raw_configuration = {}
        self._defaults = {}
        self._initialized = True

    def __getattr__(self, key):
        if self._initialized and key not in self.__dict__:
            try:
                return self._raw_configuration[key]
            except KeyError:
                return self._defaults.get(key)
        else:
            return self.__dict__[key]

    def __setattr__(self, key, value):
        if self._initialized and key not in self.__dict__:
            self._raw_configuration[key] = value
        else:
            self.__dict__[key] = value

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
