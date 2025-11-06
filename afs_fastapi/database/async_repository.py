"""
Async-compatible repository pattern for agricultural database operations.

This module provides async-compatible repository classes for all agricultural
database models, following the Repository pattern for clean separation of
data access logic from business logic. All operations are optimized for
high-performance async database operations in agricultural robotics contexts.

Implementation follows Test-First Development (TDD) GREEN phase.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any, TypeVar

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from afs_fastapi.database.agricultural_schemas_async import (
    AgriculturalSensorRecord,
    AsyncDatabaseManager,
    Equipment,
    Field,
    ISOBUSMessageRecord,
    OperationalSession,
    TokenUsage,
    TractorTelemetryRecord,
    YieldMonitorRecord,
)

# Generic type for repository entities
T = TypeVar("T")


class BaseAsyncRepository[T]:
    """Base repository for async database operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Parameters
        ----------
        session : AsyncSession
            Database session for async operations
        """
        self.session = session

    async def create(self, instance: T) -> T:
        """Create a new database record.

        Parameters
        ----------
        instance : Any
            Database model instance to create

        Returns
        -------
        Any
            Created instance with generated ID
        """
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def get_by_id(self, model_class: type[T], entity_id: str | int) -> T | None:
        """Get entity by ID.

        Parameters
        ----------
        model_class : type
            SQLAlchemy model class
        entity_id : str | int
            Entity ID

        Returns
        -------
        Optional[Any]
            Entity instance or None if not found
        """
        # Build query with proper attribute access
        query = select(model_class)

        # Try to determine the primary key attribute
        if hasattr(model_class, "id"):
            query = query.where(model_class.id == entity_id)
        elif hasattr(model_class, "equipment_id"):
            query = query.where(model_class.equipment_id == entity_id)
        else:
            # Fallback: use first column attribute
            column_attrs = [attr for attr in model_class.__table__.columns.keys()]
            if column_attrs:
                first_attr = getattr(model_class, column_attrs[0])
                query = query.where(first_attr == entity_id)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(self, instance: Any, **kwargs: Any) -> Any:
        """Update an existing entity.

        Parameters
        ----------
        instance : Any
            Entity instance to update
        **kwargs : Any
            Fields to update

        Returns
        -------
        Any
            Updated instance
        """
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, instance: Any) -> bool:
        """Delete an entity.

        Parameters
        ----------
        instance : Any
            Entity instance to delete

        Returns
        -------
        bool
            True if deletion was successful
        """
        await self.session.delete(instance)
        await self.session.flush()
        return True

    async def list_all(self, model_class: type, limit: int = 100, offset: int = 0) -> list[Any]:
        """List all entities with pagination.

        Parameters
        ----------
        model_class : type
            SQLAlchemy model class
        limit : int, default 100
            Maximum number of results
        offset : int, default 0
            Offset for pagination

        Returns
        -------
        list[Any]
            List of entity instances
        """
        result = await self.session.execute(select(model_class).offset(offset).limit(limit))
        return list(result.scalars().all())


class EquipmentAsyncRepository(BaseAsyncRepository[Equipment]):
    """Async repository for equipment management in agricultural operations."""

    async def create_equipment(
        self,
        equipment_id: str,
        isobus_address: int,
        equipment_type: str,
        manufacturer: str,
        model: str | None = None,
        serial_number: str | None = None,
        firmware_version: str | None = None,
        installation_date: datetime | None = None,
        status: str = "active",
    ) -> Equipment:
        """Create a new equipment record.

        Parameters
        ----------
        equipment_id : str
            Unique equipment identifier
        isobus_address : int
            ISOBUS address (0x00-0xFF)
        equipment_type : str
            Type of equipment (tractor, implement, sensor)
        manufacturer : str
            Equipment manufacturer
        model : str, optional
            Equipment model
        serial_number : str, optional
            Equipment serial number
        firmware_version : str, optional
            Equipment firmware version
        installation_date : datetime, optional
            Equipment installation date
        status : str, default "active"
            Equipment status (active, maintenance, retired)

        Returns
        -------
        Equipment
            Created equipment instance
        """
        equipment = Equipment(
            equipment_id=equipment_id,
            isobus_address=isobus_address,
            equipment_type=equipment_type,
            manufacturer=manufacturer,
            model=model,
            serial_number=serial_number,
            firmware_version=firmware_version,
            installation_date=installation_date,
            status=status,
        )
        return await self.create(equipment)

    async def get_equipment_by_isobus_address(self, isobus_address: int) -> Equipment | None:
        """Get equipment by ISOBUS address.

        Parameters
        ----------
        isobus_address : int
            ISOBUS address

        Returns
        -------
        Optional[Equipment]
            Equipment instance or None if not found
        """
        result = await self.session.execute(
            select(Equipment).where(Equipment.isobus_address == isobus_address)
        )
        return result.scalar_one_or_none()

    async def get_equipment_by_type(
        self, equipment_type: str, status: str | None = None
    ) -> list[Equipment]:
        """Get equipment by type and optional status.

        Parameters
        ----------
        equipment_type : str
            Type of equipment
        status : str, optional
            Equipment status filter

        Returns
        -------
        list[Equipment]
            List of equipment instances
        """
        query = select(Equipment).where(Equipment.equipment_type == equipment_type)
        if status:
            query = query.where(Equipment.status == status)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_equipment_status(self, equipment_id: str, status: str) -> Equipment | None:
        """Update equipment status.

        Parameters
        ----------
        equipment_id : str
            Equipment identifier
        status : str
            New status

        Returns
        -------
        Optional[Equipment]
            Updated equipment instance or None if not found
        """
        result = await self.session.execute(
            select(Equipment).where(Equipment.equipment_id == equipment_id)
        )
        equipment = result.scalar_one_or_none()

        if equipment:
            equipment.status = status
            await self.session.flush()
            await self.session.refresh(equipment)

        return equipment

    async def get_equipment_by_id(self, equipment_id: str) -> Equipment | None:
        """Get equipment by ID.

        Parameters
        ----------
        equipment_id : str
            Equipment identifier

        Returns
        -------
        Optional[Equipment]
            Equipment instance or None if not found
        """
        result = await self.session.execute(
            select(Equipment).where(Equipment.equipment_id == equipment_id)
        )
        return result.scalar_one_or_none()

    async def list_equipment(
        self, filters: dict | None = None, limit: int = 100, offset: int = 0
    ) -> list[Equipment]:
        """List all equipment with pagination and optional filtering.

        Parameters
        ----------
        filters : dict, optional
            Filter criteria (e.g., equipment_type, manufacturer)
        limit : int, default 100
            Maximum number of equipment to return
        offset : int, default 0
            Number of equipment to skip

        Returns
        -------
        list[Equipment]
            List of equipment instances
        """
        query = select(Equipment).offset(offset).limit(limit)

        if filters:
            if "equipment_type" in filters:
                query = query.where(Equipment.equipment_type == filters["equipment_type"])
            if "manufacturer" in filters:
                query = query.where(Equipment.manufacturer == filters["manufacturer"])

        result = await self.session.execute(query)
        return list(result.scalars().all())


class FieldAsyncRepository(BaseAsyncRepository[Field]):
    """Async repository for field management in agricultural operations."""

    async def create_field(
        self,
        field_id: str,
        field_name: str,
        crop_type: str | None = None,
        field_area_hectares: float | None = None,
        boundary_coordinates: list | None = None,
        soil_type: str | None = None,
        drainage_class: str | None = None,
        elevation_meters: float | None = None,
        slope_percentage: float | None = None,
    ) -> Field:
        """Create a new field record.

        Parameters
        ----------
        field_id : str
            Unique field identifier
        field_name : str
            Field name
        crop_type : str, optional
            Crop type grown in field
        field_area_hectares : float, optional
            Field area in hectares
        boundary_coordinates : list, optional
            List of (lat, lon) tuples defining field boundaries
        soil_type : str, optional
            Soil type classification
        drainage_class : str, optional
            Drainage classification
        elevation_meters : float, optional
            Field elevation in meters
        slope_percentage : float, optional
            Field slope percentage

        Returns
        -------
        Field
            Created field instance
        """
        field = Field(
            field_id=field_id,
            field_name=field_name,
            crop_type=crop_type,
            field_area_hectares=field_area_hectares,
            boundary_coordinates=boundary_coordinates,
            soil_type=soil_type,
            drainage_class=drainage_class,
            elevation_meters=elevation_meters,
            slope_percentage=slope_percentage,
        )
        return await self.create(field)

    async def get_fields_by_crop_type(self, crop_type: str) -> list[Field]:
        """Get fields by crop type.

        Parameters
        ----------
        crop_type : str
            Crop type filter

        Returns
        -------
        list[Field]
            List of field instances
        """
        result = await self.session.execute(select(Field).where(Field.crop_type == crop_type))
        return result.scalars().all()

    async def get_fields_by_area_range(
        self, min_area: float | None = None, max_area: float | None = None
    ) -> list[Field]:
        """Get fields by area range.

        Parameters
        ----------
        min_area : float, optional
            Minimum field area in hectares
        max_area : float, optional
            Maximum field area in hectares

        Returns
        -------
        list[Field]
            List of field instances
        """
        query = select(Field)

        if min_area is not None and max_area is not None:
            query = query.where(
                and_(Field.field_area_hectares >= min_area, Field.field_area_hectares <= max_area)
            )
        elif min_area is not None:
            query = query.where(Field.field_area_hectares >= min_area)
        elif max_area is not None:
            query = query.where(Field.field_area_hectares <= max_area)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def list_fields(self, limit: int = 100, offset: int = 0) -> list[Field]:
        """List all fields with pagination.

        Parameters
        ----------
        limit : int, default 100
            Maximum number of fields to return
        offset : int, default 0
            Number of fields to skip

        Returns
        -------
        list[Field]
            List of field instances
        """
        return await self.list_all(Field, limit=limit, offset=offset)


class ISOBUSMessageAsyncRepository(BaseAsyncRepository[ISOBUSMessageRecord]):
    """Async repository for ISOBUS message management in agricultural operations."""

    async def create_message(
        self,
        equipment_id: str,
        pgn: int,
        source_address: int,
        destination_address: int,
        data_payload: dict | None = None,
        priority_level: int = 0,
        timestamp: datetime | None = None,
    ) -> ISOBUSMessageRecord:
        """Create a new ISOBUS message record.

        Parameters
        ----------
        equipment_id : str
            Equipment identifier
        pgn : int
            Parameter Group Number
        source_address : int
            Source ISOBUS address
        destination_address : int
            Destination ISOBUS address
        data_payload : dict, optional
            Parsed message data
        priority_level : int, default 0
            Message priority level
        timestamp : datetime, optional
            Message timestamp

        Returns
        -------
        ISOBUSMessageRecord
            Created message instance
        """
        message = ISOBUSMessageRecord(
            equipment_id=equipment_id,
            pgn=pgn,
            source_address=source_address,
            destination_address=destination_address,
            data_payload=data_payload,
            priority_level=priority_level,
            timestamp=timestamp or datetime.now(UTC),
        )
        return await self.create(message)

    async def get_messages_by_equipment(
        self,
        equipment_id: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[ISOBUSMessageRecord]:
        """Get messages by equipment with optional time range.

        Parameters
        ----------
        equipment_id : str
            Equipment identifier
        start_time : datetime, optional
            Start time for message retrieval
        end_time : datetime, optional
            End time for message retrieval

        Returns
        -------
        list[ISOBUSMessageRecord]
            List of message instances
        """
        query = select(ISOBUSMessageRecord).where(ISOBUSMessageRecord.equipment_id == equipment_id)

        if start_time:
            query = query.where(ISOBUSMessageRecord.timestamp >= start_time)
        if end_time:
            query = query.where(ISOBUSMessageRecord.timestamp <= end_time)

        query = query.order_by(ISOBUSMessageRecord.timestamp.desc())

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_messages_by_pgn(self, pgn: int, limit: int = 1000) -> list[ISOBUSMessageRecord]:
        """Get messages by PGN (Parameter Group Number).

        Parameters
        ----------
        pgn : int
            Parameter Group Number
        limit : int, default 1000
            Maximum number of messages to retrieve

        Returns
        -------
        list[ISOBUSMessageRecord]
            List of message instances
        """
        result = await self.session.execute(
            select(ISOBUSMessageRecord)
            .where(ISOBUSMessageRecord.pgn == pgn)
            .order_by(ISOBUSMessageRecord.timestamp.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_messages_by_priority_range(
        self, min_priority: int, max_priority: int
    ) -> list[ISOBUSMessageRecord]:
        """Get messages by priority range.

        Parameters
        ----------
        min_priority : int
            Minimum priority level
        max_priority : int
            Maximum priority level

        Returns
        -------
        list[ISOBUSMessageRecord]
            List of message instances
        """
        result = await self.session.execute(
            select(ISOBUSMessageRecord).where(
                and_(
                    ISOBUSMessageRecord.priority_level >= min_priority,
                    ISOBUSMessageRecord.priority_level <= max_priority,
                )
            )
        )
        return result.scalars().all()


class AgriculturalSensorAsyncRepository(BaseAsyncRepository[AgriculturalSensorRecord]):
    """Async repository for agricultural sensor data management."""

    async def create_sensor_reading(
        self,
        equipment_id: str,
        sensor_type: str,
        sensor_value: float,
        unit: str,
        field_id: str | None = None,
        gps_latitude: float | None = None,
        gps_longitude: float | None = None,
        quality_indicator: str = "good",
        calibration_date: datetime | None = None,
        timestamp: datetime | None = None,
    ) -> AgriculturalSensorRecord:
        """Create a new sensor reading record.

        Parameters
        ----------
        equipment_id : str
            Equipment identifier
        sensor_type : str
            Type of sensor
        sensor_value : float
            Sensor reading value
        unit : str
            Unit of measurement
        field_id : str, optional
            Field identifier
        gps_latitude : float, optional
            GPS latitude coordinate
        gps_longitude : float, optional
            GPS longitude coordinate
        quality_indicator : str, default "good"
            Data quality indicator (good, warning, error)
        calibration_date : datetime, optional
            Sensor calibration date
        timestamp : datetime, optional
            Reading timestamp

        Returns
        -------
        AgriculturalSensorRecord
            Created sensor reading instance
        """
        reading = AgriculturalSensorRecord(
            equipment_id=equipment_id,
            sensor_type=sensor_type,
            sensor_value=sensor_value,
            unit=unit,
            field_id=field_id,
            gps_latitude=gps_latitude,
            gps_longitude=gps_longitude,
            quality_indicator=quality_indicator,
            calibration_date=calibration_date,
            timestamp=timestamp or datetime.now(UTC),
        )
        return await self.create(reading)

    async def get_sensor_readings_by_equipment(
        self,
        equipment_id: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        sensor_type: str | None = None,
    ) -> list[AgriculturalSensorRecord]:
        """Get sensor readings by equipment with optional filters.

        Parameters
        ----------
        equipment_id : str
            Equipment identifier
        start_time : datetime, optional
            Start time for reading retrieval
        end_time : datetime, optional
            End time for reading retrieval
        sensor_type : str, optional
            Sensor type filter

        Returns
        -------
        list[AgriculturalSensorRecord]
            List of sensor reading instances
        """
        query = select(AgriculturalSensorRecord).where(
            AgriculturalSensorRecord.equipment_id == equipment_id
        )

        if start_time:
            query = query.where(AgriculturalSensorRecord.timestamp >= start_time)
        if end_time:
            query = query.where(AgriculturalSensorRecord.timestamp <= end_time)
        if sensor_type:
            query = query.where(AgriculturalSensorRecord.sensor_type == sensor_type)

        query = query.order_by(AgriculturalSensorRecord.timestamp.desc())

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_sensor_readings_by_field_and_type(
        self,
        field_id: str,
        sensor_type: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[AgriculturalSensorRecord]:
        """Get sensor readings by field and sensor type.

        Parameters
        ----------
        field_id : str
            Field identifier
        sensor_type : str
            Sensor type filter
        start_time : datetime, optional
            Start time for reading retrieval
        end_time : datetime, optional
            End time for reading retrieval

        Returns
        -------
        list[AgriculturalSensorRecord]
            List of sensor reading instances
        """
        query = select(AgriculturalSensorRecord).where(
            and_(
                AgriculturalSensorRecord.field_id == field_id,
                AgriculturalSensorRecord.sensor_type == sensor_type,
            )
        )

        if start_time:
            query = query.where(AgriculturalSensorRecord.timestamp >= start_time)
        if end_time:
            query = query.where(AgriculturalSensorRecord.timestamp <= end_time)

        query = query.order_by(AgriculturalSensorRecord.timestamp.desc())

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_sensor_statistics(
        self,
        equipment_id: str,
        sensor_type: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict[str, float]:
        """Get statistical summary for sensor readings.

        Parameters
        ----------
        equipment_id : str
            Equipment identifier
        sensor_type : str
            Sensor type
        start_time : datetime, optional
            Start time for analysis
        end_time : datetime, optional
            End time for analysis

        Returns
        -------
        dict[str, float]
            Statistical summary (count, average, min, max)
        """
        query = select(
            func.count(AgriculturalSensorRecord.id).label("count"),
            func.avg(AgriculturalSensorRecord.sensor_value).label("average"),
            func.min(AgriculturalSensorRecord.sensor_value).label("minimum"),
            func.max(AgriculturalSensorRecord.sensor_value).label("maximum"),
        ).where(
            and_(
                AgriculturalSensorRecord.equipment_id == equipment_id,
                AgriculturalSensorRecord.sensor_type == sensor_type,
            )
        )

        if start_time:
            query = query.where(AgriculturalSensorRecord.timestamp >= start_time)
        if end_time:
            query = query.where(AgriculturalSensorRecord.timestamp <= end_time)

        result = await self.session.execute(query)
        stats = result.first()

        return {
            "count": stats.count or 0,
            "average": stats.average or 0.0,
            "minimum": stats.minimum or 0.0,
            "maximum": stats.maximum or 0.0,
        }


class TractorTelemetryAsyncRepository(BaseAsyncRepository[TractorTelemetryRecord]):
    """Async repository for tractor telemetry data management."""

    async def create_telemetry_reading(
        self,
        equipment_id: str,
        vehicle_speed: float,
        fuel_level: float,
        engine_temperature: float,
        operational_mode: str,
        gps_latitude: float | None = None,
        gps_longitude: float | None = None,
        engine_hours: float | None = None,
        hydraulic_pressure: float | None = None,
        timestamp: datetime | None = None,
    ) -> TractorTelemetryRecord:
        """Create a new telemetry reading record.

        Parameters
        ----------
        equipment_id : str
            Equipment identifier
        vehicle_speed : float
            Vehicle speed in km/h
        fuel_level : float
            Fuel level percentage (0-100)
        engine_temperature : float
            Engine temperature in celsius
        operational_mode : str
            Current operational mode
        gps_latitude : float, optional
            GPS latitude coordinate
        gps_longitude : float, optional
            GPS longitude coordinate
        engine_hours : float, optional
            Engine hours
        hydraulic_pressure : float, optional
            Hydraulic pressure in bar
        timestamp : datetime, optional
            Reading timestamp

        Returns
        -------
        TractorTelemetryRecord
            Created telemetry reading instance
        """
        reading = TractorTelemetryRecord(
            equipment_id=equipment_id,
            vehicle_speed=vehicle_speed,
            fuel_level=fuel_level,
            engine_temperature=engine_temperature,
            operational_mode=operational_mode,
            gps_latitude=gps_latitude,
            gps_longitude=gps_longitude,
            engine_hours=engine_hours,
            hydraulic_pressure=hydraulic_pressure,
            timestamp=timestamp or datetime.now(UTC),
        )
        return await self.create(reading)

    async def get_telemetry_by_equipment(
        self,
        equipment_id: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        operational_mode: str | None = None,
    ) -> list[TractorTelemetryRecord]:
        """Get telemetry readings by equipment with optional filters.

        Parameters
        ----------
        equipment_id : str
            Equipment identifier
        start_time : datetime, optional
            Start time for reading retrieval
        end_time : datetime, optional
            End time for reading retrieval
        operational_mode : str, optional
            Operational mode filter

        Returns
        -------
        list[TractorTelemetryRecord]
            List of telemetry reading instances
        """
        query = select(TractorTelemetryRecord).where(
            TractorTelemetryRecord.equipment_id == equipment_id
        )

        if start_time:
            query = query.where(TractorTelemetryRecord.timestamp >= start_time)
        if end_time:
            query = query.where(TractorTelemetryRecord.timestamp <= end_time)
        if operational_mode:
            query = query.where(TractorTelemetryRecord.operational_mode == operational_mode)

        query = query.order_by(TractorTelemetryRecord.timestamp.desc())

        result = await self.session.execute(query)
        return result.scalars().all()


class YieldMonitorAsyncRepository(BaseAsyncRepository[YieldMonitorRecord]):
    """Async repository for yield monitoring data management."""

    async def create_yield_reading(
        self,
        equipment_id: str,
        field_id: str,
        crop_type: str,
        yield_volume: float,
        moisture_content: float,
        gps_latitude: float,
        gps_longitude: float,
        harvest_width: float,
        harvest_speed: float,
        grain_temperature: float | None = None,
        timestamp: datetime | None = None,
    ) -> YieldMonitorRecord:
        """Create a new yield reading record.

        Parameters
        ----------
        equipment_id : str
            Equipment identifier
        field_id : str
            Field identifier
        crop_type : str
            Crop type
        yield_volume : float
            Yield volume in tons per hectare
        moisture_content : float
            Moisture content percentage
        gps_latitude : float
            GPS latitude coordinate
        gps_longitude : float
            GPS longitude coordinate
        harvest_width : float
            Harvest width in meters
        harvest_speed : float
            Harvest speed in km/h
        grain_temperature : float, optional
            Grain temperature in celsius
        timestamp : datetime, optional
            Reading timestamp

        Returns
        -------
        YieldMonitorRecord
            Created yield reading instance
        """
        reading = YieldMonitorRecord(
            equipment_id=equipment_id,
            field_id=field_id,
            crop_type=crop_type,
            yield_volume=yield_volume,
            moisture_content=moisture_content,
            gps_latitude=gps_latitude,
            gps_longitude=gps_longitude,
            harvest_width=harvest_width,
            harvest_speed=harvest_speed,
            grain_temperature=grain_temperature,
            timestamp=timestamp or datetime.now(UTC),
        )
        return await self.create(reading)


class TokenUsageAsyncRepository(BaseAsyncRepository[TokenUsage]):
    """Async repository for token usage tracking in agricultural AI operations."""

    async def create_token_usage(
        self,
        agent_id: str,
        task_id: str,
        tokens_used: float,
        model_name: str,
        timestamp: datetime | None = None,
    ) -> TokenUsage:
        """Create a new token usage record.

        Parameters
        ----------
        agent_id : str
            Agent identifier
        task_id : str
            Task identifier
        tokens_used : float
            Number of tokens used
        model_name : str
            Name of the model used
        timestamp : datetime, optional
            Usage timestamp

        Returns
        -------
        TokenUsage
            Created token usage instance
        """
        usage = TokenUsage(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            task_id=task_id,
            tokens_used=tokens_used,
            model_name=model_name,
            timestamp=timestamp or datetime.now(UTC),
        )
        return await self.create(usage)

    async def get_token_usage_by_agent(
        self,
        agent_id: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[TokenUsage]:
        """Get token usage by agent with optional time range.

        Parameters
        ----------
        agent_id : str
            Agent identifier
        start_time : datetime, optional
            Start time for usage retrieval
        end_time : datetime, optional
            End time for usage retrieval

        Returns
        -------
        list[TokenUsage]
            List of token usage instances
        """
        query = select(TokenUsage).where(TokenUsage.agent_id == agent_id)

        if start_time:
            query = query.where(TokenUsage.timestamp >= start_time)
        if end_time:
            query = query.where(TokenUsage.timestamp <= end_time)

        query = query.order_by(TokenUsage.timestamp.desc())

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_token_usage_by_task(
        self,
        task_id: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[TokenUsage]:
        """Get token usage by task with optional time range.

        Parameters
        ----------
        task_id : str
            Task identifier
        start_time : datetime, optional
            Start time for usage retrieval
        end_time : datetime, optional
            End time for usage retrieval

        Returns
        -------
        list[TokenUsage]
            List of token usage instances
        """
        query = select(TokenUsage).where(TokenUsage.task_id == task_id)

        if start_time:
            query = query.where(TokenUsage.timestamp >= start_time)
        if end_time:
            query = query.where(TokenUsage.timestamp <= end_time)

        query = query.order_by(TokenUsage.timestamp.desc())

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_token_usage_statistics(
        self,
        agent_id: str | None = None,
        task_id: str | None = None,
        model_name: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict[str, Any]:
        """Get token usage statistics with optional filters.

        Parameters
        ----------
        agent_id : str, optional
            Agent identifier filter
        task_id : str, optional
            Task identifier filter
        model_name : str, optional
            Model name filter
        start_time : datetime, optional
            Start time for analysis
        end_time : datetime, optional
            End time for analysis

        Returns
        -------
        dict[str, Any]
            Statistical summary of token usage
        """
        query = select(
            func.count(TokenUsage.id).label("total_usage_count"),
            func.sum(TokenUsage.tokens_used).label("total_tokens_used"),
            func.avg(TokenUsage.tokens_used).label("average_tokens_per_usage"),
            func.min(TokenUsage.tokens_used).label("minimum_tokens_used"),
            func.max(TokenUsage.tokens_used).label("maximum_tokens_used"),
        )

        # Apply filters
        conditions = []
        if agent_id:
            conditions.append(TokenUsage.agent_id == agent_id)
        if task_id:
            conditions.append(TokenUsage.task_id == task_id)
        if model_name:
            conditions.append(TokenUsage.model_name == model_name)
        if start_time:
            conditions.append(TokenUsage.timestamp >= start_time)
        if end_time:
            conditions.append(TokenUsage.timestamp <= end_time)

        if conditions:
            query = query.where(and_(*conditions))

        result = await self.session.execute(query)
        stats = result.first()

        return {
            "total_usage_count": stats.total_usage_count or 0,
            "total_tokens_used": stats.total_tokens_used or 0.0,
            "average_tokens_per_usage": stats.average_tokens_per_usage or 0.0,
            "minimum_tokens_used": stats.minimum_tokens_used or 0.0,
            "maximum_tokens_used": stats.maximum_tokens_used or 0.0,
        }

    async def delete_old_token_usage(self, cutoff_date: datetime) -> int:
        """Delete token usage records older than cutoff date.

        Parameters
        ----------
        cutoff_date : datetime
            Cutoff date for deletion

        Returns
        -------
        int
            Number of deleted records
        """
        result = await self.session.execute(
            delete(TokenUsage).where(TokenUsage.timestamp < cutoff_date)
        )
        await self.session.flush()
        return result.rowcount


class OperationalSessionAsyncRepository(BaseAsyncRepository[OperationalSession]):
    """Async repository for operational session management in agricultural operations."""

    async def create_session(
        self,
        session_id: str,
        equipment_id: str,
        field_id: str | None = None,
        operation_type: str = "cultivation",
        start_time: datetime | None = None,
        operator_id: str | None = None,
        weather_conditions: str | None = None,
        soil_conditions: str | None = None,
        notes: str | None = None,
    ) -> OperationalSession:
        """Create a new operational session.

        Parameters
        ----------
        session_id : str
            Unique session identifier
        equipment_id : str
            Equipment identifier
        field_id : str, optional
            Field identifier
        operation_type : str, default "cultivation"
            Type of operation (planting, cultivation, harvesting)
        start_time : datetime, optional
            Session start time
        operator_id : str, optional
            Operator identifier
        weather_conditions : str, optional
            Weather conditions during operation
        soil_conditions : str, optional
            Soil conditions during operation
        notes : str, optional
            Additional session notes

        Returns
        -------
        OperationalSession
            Created operational session instance
        """
        session = OperationalSession(
            session_id=session_id,
            equipment_id=equipment_id,
            field_id=field_id,
            operation_type=operation_type,
            start_time=start_time or datetime.now(UTC),
            operator_id=operator_id,
            weather_conditions=weather_conditions,
            soil_conditions=soil_conditions,
            notes=notes,
            session_status="active",
        )
        return await self.create(session)

    async def update_session_end(
        self,
        session_id: str,
        end_time: datetime,
        total_area_covered: float | None = None,
        total_yield: float | None = None,
        average_speed: float | None = None,
        fuel_consumed: float | None = None,
    ) -> OperationalSession | None:
        """Update operational session with end information.

        Parameters
        ----------
        session_id : str
            Session identifier
        end_time : datetime
            Session end time
        total_area_covered : float, optional
            Total area covered in hectares
        total_yield : float, optional
            Total yield (for harvest operations)
        average_speed : float, optional
            Average operational speed
        fuel_consumed : float, optional
            Total fuel consumed

        Returns
        -------
        Optional[OperationalSession]
            Updated session instance or None if not found
        """
        result = await self.session.execute(
            select(OperationalSession).where(OperationalSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()

        if session:
            session.end_time = end_time
            session.total_area_covered = total_area_covered
            session.total_yield = total_yield
            session.average_speed = average_speed
            session.fuel_consumed = fuel_consumed
            session.session_status = "completed"

            await self.session.flush()
            await self.session.refresh(session)

        return session

    async def get_active_sessions(self) -> list[OperationalSession]:
        """Get all currently active operational sessions.

        Returns
        -------
        list[OperationalSession]
            List of active session instances
        """
        result = await self.session.execute(
            select(OperationalSession).where(OperationalSession.session_status == "active")
        )
        return result.scalars().all()

    async def get_sessions_by_equipment_and_type(
        self,
        equipment_id: str,
        operation_type: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[OperationalSession]:
        """Get operational sessions by equipment and operation type.

        Parameters
        ----------
        equipment_id : str
            Equipment identifier
        operation_type : str
            Type of operation
        start_time : datetime, optional
            Start time for session retrieval
        end_time : datetime, optional
            End time for session retrieval

        Returns
        -------
        list[OperationalSession]
            List of session instances
        """
        query = select(OperationalSession).where(
            and_(
                OperationalSession.equipment_id == equipment_id,
                OperationalSession.operation_type == operation_type,
            )
        )

        if start_time:
            query = query.where(OperationalSession.start_time >= start_time)
        if end_time:
            query = query.where(OperationalSession.end_time <= end_time)

        query = query.order_by(OperationalSession.start_time.desc())

        result = await self.session.execute(query)
        return result.scalars().all()


class UnitOfWork:
    """Unit of Work pattern for async database transactions in agricultural operations.

    Provides a consistent way to manage multiple repository operations within
    a single transaction, ensuring data consistency across agricultural operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize unit of work with database session.

        Parameters
        ----------
        session : AsyncSession
            Database session for transactions
        """
        self.session = session
        self._repositories = {}
        self._new = set()
        self._dirty = set()
        self._deleted = set()

    def __enter__(self) -> UnitOfWork:
        """Enter context manager."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager and commit or rollback transaction."""
        if exc_type is None:
            self.commit()
        else:
            import asyncio

            asyncio.run(self.rollback())

    async def __aenter__(self) -> UnitOfWork:
        """Enter async context manager."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager and commit or rollback transaction."""
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()

    def get_repository(self, repository_class: type) -> BaseAsyncRepository:
        """Get or create repository instance.

        Parameters
        ----------
        repository_class : type
            Repository class to instantiate

        Returns
        -------
        BaseAsyncRepository
            Repository instance
        """
        if repository_class not in self._repositories:
            self._repositories[repository_class] = repository_class(self.session)

        return self._repositories[repository_class]

    @property
    def equipment(self) -> EquipmentAsyncRepository:
        """Get equipment repository."""
        return self.get_repository(EquipmentAsyncRepository)

    @property
    def field(self) -> FieldAsyncRepository:
        """Get field repository."""
        return self.get_repository(FieldAsyncRepository)

    @property
    def isobus_message(self) -> ISOBUSMessageAsyncRepository:
        """Get ISOBUS message repository."""
        return self.get_repository(ISOBUSMessageAsyncRepository)

    @property
    def sensor_data(self) -> AgriculturalSensorAsyncRepository:
        """Get sensor data repository."""
        return self.get_repository(AgriculturalSensorAsyncRepository)

    @property
    def telemetry(self) -> TractorTelemetryAsyncRepository:
        """Get telemetry repository."""
        return self.get_repository(TractorTelemetryAsyncRepository)

    @property
    def yield_monitor(self) -> YieldMonitorAsyncRepository:
        """Get yield monitor repository."""
        return self.get_repository(YieldMonitorAsyncRepository)

    @property
    def token_usage(self) -> TokenUsageAsyncRepository:
        """Get token usage repository."""
        return self.get_repository(TokenUsageAsyncRepository)

    @property
    def operational_session(self) -> OperationalSessionAsyncRepository:
        """Get operational session repository."""
        return self.get_repository(OperationalSessionAsyncRepository)

    async def commit(self) -> None:
        """Commit all changes to the database."""
        # Flush to get generated IDs and validate constraints
        await self.session.flush()

        # Track changes for auditing and optimization
        self._track_changes()

        # Commit transaction
        await self.session.commit()

        # Clear tracking sets
        self._new.clear()
        self._dirty.clear()
        self._deleted.clear()

    async def rollback(self) -> None:
        """Rollback all changes."""
        await self.session.rollback()
        self._new.clear()
        self._dirty.clear()
        self._deleted.clear()

    def _track_changes(self) -> None:
        """Track changes for auditing and performance optimization."""
        # Track newly created instances
        for instance in self._new:
            if hasattr(instance, "created_at") and instance.created_at:
                # Log creation event for agricultural operations tracking
                pass

        # Track updated instances
        for instance in self._dirty:
            if hasattr(instance, "updated_at"):
                instance.updated_at = datetime.now(UTC)

        # Track deleted instances
        for _instance in self._deleted:
            # Log deletion event for agricultural operations tracking
            pass


# Async session context manager
async def get_async_session(
    database_manager: AsyncDatabaseManager,
) -> AsyncGenerator[UnitOfWork, None]:
    """Get async database session with unit of work pattern.

    Parameters
    ----------
    database_manager : AsyncDatabaseManager
        Database manager instance

    Yields
    ------
    UnitOfWork
        Unit of work with database session
    """
    async with database_manager.get_session() as session:
        yield UnitOfWork(session)
