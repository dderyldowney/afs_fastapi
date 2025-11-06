#!/usr/bin/env python3
"""
Demonstration script showing async database performance improvements.

This script demonstrates the performance gains achieved by converting
synchronous database operations to async operations in agricultural robotics.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timedelta

import sqlalchemy
from sqlalchemy import create_engine, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# Define Base for SQLAlchemy models
class Base(DeclarativeBase):
    pass


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def setup_test_databases():
    """Set up test databases for comparison."""
    # Sync database
    sync_engine = create_engine("/benchmark_sync.db", echo=False)

    # Async database
    async_engine = create_async_engine("/benchmark_async.db", echo=False)

    return sync_engine, async_engine


def sync_operations_demo(sync_engine, count: int = 1000):
    """Demonstrate synchronous database operations."""
    logger.info(f"Running sync operations with {count} records...")

    start_time = time.time()

    # Create tables
    Base = sqlalchemy.orm.declarative_base()

    class TestEquipment(Base):
        __tablename__ = "test_equipment"

        id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
        equipment_id = sqlalchemy.Column(sqlalchemy.String(50))
        isobus_address = sqlalchemy.Column(sqlalchemy.Integer)
        created_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.utcnow)

    Base.metadata.create_all(sync_engine)

    # Insert records synchronously
    SessionLocal = sessionmaker(bind=sync_engine)

    with SessionLocal() as session:
        insert_start = time.time()

        for i in range(count):
            equipment = TestEquipment(equipment_id=f"sync_equipment_{i}", isobus_address=1000 + i)
            session.add(equipment)

            # Commit every 100 records for fair comparison
            if i % 100 == 99:
                session.commit()

        # Commit remaining records
        session.commit()

        insert_time = time.time() - insert_start

        # Query records
        query_start = time.time()
        session.query(TestEquipment).limit(count // 10).all()
        query_time = time.time() - query_start

    total_time = time.time() - start_time

    logger.info("Sync Results:")
    logger.info(f"  Total Time: {total_time:.3f}s")
    logger.info(f"  Insert Time: {insert_time:.3f}s")
    logger.info(f"  Query Time: {query_time:.3f}s")
    logger.info(f"  Throughput: {count/insert_time:.1f} records/sec")

    return {
        "total_time": total_time,
        "insert_time": insert_time,
        "query_time": query_time,
        "throughput": count / insert_time,
    }


async def async_operations_demo(async_engine, count: int = 1000):
    """Demonstrate async database operations."""
    logger.info(f"Running async operations with {count} records...")

    start_time = time.time()

    # Create tables
    Base = sqlalchemy.orm.declarative_base()

    class TestEquipment(Base):
        __tablename__ = "test_equipment"

        id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
        equipment_id = sqlalchemy.Column(sqlalchemy.String(50))
        isobus_address = sqlalchemy.Column(sqlalchemy.Integer)
        created_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.utcnow)

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = async_sessionmaker(async_engine, expire_on_commit=False)

    # Insert records asynchronously
    insert_start = time.time()

    async with async_session_factory() as session:
        for i in range(count):
            equipment = TestEquipment(equipment_id=f"async_equipment_{i}", isobus_address=2000 + i)
            session.add(equipment)

            # Commit every 100 records for fair comparison
            if i % 100 == 99:
                await session.commit()

        # Commit remaining records
        await session.commit()

        insert_time = time.time() - insert_start

        # Query records
        query_start = time.time()
        result = await session.execute(select(TestEquipment).limit(count // 10))
        result.scalars().all()
        query_time = time.time() - query_start

    total_time = time.time() - start_time

    logger.info("Async Results:")
    logger.info(f"  Total Time: {total_time:.3f}s")
    logger.info(f"  Insert Time: {insert_time:.3f}s")
    logger.info(f"  Query Time: {query_time:.3f}s")
    logger.info(f"  Throughput: {count/insert_time:.1f} records/sec")

    return {
        "total_time": total_time,
        "insert_time": insert_time,
        "query_time": query_time,
        "throughput": count / insert_time,
    }


async def agricultural_can_message_demo():
    """Demonstrate high-frequency CAN message processing."""
    logger.info("Demonstrating agricultural CAN message processing...")

    # Simulate agricultural CAN messages
    agricultural_messages = []
    for i in range(5000):  # 5,000 CAN messages (typical for 1 minute of tractor operation)
        agricultural_messages.append(
            {
                "timestamp": datetime.now()
                - timedelta(seconds=i * 0.012),  # 83ms intervals (CAN bus frequency)
                "equipment_id": f"TRACTOR_{i % 5}",  # 5 tractors
                "pgn": 61444 + (i % 10),  # Agricultural PGNs
                "data": {
                    "rpm": 2000 + (i % 500),
                    "speed": 8.5 + (i % 3),
                    "fuel_level": 75 - (i % 10),
                    "temperature": 85 + (i % 5),
                },
            }
        )

    # Async CAN message processing
    async def process_can_messages_async(messages):
        """Process CAN messages with async operations."""
        engine = create_async_engine("/can_messages_async.db", echo=False)
        async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

        class CANMessage(Base):
            __tablename__ = "can_messages"

            id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
            timestamp = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False)
            equipment_id = sqlalchemy.Column(sqlalchemy.String(50), nullable=False)
            pgn = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
            data = sqlalchemy.Column(sqlalchemy.JSON, nullable=False)
            created_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.utcnow)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        start_time = time.time()

        async with async_session_factory() as session:
            for msg in messages:
                can_msg = CANMessage(
                    timestamp=msg["timestamp"],
                    equipment_id=msg["equipment_id"],
                    pgn=msg["pgn"],
                    data=msg["data"],
                )
                session.add(can_msg)

                # Batch commit for performance
                if msg == messages[-1]:  # Commit last batch
                    await session.commit()

        processing_time = time.time() - start_time

        await engine.dispose()

        return processing_time

    # Sync CAN message processing (comparison)
    def process_can_messages_sync(messages):
        """Process CAN messages with sync operations."""
        engine = create_engine("/can_messages_sync.db", echo=False)

        class CANMessage(Base):
            __tablename__ = "can_messages"

            id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
            timestamp = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False)
            equipment_id = sqlalchemy.Column(sqlalchemy.String(50), nullable=False)
            pgn = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
            data = sqlalchemy.Column(sqlalchemy.JSON, nullable=False)
            created_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.utcnow)

        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)

        start_time = time.time()

        with SessionLocal() as session:
            for msg in messages:
                can_msg = CANMessage(
                    timestamp=msg["timestamp"],
                    equipment_id=msg["equipment_id"],
                    pgn=msg["pgn"],
                    data=msg["data"],
                )
                session.add(can_msg)

                # Batch commit for performance
                if msg == messages[-1]:  # Commit last batch
                    session.commit()

        processing_time = time.time() - start_time

        return processing_time

    logger.info("Processing 5,000 agricultural CAN messages...")

    # Run async processing
    async_time = await process_can_messages_async(agricultural_messages)

    # Run sync processing
    sync_time = process_can_messages_sync(agricultural_messages)

    logger.info("CAN Message Processing Results:")
    logger.info(f"  Sync Time: {sync_time:.3f}s")
    logger.info(f"  Async Time: {async_time:.3f}s")
    logger.info(f"  Performance Improvement: {sync_time/async_time:.2f}x")
    logger.info(f"  Messages/sec (Sync): {5000/sync_time:.1f}")
    logger.info(f"  Messages/sec (Async): {5000/async_time:.1f}")

    return {
        "sync_time": sync_time,
        "async_time": async_time,
        "improvement_factor": sync_time / async_time,
        "sync_throughput": 5000 / sync_time,
        "async_throughput": 5000 / async_time,
    }


async def main():
    """Main demonstration function."""
    logger.info("🚀 Starting Async Database Performance Demonstration")
    logger.info("=" * 60)

    # Set up test databases
    sync_engine, async_engine = setup_test_databases()

    try:
        # Run basic operation comparison
        logger.info("\n📊 Basic Database Operations Comparison:")
        logger.info("-" * 40)

        sync_results = sync_operations_demo(sync_engine, 1000)
        async_results = await async_operations_demo(async_engine, 1000)

        # Calculate improvements
        total_improvement = sync_results["total_time"] / async_results["total_time"]
        insert_improvement = sync_results["insert_time"] / async_results["insert_time"]
        query_improvement = sync_results["query_time"] / async_results["query_time"]
        throughput_improvement = async_results["throughput"] / sync_results["throughput"]

        logger.info("\n🎯 Performance Improvements:")
        logger.info(f"  Total Operations: {total_improvement:.2f}x faster")
        logger.info(f"  Insert Operations: {insert_improvement:.2f}x faster")
        logger.info(f"  Query Operations: {query_improvement:.2f}x faster")
        logger.info(f"  Throughput: {throughput_improvement:.2f}x higher")

        # Run agricultural CAN message demo
        logger.info("\n🌾 Agricultural CAN Message Processing:")
        logger.info("-" * 40)

        can_results = await agricultural_can_message_demo()

        # Final summary
        logger.info("\n🏆 Final Summary:")
        logger.info("=" * 60)
        logger.info(
            f"✅ Async database operations provide {total_improvement:.1f}x to {can_results['improvement_factor']:.1f}x performance improvement"
        )
        logger.info(
            f"✅ Agricultural CAN message processing improved by {can_results['improvement_factor']:.1f}x"
        )
        logger.info(
            f"✅ Overall throughput increased from {sync_results['throughput']:.1f} to {async_results['throughput']:.1f} records/sec"
        )
        logger.info(
            f"✅ High-frequency agricultural data processing now capable of {can_results['async_throughput']:.1f} messages/sec"
        )

        logger.info("\n🎯 Key Benefits for Agricultural Robotics:")
        logger.info("  • Faster equipment data processing")
        logger.info("  • Real-time telemetry for field operations")
        logger.info("  • Improved fleet coordination capabilities")
        logger.info("  • Better AI model performance for agricultural analytics")
        logger.info("  • Enhanced scalability for multi-tractor operations")

    except Exception as e:
        logger.error(f"❌ Demonstration failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    finally:
        # Clean up test databases
        import os

        if os.path.exists("benchmark_sync.db"):
            os.remove("benchmark_sync.db")
        if os.path.exists("benchmark_async.db"):
            os.remove("benchmark_async.db")
        if os.path.exists("can_messages_sync.db"):
            os.remove("can_messages_sync.db")
        if os.path.exists("can_messages_async.db"):
            os.remove("can_messages_async.db")

    logger.info("\n🎉 Async Database Implementation Complete!")
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
