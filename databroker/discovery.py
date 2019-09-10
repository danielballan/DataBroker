class EntrypointEntry(CatalogEntry):
    """
    A catalog entry for an entrypoint.
    """
    def __init__(self, entrypoint):
        self._entrypoint = entrypoint
        self._name = entrypoint.name

    @property
    def name(self):
        return self._name

    def describe(self):
        """Basic information about this entry"""
        return {'name': self._name,
                'module_name': self._entrypoint.module_name,
                'object_name': self._entrypoint.object_name,
                'distro': self._entrypoint.distro,
                'extras': self._entrypoint.extras}

    def get(self):
        """Instantiate the DataSource for the given parameters"""
        return self._entrypoint.load()


class EntrypointsCatalog(Catalog):

    def __init__(self, *args, entrypoints_group='intake.catalogs', **kwargs):
        self._entrypoints_group = entrypoints_group
        super().__init__(*args, **kwargs)

    def _load(self):
        catalogs = entrypoints.get_group_named(self._entrypoints_group)
        self.name = self.name or 'EntrypointsCatalog'
        self.description = (self.description
                            or f'EntrypointsCatalog of {len(catalogs)} catalogs.')
        for name, entrypoint in catalogs.items():
            try:
                self._entries[name] = EntrypointEntry(entrypoint)
            except Exception as e:
                warings.warn(f"Failed to load {name}, {entrypoint}, {e!r}.")


class V0Entry(CatalogEntry):

    def __init__(self, name, *args, **kwargs):
        self._name = name
        super().__init__(*args, **kwargs)

    def get(self):
        # Hide this import here so that
        # importing v2 doesn't import v1 unless we actually use it.
        from databroker import v1
        config = lookup_config(name)
        catalog = v1.from_config(config)  # might return v0, v1, or v2 Broker
        if not hasattr(catalog, 'v2'):
            raise ValueError("The config file could not be parsed for v2-style access.")
        return catalog.v2  # works if catalog is v1-style or v2-style


class V0Catalog(Catalog):
    """
    Build v2.Brokers based on any v0-style configs we can find.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _load(self):
        for name in list_configs():
            self._entries[name] = V0Entry(name)


class MergedCatalog(Catalog):
    """
    A Catalog that merges the entries of a list of catalogs.
    """
    def __init__(self, catalogs, *args, **kwargs):
        self._catalogs = catalogs
        super().__init__(*args, **kwargs)

    def _load(self):
        for catalog in self._catalogs:
            catalog._load()

    def _make_entries_container(self):
        return collections.ChainMap(*(catalog._entries for catalog in self._catalogs))
