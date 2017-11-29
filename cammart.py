import collections
import json
from urllib import parse

import pip
import requests
import yaml
from appdirs import user_config_dir, site_config_dir

from . import manager
from . import venvs

user_package_registry = user_config_dir('xicam/packages.yml')
site_package_registry = site_config_dir('xicam/packages.yml')

def install(name: str):
    """
    Install a Xi-cam plugin package by querying the Xi-cam package repository with REST.

    Packages are installed into the currently active virtualenv

    Parameters
    ----------
    name : str
        The package name to be installed.
    """
    # TODO: test if installed
    # TODO: check if package is in repo

    # Get install plugin package information from cam-mart repository
    o = requests.get(f'http://127.0.0.1:5000/pluginpackages/{name}')

    # Get the uri from the plugin package information
    uri = parse.urlparse(json.loads(o.content)["installuri"])

    failure = True

    # Install from the uri
    if uri.scheme == 'pipgit':  # Clones a git repo and installs with pip
        failure = pip.main(["install", 'git+https://' + ''.join(uri[1:]), "--prefix", venvs.current_environment])
    elif uri.scheme == 'pip':
        failure = pip.main(["install", ''.join(uri[1:]), "--prefix", venvs.current_environment])
    elif uri.scheme == 'conda':
        raise NotImplementedError

    if not failure:
        pkg_registry[name] = uri.scheme

    manager.collectPlugins()


def uninstall(name: str):
    failure = True
    if name in pkg_registry:
        scheme = pkg_registry[name]
        if scheme in ['pipgit', 'pip']:
            failure = pip.main(['uninstall', name])
        elif scheme == 'conda':
            raise NotImplementedError
    else:
        # TODO: Handle if name is not in the registry
        pass

    if not failure:
        del pkg_registry[name]

    return not failure


class pkg_registry(collections.MutableMapping):
    def __init__(self):
        self._store = dict()
        self.update(self._store)  # use the free update to set keys
        self.load()
        self.save()

    def __getitem__(self, key):
        return self._store[self.__keytransform__(key)]

    def __setitem__(self, key, value):
        self._store[self.__keytransform__(key)] = value
        self.save()

    def __delitem__(self, key):
        del self._store[self.__keytransform__(key)]
        self.save()

    def __iter__(self):
        return iter(self._store)

    def __len__(self):
        return len(self._store)

    def __keytransform__(self, key):
        return key

    def load(self):
        try:
            with open(user_package_registry, 'r') as f:
                self._store = yaml.load(f.read())
        except FileNotFoundError:
            pass

    def save(self):
        with open(user_package_registry, 'w') as f:
            f.write(yaml.dump(self._store))


pkg_registry = pkg_registry()

# def check_registry():
#
# def scan_for_unregistered():
#     unregistered_packages = {}
#     pkgs = pip.get_installed_distributions()
#     for pkg in pkgs:
#         targets = [pathlib.Path(pkg._provider.egg_info) / 'installed-files.txt',
#                    pathlib.Path(pkg._provider.egg_info) / 'RECORD']
#         for target in targets:
#             if target.exists():
#                 with open(str(target),'r') as f:
#                     if 'yapsy-plugin' in f.read():
#                         unregistered_packages[str(pathlib.Path(pkg.location)/pkg.key)] = pkg.project_name
#
#     return unregistered_packages