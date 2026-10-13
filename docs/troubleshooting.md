# Troubleshooting Guide: Music Analytics Platform

This guide documents encountered failure scenarios, root causes, and verified solutions.

---

## 1. Issue: Java 17 InaccessibleObjectException (Kryo / MapReduce)

### Symptoms
`java.lang.reflect.InaccessibleObjectException: Unable to make field accessible: module java.base does not opens java.net / java.util to unnamed module`

### Root Cause
Java 17 strongly encapsulates internal packages. Big Data tools like Apache Hive, Pig, and Kryo serialization need explicit reflection access.

### Solution
Provide JVM module opens flags to both the client and YARN containers:
```bash
--add-opens=java.base/java.lang=ALL-UNNAMED
--add-opens=java.base/java.net=ALL-UNNAMED
--add-opens=java.base/java.util=ALL-UNNAMED
--add-opens=java.base/java.util.concurrent=ALL-UNNAMED
--add-opens=java.base/java.util.concurrent.atomic=ALL-UNNAMED
--add-opens=java.base/java.io=ALL-UNNAMED
--add-opens=java.base/java.nio=ALL-UNNAMED
```
Configured automatically in `config/mapred-site.xml` (`mapreduce.map.java.opts` and `mapreduce.reduce.java.opts`).

---

## 2. Issue: Derby Metastore Lock (`ERROR XSDB6`)

### Symptoms
`ERROR XSDB6: Another instance of Derby may have already booted the database`

### Root Cause
Embedded Apache Derby allows only one active connection at a time. If an unmanaged Hive process or HiveServer2 holds the lock, subsequent CLI connections fail.

### Solution
Stop conflicting background instances and release the lock file:
```bash
rm -f /home/maddy/opt/hive-4.0.0/metastore_db/db.lck
rm -f /home/maddy/opt/hive-4.0.0/metastore_db/dbex.lck
```
Handled automatically in `hive/run.sh` and `pipeline/cleanup.sh`.

---

## 3. Issue: SSH Disabled on Port 22

### Symptoms
`ssh: connect to host localhost port 22: Connection refused` when running `start-dfs.sh` or `start-yarn.sh`.

### Root Cause
Standard Apache Hadoop shell startup scripts assume passwordless SSH to localhost is running.

### Solution
Do not depend on `start-dfs.sh`. Instead, run Hadoop daemons natively or manage them via user systemd units:
```bash
systemd-run --user --unit=hadoop-namenode ...
systemd-run --user --unit=hadoop-datanode ...
```
Implemented and automated in `scripts/bootstrap.sh`.

---

## 4. Issue: Missing `CollectionUtils` in YARN Mapper

### Symptoms
`ClassNotFoundException: org.apache.commons.collections.CollectionUtils`

### Root Cause
Hadoop 3.5.0 ships with `commons-collections4-4.4.jar`, whereas Hive 4.0.0 queries compiled against older commons collections require `commons-collections-3.2.2.jar`.

### Solution
Copy `commons-collections-3.2.2.jar` from Hive lib into Hadoop common lib:
```bash
cp /home/maddy/opt/hive-4.0.0/lib/commons-collections-3.2.2.jar /home/maddy/opt/hadoop-3.5.0/share/hadoop/common/lib/
```
Now present permanently in the Hadoop installation.
