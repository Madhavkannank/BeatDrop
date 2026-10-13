#!/usr/bin/env bash
# ==============================================================================
# Reset Environment Script
# Safely stops user services and cleans temporary run files
# ==============================================================================

set -euo pipefail

echo "Stopping Hadoop & YARN user services..."
systemctl --user stop hadoop-namenode.service 2>/dev/null || true
systemctl --user stop hadoop-datanode.service 2>/dev/null || true
systemctl --user stop hadoop-resourcemanager.service 2>/dev/null || true
systemctl --user stop hadoop-nodemanager.service 2>/dev/null || true

echo "Cleaning temporary runtime PID files..."
rm -f /tmp/hadoop-*.pid

echo "Environment reset complete. Run ./scripts/bootstrap.sh to start services again."
