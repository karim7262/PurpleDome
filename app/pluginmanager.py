#!/usr/bin/env python3
""" Manage plugins """

from glob import glob
import os
import re
from typing import Optional
import straight.plugin  # type: ignore


from plugins.base.plugin_base import BasePlugin
from plugins.base.attack import AttackPlugin
from plugins.base.machinery import MachineryPlugin
from plugins.base.ssh_features import SSHFeatures
from plugins.base.sensor import SensorPlugin

from plugins.base.vulnerability_plugin import VulnerabilityPlugin
from app.interface_sfx import CommandlineColors
from app.attack_log import AttackLog

# from app.interface_sfx import CommandlineColors

sections = [{"name": "Vulnerabilities",
             "subclass": VulnerabilityPlugin},
            {"name": "Machinery",
             "subclass": MachineryPlugin},
            {"name": "Attack",
             "subclass": AttackPlugin},
            {"name": "Sensors",
             "subclass": SensorPlugin},
            ]


class PluginManager():
    """ Manage plugins """

    def __init__(self, attack_logger: AttackLog, basedir: Optional[str] = None):
        """

        @param attack_logger: The attack logger to use
        @param basedir: optional base directory for plugins. A glob
        """
        if basedir is None:
            self.base = "plugins/**/*.py"
        else:
            self.base = basedir
        self.attack_logger = attack_logger

    def get_plugins(self, subclass, name_filter: Optional[list[str]] = None) -> list[BasePlugin]:
        """ Returns a list plugins matching specified criteria


        :param subclass: The subclass to use to filter plugins. Currently: AttackPlugin, MachineryPlugin, SensorPlugin, VulnerabilityPlugin
        :param name_filter: an optional list of names to select the plugins by
        :return: A list of instantiated plugins
        """

        res = []

        def get_handlers(a_plugin):
            return a_plugin.produce()

        plugin_dirs = set()
        for a_glob in glob(self.base, recursive=True):
            plugin_dirs.add(os.path.dirname(a_glob))

        for a_dir in plugin_dirs:
            plugins = straight.plugin.load(a_dir, subclasses=subclass)

            handlers = get_handlers(plugins)

            for plugin in handlers:
                plugin.set_logger(self.attack_logger)
                if name_filter is None:
                    res.append(plugin)
                else:
                    names = set(plugin.get_names())
                    intersection = names.intersection(name_filter)
                    if len(intersection):
                        res.append(plugin)
        return res

    def count_caldera_requirements(self, subclass, name_filter=None) -> int:
        """ Count the plugins matching the filter that have caldera requirements """

        # So far it only supports attack plugins. Maybe this will be extended to other plugin types later.
        assert subclass == AttackPlugin

        plugins = self.get_plugins(subclass, name_filter)
        res = 0
        for plugin in plugins:
            if plugin.needs_caldera():
                res += 1

        return res

    def count_metasploit_requirements(self, subclass, name_filter=None) -> int:
        """ Count the plugins matching the filter that have metasploit requirements """

        # So far it only supports attack plugins. Maybe this will be extended to other plugin types later.
        assert subclass == AttackPlugin

        plugins = self.get_plugins(subclass, name_filter)
        res = 0
        for plugin in plugins:
            if plugin.needs_metasploit():
                res += 1

        return res

    def print_list(self):
        """ Print a pretty list of all available plugins """

        for section in sections:
            print(f'\t\t{section["name"]}')
            plugins = self.get_plugins(section["subclass"])
            for plugin in plugins:
                print(f"Name: {plugin.get_name()}")
                print(f"Description: {plugin.get_description()}")
                print("\t")

    def is_ttp_wrong(self, ttp):
        """ Checks if a ttp is a valid ttp """
        if ttp is None:
            return True

        # Short: T1234
        if re.match("^T\\d{4}$", ttp):
            return False

        # Detailed: T1234.123
        if re.match("^T\\d{4}\\.\\d{3}$", ttp):
            return False

        # Unkown: ???
        if ttp == "???":
            return False

        # Multiple TTPs in this attack
        if ttp == "multiple":
            return False

        return True

    def check(self, plugin):
        """ Checks a plugin for valid implementation

        @returns: A list of issues
        """

        issues = []

        # Base functionality for all plugin types

        if plugin.name is None:
            report = f"No name for plugin: in {plugin.plugin_path}"
            issues.append(report)

        if plugin.description is None:
            report = f"No description in plugin: {plugin.get_name()} in {plugin.plugin_path}"
            issues.append(report)

        # Sensors
        if issubclass(type(plugin), SensorPlugin):
            # essential methods: collect
            if plugin.collect.__func__ is SensorPlugin.collect:
                report = f"Method 'collect' not implemented in {plugin.get_name()} in {plugin.plugin_path}"
                issues.append(report)

        # Attacks
        if issubclass(type(plugin), AttackPlugin):
            # essential methods: run
            if plugin.run.__func__ is AttackPlugin.run:
                report = f"Method 'run' not implemented in {plugin.get_name()} in {plugin.plugin_path}"
                issues.append(report)
            if self.is_ttp_wrong(plugin.ttp):
                report = f"Attack plugins need a valid ttp number (either T1234, T1234.222 or ???)  {plugin.get_name()} uses {plugin.ttp} in {plugin.plugin_path}"
                issues.append(report)

        # Machinery
        if issubclass(type(plugin), MachineryPlugin):
            # essential methods: get_ip, get_state, up. halt, create, destroy
            if plugin.get_state.__func__ is MachineryPlugin.get_state:
                report = f"Method 'get_state' not implemented in {plugin.get_name()} in {plugin.plugin_path}"
                issues.append(report)
            if (plugin.get_ip.__func__ is MachineryPlugin.get_ip) or (plugin.get_ip.__func__ is SSHFeatures.get_ip):
                report = f"Method 'get_ip' not implemented in {plugin.get_name()} in {plugin.plugin_path}"
                issues.append(report)
            if plugin.up.__func__ is MachineryPlugin.up:
                report = f"Method 'up' not implemented in {plugin.get_name()} in {plugin.plugin_path}"
                issues.append(report)
            if plugin.halt.__func__ is MachineryPlugin.halt:
                report = f"Method 'halt' not implemented in {plugin.get_name()} in {plugin.plugin_path}"
                issues.append(report)
            if plugin.create.__func__ is MachineryPlugin.create:
                report = f"Method 'create' not implemented in {plugin.get_name()} in {plugin.plugin_path}"
                issues.append(report)
            if plugin.destroy.__func__ is MachineryPlugin.destroy:
                report = f"Method 'destroy' not implemented in {plugin.get_name()} in {plugin.plugin_path}"
                issues.append(report)

        # Vulnerabilities
        if issubclass(type(plugin), VulnerabilityPlugin):
            # essential methods: start, stop
            if plugin.start.__func__ is VulnerabilityPlugin.start:
                report = f"Method 'start' not implemented in {plugin.get_name()} in {plugin.plugin_path}"
                issues.append(report)
            if plugin.stop.__func__ is VulnerabilityPlugin.stop:
                report = f"Method 'stop' not implemented in {plugin.get_name()} in {plugin.plugin_path}"
                issues.append(report)
            if self.is_ttp_wrong(plugin.ttp):
                report = f"Vulnerability plugins need a valid ttp number (either T1234, T1234.222 or ???)  {plugin.get_name()} uses {plugin.ttp} in {plugin.plugin_path}"
                issues.append(report)

        return issues

    def print_check(self):
        """ Iterates through all installed plugins and verifies them """

        names = {}
        cnames = {}

        issues = []
        for section in sections:
            # print(f'\t\t{section["name"]}')
            plugins = self.get_plugins(section["subclass"])

            for plugin in plugins:
                # print(f"Checking: {plugin.get_name()}")
                # Check for duplicate names
                name = plugin.get_name()
                if name in names:
                    report = f"Name duplication: {name} is used in {names[name]} and {plugin.plugin_path}"
                    issues.append(report)
                    self.attack_logger.vprint(f"{CommandlineColors.BACKGROUND_RED}{report}{CommandlineColors.ENDC}", 0)
                names[name] = plugin.plugin_path

                # Check for duplicate class names
                name = type(plugin).__name__
                if name in cnames:
                    report = f"Class name duplication: {name} is used in {cnames[name]} and {plugin.plugin_path}"
                    issues.append(report)
                    self.attack_logger.vprint(f"{CommandlineColors.BACKGROUND_RED}{report}{CommandlineColors.ENDC}", 0)
                cnames[name] = type(plugin)

                # Deep checks

                results = self.check(plugin)

                if len(results) > 0:
                    for result in results:
                        print(f"* Issue: {result}")
                        issues.append(result)
                        self.attack_logger.vprint(f"{CommandlineColors.BACKGROUND_RED}{result}{CommandlineColors.ENDC}", 1)
        return issues

    # TODO: Add verify command to verify all plugins (or a specific one)

    def print_default_config(self, subclass_name, name):
        """ Pretty prints the default config for this plugin """

        subclass = None

        for section in sections:
            if section["name"] == subclass_name:
                subclass = section["subclass"]
        if subclass is None:
            print("Use proper subclass")

        plugins = self.get_plugins(subclass, [name])
        for plugin in plugins:
            print(plugin.get_raw_default_config())
