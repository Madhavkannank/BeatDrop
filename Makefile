.PHONY: help bootstrap healthcheck test pipeline clean reset dashboard datacenter sql-bridge nosql

SHELL := /bin/bash

help:
	@echo "Music Analytics Platform - Commands:"
	@echo "  make bootstrap     - Ensure environment, start HDFS/YARN daemons, create HDFS dirs"
	@echo "  make healthcheck   - Run full system and engine health checks"
	@echo "  make test          - Run test suite"
	@echo "  make pipeline      - Execute full end-to-end Big Data pipeline"
	@echo "  make datacenter    - Import/Export web datacenter unstructured data to HDFS"
	@echo "  make sql-bridge    - Import/Export relational SQL database to HDFS"
	@echo "  make nosql         - Store and process data in MongoDB NoSQL with Aggregation Pipelines"
	@echo "  make clean         - Safe cleanup of local artifacts and temporary tables"
	@echo "  make reset         - Stop daemons and reset environment"
	@echo "  make dashboard     - Launch local dashboard"

bootstrap:
	chmod +x scripts/*.sh
	./scripts/bootstrap.sh

healthcheck:
	./scripts/healthcheck.sh

test:
	python3 -m unittest discover -s tests -p "test_*.py" -v

pipeline:
	./pipeline/run_pipeline.sh

datacenter:
	python3 pipeline/datacenter_web_to_hdfs.py

sql-bridge:
	python3 pipeline/sql_hdfs_connector.py

nosql:
	python3 nosql/mongo_manager.py

clean:
	./pipeline/cleanup.sh

reset:
	./scripts/reset_environment.sh

dashboard:
	python3 dashboard/server.py
