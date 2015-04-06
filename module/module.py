#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#    Frederic Mohier, frederic.mohier@gmail.com
#    Jerome Lebeon, Jerome@LeBeon.org
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

"""
This module forwards all filtered datas to another shinken
This is useful to create "real-test traffic"
"""

from subprocess import Popen
from shinken.basemodule import BaseModule
from shinken.log import logger

properties = {
    'daemons': ['broker'],
    'type': 'checks-forward',
    'external': True,
}

def get_instance(mod_conf):
    instance = Checkforward(mod_conf)
    return instance

class Checkforward(BaseModule):
    def __init__(self, mod_conf):
        BaseModule.__init__(self, mod_conf)
        logger.info("[Checks forward] module initialization")

        try:
            # Module configuration
            self.glpi_entities = getattr(mod_conf, 'glpi_entities', '')
            self.glpi_entities = self.glpi_entities.split(',')
            if len(self.glpi_entities) > 0 and self.glpi_entities[0] == '':
                self.glpi_entities = None

            self.send_nsca_bin = str(getattr(mod_conf, 'send_nsca_bin', '/usr/sbin/send_nsca'))
            self.send_nsca_config = str(getattr(mod_conf, 'send_nsca_config', '/etc/send_nsca.cfg'))

            self.nsca_server_host = str(getattr(mod_conf, 'nsca_server_host', '127.0.0.1'))
            self.nsca_server_port = int(getattr(mod_conf, 'nsca_server_port', 5667))

            logger.info("[Checks forward] module configuration, forward to: %s:%s, using %s with configuration %s" % (self.nsca_server_host, self.nsca_server_port, self.send_nsca_bin, self.send_nsca_config))
            if self.glpi_entities:
                logger.info("[Checks forward] module configuration, forward checks for GLPI entities: %s" % str(self.glpi_entities))
            else:
                logger.info("[Checks forward] module configuration, forward checks for all hosts/services")

            # Internal cache for host entities id
            self.cache_host_entities_id = {}
        except AttributeError:
            logger.error("[Checks forward] The module is missing a property, check module configuration")
            raise
        
    def init(self):
        logger.debug("[Checks forward] init function")

    def manage_initial_host_status_brok(self, b):
        try:
            logger.debug("[Checks forward] initial host status: %s" % str(b.data['customs']))
            self.cache_host_entities_id[b.data['host_name']] = b.data['customs']['_ENTITIESID']
            if self.cache_host_entities_id[b.data['host_name']] in self.glpi_entities:
                logger.info("[Checks forward] host %s checks will be forwarded (entity: %s)" % (b.data['host_name'], self.cache_host_entities_id[b.data['host_name']]))
        except:
            logger.warning("[Checks forward] no entity Id for host: %s" % (b.data['host_name']))
        
    def manage_host_check_result_brok(self, b):
        try:
            if self.glpi_entities and self.cache_host_entities_id[b.data['host_name']] not in self.glpi_entities:
                return
        except:
            return
        
        try:
            self.send_nsca(b)
        except OSError as e:
            logger.error("[Checks forward] Error forward nsca '%s'" % e)

    def manage_service_check_result_brok(self, b):
        try:
            if self.glpi_entities and self.cache_host_entities_id[b.data['host_name']] not in self.glpi_entities:
                return
        except:
            return

        try:
            self.send_nsca(b)
        except OSError as e:
            logger.error("[Checks forward] Error forward nsca '%s'" % e)
            

    def send_nsca(self, b):
        check_type = b.type
        hostname = b.data['host_name']
        return_code = b.data['return_code']
        output = b.data['output']

        if (check_type == "service_check_result"):
            service_description = b.data['service_description']
            # <hostname>[TAB]<service name>[TAB]<return code>[TAB]<plugin output>
            send_nsca = hostname+"\t"+service_description+"\t"+str(return_code)+"\t"+output+"|"+b.data['perf_data']
        if (check_type == "host_check_result"):
            # <hostname>[TAB]<return code>[TAB]<plugin output>
            send_nsca = hostname+"\t"+str(return_code)+"\t"+output+"|"+b.data['perf_data']

        logger.debug("[Checks forward] sending nsca '%s' for '%s'" % (check_type,hostname))
        command = "/bin/echo \"%s\" | %s -H %s -p %s -c %s" % (send_nsca, self.send_nsca_bin, self.nsca_server_host, self.nsca_server_port, self.send_nsca_config)
        try:
            retcode = Popen(command, shell=True)
            return True
        except:
            return False

    def manage_brok(self, b):
        if b.type in ('initial_host_status', 'initial_service_status', 'service_check_result', 'host_check_result'):
            BaseModule.manage_brok(self, b)

    def main(self):
        self.set_proctitle(self.name)
        self.set_exit_handler()
        while not self.interrupted:
            l = self.to_q.get()
            for b in l:
                b.prepare()
                self.manage_brok(b)
