
ClusterSet Demo
===============

Pre-requisites
--------------
  - MySQL Server 8.0.27+
  - MySQL Shell 8.0.27+
  - MySQL Router 8.0.27+

MySQL Instances
---------------
1) Deploy 9 MySQL Instances running on the following ports:

  - "Rome": 3331, 3332, 3333
  - "Brussels": 4441, 4442, 4443
  - "Lisbon": 5551, 5552, 5553

2) Ensure the MySQL instances configuration is ready for InnoDB Cluster usage and create a cluster administration account

Example:

    mysqlsh-js> dba.configureInstance("root@rome:3331", {clusterAdmin: "clusteradmin"})

Demo
----

Create standalone cluster

    $ mysqlsh
    mysqlsh-js> \c clusteradmin@rome:3331
    mysqlsh-js> rom = dba.createCluster("ROM")
    mysqlsh-js> rom.addInstance("rome:3332")
    mysqlsh-js> rom.addInstance("rome:3333")

Create a Router administration account

    mysqlsh-js> rom.setupRouterAccount("routeradmin")


Bootstrap and start the Router

    $ mysqlrouter --bootstrap clusteradmin@rome:3331 -d router_rome --name="router_rome" --account=routeradmin --report-host=rome
    $ ./router_rome/start.sh

*NOTE*: Check router's log:

    $ tail -f router_rom/log/mysqlrouter.log

Start RW and RO applications
----------------------------
    $ python app_rw.py
    $ python app_ro.py


Create ClusterSet
-----------------
    mysqlsh-js> cs = rom.createClusterSet("clusterset")

Verify ClusterSet topology
--------------------------
    mysqlsh-js> cs.describe()
    mysqlsh-js> cs.status()
    mysqlsh-js> cs.listRouters()

*NOTE*: Notice in the output of listRouters() and in Router's log a warning mentioning that a re-bootstrap must be performed to ensure the ideal configurations are in place.

**Re-Bootstrap the Router:**

    $ ./router_rome/stop.sh
    $ mysqlrouter --bootstrap clusteradmin@rome:3331 -d router_rome --name="router_rome" --account=routeradmin --report-host=rome --force
    $ ./router_rome/start.sh


Create Replica Clusters
-----------------------

**Brussels Replica Cluster**

    mysqlsh-js> bru = cs.createReplicaCluster("brussels:4441", "BRU")
    mysqlsh-js> bru.addInstance("brussels:4442")
    mysqlsh-js> bru.addInstance("brussels:4443")

**Lisbon Replica Cluster**

    mysqlsh-js> lis = cs.createReplicaCluster("lisbon:5551", "LIS")
    mysqlsh-js> lis.addInstance("lisbon:5552")
    mysqlsh-js> lis.addInstance("lisbon:5553")


Check ClusterSet Status and Individual Cluster Status + Extended Status
-----------------------------------------------------------------------
    mysqlsh-js> cs.status()
    mysqlsh-js> cs.status({extended: 1})
    mysqlsh-js> bru.status()
    mysqlsh-js> lis.status()
    mysqlsh-js> rom.status()


Change Individual Clusters Primary Instance
-------------------------------------------
    mysqlsh-js> bru.setPrimaryInstance("brussels:4442")
    mysqlsh-js> rom.setPrimaryInstance("rome:3332")

*NOTE*: Verify Router's changing the RW traffic to rome:3332 now.


Change ClusterSet Primary Cluster - Switchover
----------------------------------------------
    mysqlsh-js> cs.setPrimaryCluster("BRU")

*NOTE*: Verify Router adapting automatically, RW traffic going to brussels:4442 now (the primary instance of the primary Cluster)


Check Routing Policies
----------------------
    mysqlsh-js> cs.routingOptions()

*NOTE*: There are two possible routing policies: `target_cluster` (default value `primary`) and `invalidated_cluster_policy` (default value `drop_all`)


Change Global target_cluster Routing policy
-------------------------------------------
    mysqlsh-js> cs.setRoutingOption("target_cluster", "ROM")

*NOTE*: Write traffic is now rejected by the Router since the Router's target_cluster is now "ROM" that is a Replica Cluster.


**Change the Primary Cluster**

    mysqlsh-js> cs.setPrimaryCluster("ROM")

*NOTE*: Router accepts RW traffic now since "ROM" became the Primary Cluster


**Switch back the global routing policy to follow the primary Cluster**

    mysqlsh-js> cs.setRoutingOption("target_cluster", "primary")


Disasters
---------

**Kill primary instance of "ROM"**

Send a SIGKILL to the primary member of "ROM" that is at the moment "rome:3332".

Example:

    $ kill -9 $(ps aux | grep 'mysqld' | grep 3332 | awk '{print $2}'

*NOTE*: Verify how the ClusterSet replication channel was automatically re-established to the newly elected primary instance of "ROM" and how Router is sending the RW traffic to it.


**Kill primary instance of "BRU"**
Send a SIGKILL to the primary member of "ROM" that is at the moment "brussels:4442".

Example:

    $ kill -9 $(ps aux | grep 'mysqld' | grep 4442 | awk '{print $2}')

*NOTE*: Verify the ClusterSet replication channel was automatically re-established from the newly elected primary of "BRU" to the primary member of "ROM"


**Kill the whole Primary Cluster "ROM"**
Send a SIGKILL to the remaining 2 members of "ROM": "rome:3331" and "rome:3333"

Example:

    $ kill -9 $(ps aux | grep 'mysqld' | grep 3331 | awk '{print $2}')
    $ kill -9 $(ps aux | grep 'mysqld' | grep 3333 | awk '{print $2}')


Force Failover of the Primary Cluster
-------------------------------------
    mysqlsh-js> \c clusteradmin@brussels:4441
    mysqlsh-js> cs = dba.getClusterSet()
    mysqlsh-js> cs.status()
    mysqlsh-js> cs.forcePrimaryCluster("BRU")

**Verify the status after the failover is successful**

    mysqlsh-js> bru = dba.getCluster()
    mysqlsh-js> bru.status()
    mysqlsh-js> cs.status()


Restore "ROM" Cluster and rejoin it back to the ClusterSet
----------------------------------------------------------
Start all "ROM" instances:

  - rome:3331
  - rome:3332
  - rome:3333

**Reboot the Cluster from Complete Outage**

    mysqlsh-js> \c clusteradmin@rome:3331
    mysqlsh-js> rom = dba.rebootClusterFromCompleteOutage()

    mysqlsh-js> cs.status()

*NOTE*: Verify the Cluster is marked as INVALIDATED in the ClusterSet and must be either removed from it or rejoined

**Rejoin the Cluster back to the ClusterSet**

    mysqlsh-js> cs.rejoinCluster("ROM")
    mysqlsh-js> cs.status()
