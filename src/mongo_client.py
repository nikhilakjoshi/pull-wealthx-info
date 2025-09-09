import os
from typing import Dict, List, Optional, Any
from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError, PyMongoError
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class MongoDBClient:
    """Client for MongoDB operations"""

    def __init__(self):
        self.uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        self.database_name = os.getenv("MONGO_DATABASE", "wealthx_data")
        self.collection_name = os.getenv("MONGO_COLLECTION", "profiles")

        self.client = MongoClient(self.uri)
        self.db = self.client[self.database_name]
        self.collection = self.db[self.collection_name]

        self.logger = logging.getLogger(__name__)

        # Ensure indexes
        self._create_indexes()

    def _create_indexes(self):
        """Create necessary indexes for efficient operations"""
        try:
            # Index on WealthX ID for upserts
            self.collection.create_index("ID", unique=True, sparse=True)
            # Index on created/updated timestamps
            self.collection.create_index("created_at")
            self.collection.create_index("updated_at")
            # Additional useful indexes for WealthX data
            self.collection.create_index("dossierState")
            self.collection.create_index("dossierCategory")
            self.collection.create_index([("lastName", 1), ("firstName", 1)])
            self.logger.info("Database indexes created/verified")
        except PyMongoError as e:
            self.logger.warning(f"Error creating indexes: {e}")

    def test_connection(self) -> bool:
        """Test MongoDB connection"""
        try:
            self.client.admin.command("ismaster")
            return True
        except PyMongoError:
            return False

    def bulk_upsert_profiles(self, dossiers: List[Dict]) -> Dict[str, int]:
        """Bulk upsert dossiers with conflict resolution"""
        if not dossiers:
            return {"inserted": 0, "updated": 0, "errors": 0}

        operations = []
        current_time = datetime.utcnow()

        for dossier in dossiers:
            # Add metadata
            dossier_data = {**dossier, "updated_at": current_time}

            # Set created_at only for new documents
            if "created_at" not in dossier_data:
                dossier_data["created_at"] = current_time

            # Use WealthX ID as unique identifier
            wealthx_id = dossier.get("ID")
            if not wealthx_id:
                self.logger.warning("Dossier missing WealthX ID, skipping")
                continue

            operation = UpdateOne(
                {"ID": wealthx_id},
                {"$set": dossier_data, "$setOnInsert": {"created_at": current_time}},
                upsert=True,
            )
            operations.append(operation)

        try:
            result = self.collection.bulk_write(operations, ordered=False)

            stats = {
                "inserted": result.upserted_count,
                "updated": result.modified_count,
                "errors": 0,
            }

            self.logger.info(f"Bulk upsert completed: {stats}")
            return stats

        except BulkWriteError as bwe:
            # Handle partial success
            stats = {
                "inserted": bwe.details.get("nUpserted", 0),
                "updated": bwe.details.get("nModified", 0),
                "errors": len(bwe.details.get("writeErrors", [])),
            }

            self.logger.error(f"Bulk write errors: {stats}")
            for error in bwe.details.get("writeErrors", []):
                self.logger.error(f"Write error: {error}")

            return stats

        except PyMongoError as e:
            self.logger.error(f"MongoDB error during bulk upsert: {e}")
            return {"inserted": 0, "updated": 0, "errors": len(dossiers)}

    def get_total_documents(self) -> int:
        """Get total number of documents in collection"""
        try:
            return self.collection.count_documents({})
        except PyMongoError as e:
            self.logger.error(f"Error counting documents: {e}")
            return 0

    def get_latest_wealthx_id(self) -> Optional[int]:
        """Get the highest WealthX ID to resume from"""
        try:
            doc = self.collection.find_one({}, {"ID": 1}, sort=[("ID", -1)])
            return doc.get("ID") if doc else None
        except PyMongoError as e:
            self.logger.error(f"Error finding latest WealthX ID: {e}")
            return None

    def cleanup_duplicates(self) -> int:
        """Remove duplicate documents based on WealthX ID"""
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": "$ID",
                        "docs": {"$push": "$_id"},
                        "count": {"$sum": 1},
                    }
                },
                {"$match": {"count": {"$gt": 1}}},
            ]

            duplicates = list(self.collection.aggregate(pipeline))
            removed_count = 0

            for duplicate in duplicates:
                # Keep the first document, remove the rest
                docs_to_remove = duplicate["docs"][1:]
                self.collection.delete_many({"_id": {"$in": docs_to_remove}})
                removed_count += len(docs_to_remove)

            self.logger.info(f"Removed {removed_count} duplicate documents")
            return removed_count

        except PyMongoError as e:
            self.logger.error(f"Error cleaning up duplicates: {e}")
            return 0

    def close(self):
        """Close MongoDB connection"""
        self.client.close()
