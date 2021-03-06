#!/usr/bin/env python3
""" Base class for all plugin types """

from inspect import currentframe
import os
from typing import Optional
import yaml
from app.exceptions import PluginError  # type: ignore
import app.exceptions  # type: ignore


class BasePlugin():
    """ Base class for plugins """

    required_files: list[str] = []   # a list of files shipped with the plugin to be installed
    name: str = ""  # The name of the plugin
    alternative_names: list[str] = []  # The is an optional list of alternative names
    description: Optional[str] = None  # The description of this plugin

    def __init__(self) -> None:
        # self.machine = None
        self.plugin_path: Optional[str] = None
        self.machine_plugin = None
        # self.sysconf = {}
        self.conf: dict = {}
        self.attack_logger = None

        self.default_config_name = "default_config.yaml"

    def get_filename(self):
        """ Returns the current filename.  """
        cf = currentframe()  # pylint: disable=invalid-name
        return cf.f_back.filename

    def get_linenumber(self):
        """ Returns the current linenumber.  """
        cf = currentframe()  # pylint: disable=invalid-name
        return cf.f_back.f_lineno

    def get_playground(self):
        """ Returns the machine specific playground

         Which is the folder on the machine where we run our tasks in
         """

        if self.machine_plugin is None:
            raise PluginError("Default machine not configured. Maybe you are creating an attack plugin. Then there are special attack/target machines")

        return self.machine_plugin.get_playground()

    def set_logger(self, attack_logger):
        """ Set the attack logger for this machine """
        self.attack_logger = attack_logger

    def process_templates(self):  # pylint: disable=no-self-use
        """ A method you can optionally implement to transfer your jinja2 templates into the files yo want to send to the target. See 'required_files' """

        return

    def copy_to_attacker_and_defender(self):  # pylint: disable=no-self-use
        """ Copy attacker/defender specific files to the machines """

        return

    def setup(self):
        """ Prepare everything for the plugin """

        self.process_templates()

        for a_file in self.required_files:
            src = os.path.join(os.path.dirname(self.plugin_path), a_file)
            self.vprint(src, 3)
            self.copy_to_machine(src)

        self.copy_to_attacker_and_defender()

    def set_machine_plugin(self, machine_plugin):
        """ Set the machine plugin class to communicate with

        @param machine_plugin: Machine plugin to communicate with
        """

        self.machine_plugin = machine_plugin

    def set_sysconf(self, config):   # pylint:disable=unused-argument
        """ Set system config

        @param config: A dict with system configuration relevant for all plugins
        """

        # self.sysconf["abs_machinepath_internal"] = config["abs_machinepath_internal"]
        # self.sysconf["abs_machinepath_external"] = config["abs_machinepath_external"]
        self.load_default_config()

    def process_config(self, config: dict):
        """ process config and use defaults if stuff is missing

        @param config: The config dict
        """

        # TODO: Move to python 3.9 syntax z = x | y

        self.conf = {**self.conf, **config}

    def copy_to_machine(self, filename: str):
        """ Copies a file shipped with the plugin to the machine share folder

        @param filename: File from the plugin folder to copy to the machine share.
        """

        if self.machine_plugin is not None:
            self.machine_plugin.put(filename, self.machine_plugin.get_playground())
        else:
            raise PluginError("Missing machine")

    def get_from_machine(self, src: str, dst: str):
        """ Get a file from the machine """
        if self.machine_plugin is not None:
            self.machine_plugin.get(src, dst)  # nosec
        else:
            raise PluginError("Missing machine")

    def run_cmd(self, command: str, disown: bool = False):
        """ Execute a command on the vm using the connection

         @param command: Command to execute
         @param disown: Run in background
         """

        if self.machine_plugin is None:
            raise PluginError("machine to run command on is not registered")

        self.vprint(f"      Plugin running command {command}", 3)

        res = self.machine_plugin.__call_remote_run__(command, disown=disown)
        return res

    def get_name(self):
        """ Returns the name of the plugin, please set in boilerplate """
        if self.name:
            return self.name

        raise NotImplementedError

    def get_names(self) -> list[str]:
        """ Adds the name of the plugin to the alternative names and returns the list """

        res = set()

        if self.name:
            res.add(self.name)

        for i in self.alternative_names:
            res.add(i)

        if len(res) > 0:
            return list(res)

        raise NotImplementedError

    def get_description(self):
        """ Returns the description of the plugin, please set in boilerplate """
        if self.description:
            return self.description

        raise NotImplementedError

    def get_plugin_path(self):
        """ Returns the path the plugin file(s) are stored in """

        return os.path.join(os.path.dirname(self.plugin_path))

    def get_default_config_filename(self):
        """ Generate the default filename of the default configuration file """

        return os.path.join(self.get_plugin_path(), self.default_config_name)

    def get_raw_default_config(self):
        """ Returns the default config as string. Usable as an example and for documentation """

        if os.path.isfile(self.get_default_config_filename()):
            with open(self.get_default_config_filename(), "rt") as fh:
                return fh.read()
        else:
            return f"# The plugin {self.get_name()} does not support configuration"

    def load_default_config(self):
        """ Reads and returns the default config as dict """

        filename = self.get_default_config_filename()

        if not os.path.isfile(filename):
            self.vprint(f"Did not find default config {filename}", 3)
            self.conf = {}
        else:
            with open(filename) as fh:
                self.vprint(f"Loading default config {filename}", 3)
                self.conf = yaml.safe_load(fh)
            if self.conf is None:
                self.conf = {}

    def get_config_section_name(self) -> str:
        """ Returns the name for the config sub-section to use for this plugin.

        Defaults to the name of the plugin. This method should be overwritten if it gets more complicated """

        return self.get_name()

    def main_path(self) -> str:  # pylint:disable=no-self-use
        """ Returns the main path of the Purple Dome installation """
        app_dir = os.path.dirname(app.exceptions.__file__)

        return os.path.split(app_dir)[0]

    def vprint(self, text: str, verbosity: int):
        """ verbosity based stdout printing

        0: Errors only
        1: Main colored information
        2: Detailed progress information
        3: Debug logs, data dumps, everything

        @param text: The text to print
        @param verbosity: the verbosity level the text has.
        """
        if self.attack_logger is not None:
            self.attack_logger.vprint(text, verbosity)
