.. _gpli_checks_forward_module:

=========================
Checks forward
=========================


This module is a broker module that builds NSCA messages from host/service checks. The idea is to "forward" the checks results to another instance of Shinken ... nice feature to simulate high traffic on testing environment !


Requirements 
=============



Enabling Checks forward module 
=============================

To use the checks-forward module you must declare it in your broker configuration.

::

  define arbiter {
      ... 

      modules    	 ..., checks-forward

  }


The module configuration is defined in the file: checks-forward.cfg.

Default behaviour is that none of the checks are managed. 
For each GLPI entity you wish to forward checks for, you need to add its Id to the glpi_entities parameter.

::

  ## Module:      checks-forward
  ## Loaded by:   broker
  # Checks forwarder
  define module {
      module_name         checks-forward
      module_type         checks-forward

      # Default values are as is:
      send_nsca_bin        /usr/sbin/send_nsca
      send_nsca_config     /etc/send_nsca.cfg
    
      # Define host where to send checks results
      nsca_server_host     192.168.1.13
      nsca_server_port     5667 

      # Define list of Glpi entities concerned by forwarding
      glpi_entities         1,2,3
  }

It's done :)
