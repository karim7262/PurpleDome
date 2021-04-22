**************
Sensor plugins
**************

To experiment with different senors installed on the targets there is the sensor plugin. It contains a plugin class that **MUST** be based on the *SensorPlugin* class.

Usage
=====

To create a new plugin, start a sub-folder in plugins. The python file in there must contain a class that inherits from *SensorPlugin*.

If the plugin is activated for a specific machine four specific methods will be called to interact with the target:

* Install
* Start
* Stop
* Collect results

Methods for these four are called by PurpleDome. Normally you should not have to edit these methods. Just the commands you that are called by them. And those commands are created by specific methods:

* install_command
* start_command
* stop_command
* collect_command

Boilerplate
-----------

The boilerplate contains some basics:

* name: a unique name, also used in the config yaml file to reference this plugin
* description. A human readable description for this plugin.
* required_files: A list. If you ship files with your plugin, listing them here will cause them to be installed on plugin init by creating a copy in the share.

Additionally you can set *self.debugit* to True. This will run the sensor on execution in gdb and make the call blocking. So you can debug your sensor.



The plugin class
================

.. autoclass:: plugins.base.sensor.SensorPlugin
   :members: