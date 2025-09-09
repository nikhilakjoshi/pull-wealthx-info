#!/usr/bin/env python3
"""
WealthX Data Puller - Monitoring Dashboard

Real-time monitoring dashboard for the 10-day data pull operation.
Shows progress, statistics, and system health.
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

try:
    from src.mongo_client import MongoDBClient
    from src.progress_tracker import ProgressTracker
    from src.config import get_batch_schedule
except ImportError:
    print(
        "Error: Could not import required modules. Make sure dependencies are installed."
    )
    sys.exit(1)


class WealthXMonitor:
    """Real-time monitoring dashboard"""

    def __init__(self):
        self.mongo_client = MongoDBClient()
        self.progress_tracker = ProgressTracker()

    def clear_screen(self):
        """Clear terminal screen"""
        os.system("clear" if os.name == "posix" else "cls")

    def get_system_health(self) -> Dict[str, Any]:
        """Check system health"""
        return {
            "mongodb_connected": self.mongo_client.test_connection(),
            "progress_file_exists": os.path.exists("progress.json"),
            "logs_directory_exists": os.path.exists("logs"),
            "disk_space_mb": self.get_disk_space(),
            "uptime_hours": self.get_uptime_hours(),
        }

    def get_disk_space(self) -> Optional[int]:
        """Get available disk space in MB"""
        try:
            statvfs = os.statvfs(".")
            return (statvfs.f_frsize * statvfs.f_bavail) // (1024 * 1024)
        except:
            return None

    def get_uptime_hours(self) -> Optional[float]:
        """Get system uptime in hours"""
        try:
            with open("/proc/uptime", "r") as f:
                uptime_seconds = float(f.readline().split()[0])
                return uptime_seconds / 3600
        except:
            return None

    def get_recent_logs(self, lines: int = 10) -> list:
        """Get recent log entries"""
        log_file = "logs/wealthx_pull.log"
        if not os.path.exists(log_file):
            return []

        try:
            with open(log_file, "r") as f:
                return f.readlines()[-lines:]
        except:
            return []

    def calculate_performance_metrics(self, stats: Dict) -> Dict[str, Any]:
        """Calculate performance metrics"""
        if not stats.get("session_start") or not stats.get("total_processed"):
            return {}

        try:
            start_time = datetime.fromisoformat(stats["session_start"])
            elapsed = (datetime.utcnow() - start_time).total_seconds()

            records_per_hour = (
                (stats["total_processed"] / elapsed) * 3600 if elapsed > 0 else 0
            )
            records_per_day = records_per_hour * 24

            return {
                "elapsed_hours": elapsed / 3600,
                "records_per_hour": records_per_hour,
                "records_per_day": records_per_day,
                "average_batch_time": (
                    elapsed / stats["batches_completed"]
                    if stats["batches_completed"] > 0
                    else 0
                ),
            }
        except:
            return {}

    def display_dashboard(self):
        """Display the monitoring dashboard"""
        stats = self.progress_tracker.get_statistics()
        db_count = self.mongo_client.get_total_documents()
        health = self.get_system_health()
        performance = self.calculate_performance_metrics(stats)

        # Calculate progress percentage
        total_target = 420000
        progress_pct = (db_count / total_target * 100) if total_target > 0 else 0

        # Get batch schedule info
        schedule = get_batch_schedule(total_target, 10, 3)

        self.clear_screen()

        print("🌟" + "=" * 78 + "🌟")
        print("🚀 WEALTHX DATA PULLER - LIVE MONITORING DASHBOARD 🚀")
        print("🌟" + "=" * 78 + "🌟")
        print(
            f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 🎯 Target: {total_target:,} records"
        )
        print()

        # Progress Section
        print("📊 PROGRESS OVERVIEW")
        print("-" * 80)
        progress_bar = "█" * int(progress_pct // 2) + "░" * (
            50 - int(progress_pct // 2)
        )
        print(f"Progress: [{progress_bar}] {progress_pct:.1f}%")
        print(f"Records in DB: {db_count:,} / {total_target:,}")
        print(f"Session ID: {stats.get('session_id', 'None')}")
        print(f"Batches Completed: {stats.get('batches_completed', 0)}")
        print(f"Records Processed: {stats.get('total_processed', 0):,}")
        print(f"Current Offset: {stats.get('last_offset', 0):,}")
        print(f"Errors: {stats.get('error_count', 0)}")
        print()

        # Performance Metrics
        if performance:
            print("⚡ PERFORMANCE METRICS")
            print("-" * 80)
            print(f"Elapsed Time: {performance.get('elapsed_hours', 0):.1f} hours")
            print(f"Records/Hour: {performance.get('records_per_hour', 0):,.0f}")
            print(f"Records/Day: {performance.get('records_per_day', 0):,.0f}")
            print(
                f"Avg Batch Time: {performance.get('average_batch_time', 0):.1f} seconds"
            )

            # ETA Calculation
            remaining = total_target - db_count
            if performance.get("records_per_hour", 0) > 0:
                eta_hours = remaining / performance["records_per_hour"]
                eta_days = eta_hours / 24
                print(f"Estimated Completion: {eta_days:.1f} days")
            print()

        # Schedule Information
        print("📅 SCHEDULE INFORMATION")
        print("-" * 80)
        print(f"Target Days: {schedule['days']} days")
        print(f"Daily Runs: {schedule['daily_runs']} times/day")
        print(f"Batch Size: {schedule['batch_size']:,} records")
        print(f"Batches per Run: {schedule['batches_per_run']}")
        print(f"Total Runs Needed: {schedule['total_runs']}")
        print()

        # System Health
        print("💚 SYSTEM HEALTH")
        print("-" * 80)
        print(
            f"MongoDB: {'✅ Connected' if health['mongodb_connected'] else '❌ Disconnected'}"
        )
        print(
            f"Progress File: {'✅ Available' if health['progress_file_exists'] else '❌ Missing'}"
        )
        print(
            f"Logs Directory: {'✅ Available' if health['logs_directory_exists'] else '❌ Missing'}"
        )

        if health["disk_space_mb"]:
            disk_gb = health["disk_space_mb"] / 1024
            print(f"Disk Space: {disk_gb:.1f} GB available")

        if health["uptime_hours"]:
            print(f"System Uptime: {health['uptime_hours']:.1f} hours")
        print()

        # Recent Activity
        recent_logs = self.get_recent_logs(5)
        if recent_logs:
            print("📝 RECENT ACTIVITY")
            print("-" * 80)
            for log_line in recent_logs:
                print(
                    log_line.strip()[:80] + "..."
                    if len(log_line.strip()) > 80
                    else log_line.strip()
                )
            print()

        # Status Summary
        if stats.get("last_batch_time"):
            last_activity = datetime.fromisoformat(stats["last_batch_time"])
            time_since = datetime.utcnow() - last_activity

            if time_since.total_seconds() > 7200:  # 2 hours
                print("⚠️  WARNING: No activity in the last 2+ hours")
            elif time_since.total_seconds() > 3600:  # 1 hour
                print("⚠️  NOTICE: No activity in the last hour")
            else:
                print("✅ System is actively processing data")

        print()
        print("🔄 Refreshing every 30 seconds... Press Ctrl+C to exit")
        print("🌟" + "=" * 78 + "🌟")

    def run_monitor(self, refresh_interval: int = 30):
        """Run the monitoring dashboard"""
        try:
            while True:
                self.display_dashboard()
                time.sleep(refresh_interval)
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped by user")
        finally:
            self.mongo_client.close()


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="WealthX Data Puller Monitoring Dashboard"
    )
    parser.add_argument(
        "--refresh",
        type=int,
        default=30,
        help="Refresh interval in seconds (default: 30)",
    )
    parser.add_argument(
        "--once", action="store_true", help="Run once and exit (no refresh)"
    )

    args = parser.parse_args()

    monitor = WealthXMonitor()

    if args.once:
        monitor.display_dashboard()
    else:
        monitor.run_monitor(args.refresh)


if __name__ == "__main__":
    main()
