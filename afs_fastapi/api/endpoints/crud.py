"""
Basic CRUD API endpoints for agricultural equipment and field management.

This module provides standard RESTful CRUD operations for the core agricultural
entities that were missing from the original API design.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from afs_fastapi.api.core.response_models import StandardResponse
from afs_fastapi.api.core.validation_schemas import (
    EquipmentCreateRequest,
    EquipmentResponse,
    EquipmentUpdateRequest,
    FieldCreateRequest,
    FieldResponse,
    FieldUpdateRequest,
    validate_equipment_data,
    validate_field_data,
)
from afs_fastapi.database.async_repository import (
    UnitOfWork,
)
from afs_fastapi.database.optimized_db_config import get_optimized_db_config

router = APIRouter()
logger = logging.getLogger(__name__)


async def get_db_session() -> AsyncSession:
    """Get database session for CRUD operations."""
    from afs_fastapi.database.optimized_db_config import (
        get_optimized_session,
    )

    # Initialize the database pool if not already done
    db_config = await get_optimized_db_config()
    await db_config.initialize_pool()

    # Get session from the initialized pool
    async for session in get_optimized_session():
        yield session


@router.get(
    "/equipment",
    response_model=list[EquipmentResponse],
    tags=["equipment"],
    summary="List all equipment",
    description="Retrieve a list of all agricultural equipment in the system.",
)
async def list_equipment(
    session: AsyncSession = Depends(get_db_session),
    equipment_type: str | None = Query(None, description="Filter by equipment type"),
    manufacturer: str | None = Query(None, description="Filter by manufacturer"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
) -> list[EquipmentResponse]:
    """
    Get a paginated list of equipment with optional filtering.
    """
    try:
        async with UnitOfWork(session) as uow:
            equipment_repo = uow.equipment

            # Build filter criteria
            filters = {}
            if equipment_type:
                filters["equipment_type"] = equipment_type
            if manufacturer:
                filters["manufacturer"] = manufacturer

            # Get equipment list
            equipment_list = await equipment_repo.list_equipment(
                filters=filters, limit=limit, offset=offset
            )

            return [
                EquipmentResponse(
                    equipment_id=eq.equipment_id,
                    isobus_address=eq.isobus_address,
                    equipment_type=eq.equipment_type,
                    manufacturer=eq.manufacturer,
                    model=eq.model,
                    serial_number=eq.serial_number,
                    firmware_version=eq.firmware_version,
                    installation_date=eq.installation_date,
                    status=eq.status,
                    created_at=eq.created_at,
                    updated_at=eq.updated_at,
                )
                for eq in equipment_list
            ]

    except Exception as e:
        logger.error(f"Error listing equipment: {e}")
        raise HTTPException(status_code=500, detail="Failed to list equipment")


@router.post(
    "/equipment",
    response_model=EquipmentResponse,
    tags=["equipment"],
    summary="Create new equipment",
    description="Add a new piece of agricultural equipment to the system.",
)
async def create_equipment(
    equipment_data: EquipmentCreateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> EquipmentResponse:
    """
    Create a new equipment record.
    """
    try:
        # Validate input data
        validate_equipment_data(equipment_data.model_dump())

        async with UnitOfWork(session) as uow:
            equipment_repo = uow.equipment

            # Check if equipment ID already exists
            existing = await equipment_repo.get_equipment_by_id(equipment_data.equipment_id)
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Equipment with ID {equipment_data.equipment_id} already exists",
                )

            # Check if ISOBUS address is already in use
            existing_by_address = await equipment_repo.get_equipment_by_isobus_address(
                equipment_data.isobus_address
            )
            if existing_by_address:
                raise HTTPException(
                    status_code=400,
                    detail=f"ISOBUS address {equipment_data.isobus_address} is already in use",
                )

            # Create equipment
            equipment = await equipment_repo.create_equipment(
                equipment_id=equipment_data.equipment_id,
                isobus_address=equipment_data.isobus_address,
                equipment_type=equipment_data.equipment_type,
                manufacturer=equipment_data.manufacturer,
                model=equipment_data.model,
                serial_number=equipment_data.serial_number,
                firmware_version=equipment_data.firmware_version,
                installation_date=equipment_data.installation_date,
            )

            return EquipmentResponse(
                equipment_id=equipment.equipment_id,
                isobus_address=equipment.isobus_address,
                equipment_type=equipment.equipment_type,
                manufacturer=equipment.manufacturer,
                model=equipment.model,
                serial_number=equipment.serial_number,
                firmware_version=equipment.firmware_version,
                installation_date=equipment.installation_date,
                status=equipment.status,
                created_at=equipment.created_at,
                updated_at=equipment.updated_at,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating equipment: {e}")
        raise HTTPException(status_code=500, detail="Failed to create equipment")


@router.get(
    "/equipment/{equipment_id}",
    response_model=EquipmentResponse,
    tags=["equipment"],
    summary="Get equipment by ID",
    description="Retrieve detailed information about a specific piece of equipment.",
)
async def get_equipment(
    equipment_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> EquipmentResponse:
    """
    Get equipment details by ID.
    """
    try:
        async with UnitOfWork(session) as uow:
            equipment_repo = uow.equipment

            equipment = await equipment_repo.get_equipment_by_id(equipment_id)
            if not equipment:
                raise HTTPException(
                    status_code=404, detail=f"Equipment with ID {equipment_id} not found"
                )

            return EquipmentResponse(
                equipment_id=equipment.equipment_id,
                isobus_address=equipment.isobus_address,
                equipment_type=equipment.equipment_type,
                manufacturer=equipment.manufacturer,
                model=equipment.model,
                serial_number=equipment.serial_number,
                firmware_version=equipment.firmware_version,
                installation_date=equipment.installation_date,
                status=equipment.status,
                created_at=equipment.created_at,
                updated_at=equipment.updated_at,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting equipment: {e}")
        raise HTTPException(status_code=500, detail="Failed to get equipment")


@router.put(
    "/equipment/{equipment_id}",
    response_model=EquipmentResponse,
    tags=["equipment"],
    summary="Update equipment",
    description="Update information for an existing piece of equipment.",
)
async def update_equipment(
    equipment_id: str,
    equipment_data: EquipmentUpdateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> EquipmentResponse:
    """
    Update equipment information.
    """
    try:
        # Validate input data
        validate_equipment_data(equipment_data.model_dump())

        async with UnitOfWork(session) as uow:
            equipment_repo = uow.equipment

            # Check if equipment exists
            equipment = await equipment_repo.get_equipment_by_id(equipment_id)
            if not equipment:
                raise HTTPException(
                    status_code=404, detail=f"Equipment with ID {equipment_id} not found"
                )

            # Check ISOBUS address conflict if changed
            if equipment_data.isobus_address != equipment.isobus_address:
                existing = await equipment_repo.get_equipment_by_isobus_address(
                    equipment_data.isobus_address
                )
                if existing and existing.equipment_id != equipment_id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"ISOBUS address {equipment_data.isobus_address} is already in use",
                    )

            # Update equipment
            updated_equipment = await equipment_repo.update_equipment(
                equipment_id=equipment_id,
                isobus_address=equipment_data.isobus_address,
                equipment_type=equipment_data.equipment_type,
                manufacturer=equipment_data.manufacturer,
                model=equipment_data.model,
                serial_number=equipment_data.serial_number,
                firmware_version=equipment_data.firmware_version,
                installation_date=equipment_data.installation_date,
                status=equipment_data.status,
            )

            return EquipmentResponse(
                equipment_id=updated_equipment.equipment_id,
                isobus_address=updated_equipment.isobus_address,
                equipment_type=updated_equipment.equipment_type,
                manufacturer=updated_equipment.manufacturer,
                model=updated_equipment.model,
                serial_number=updated_equipment.serial_number,
                firmware_version=updated_equipment.firmware_version,
                installation_date=updated_equipment.installation_date,
                status=updated_equipment.status,
                created_at=updated_equipment.created_at,
                updated_at=updated_equipment.updated_at,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating equipment: {e}")
        raise HTTPException(status_code=500, detail="Failed to update equipment")


@router.delete(
    "/equipment/{equipment_id}",
    response_model=StandardResponse,
    tags=["equipment"],
    summary="Delete equipment",
    description="Remove a piece of equipment from the system.",
)
async def delete_equipment(
    equipment_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> StandardResponse:
    """
    Delete equipment by ID.
    """
    try:
        async with UnitOfWork(session) as uow:
            equipment_repo = uow.equipment

            # Check if equipment exists
            equipment = await equipment_repo.get_equipment_by_id(equipment_id)
            if not equipment:
                raise HTTPException(
                    status_code=404, detail=f"Equipment with ID {equipment_id} not found"
                )

            # Delete equipment
            success = await equipment_repo.delete_equipment(equipment_id)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to delete equipment")

            return StandardResponse(
                success=True, message=f"Equipment {equipment_id} deleted successfully"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting equipment: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete equipment")


# Field CRUD Endpoints
@router.get(
    "/fields",
    response_model=list[FieldResponse],
    tags=["fields"],
    summary="List all fields",
    description="Retrieve a list of all agricultural fields in the system.",
)
async def list_fields(
    session: AsyncSession = Depends(get_db_session),
    crop_type: str | None = Query(None, description="Filter by crop type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
) -> list[FieldResponse]:
    """
    Get a paginated list of fields with optional filtering.
    """
    try:
        async with UnitOfWork(session) as uow:
            field_repo = uow.field

            # Build filter criteria
            filters = {}
            if crop_type:
                filters["crop_type"] = crop_type

            # Get field list
            field_list = await field_repo.list_fields(filters=filters, limit=limit, offset=offset)

            return [
                FieldResponse(
                    field_id=field.field_id,
                    field_name=field.field_name,
                    crop_type=field.crop_type,
                    field_area_hectares=field.field_area_hectares,
                    boundary_coordinates=field.boundary_coordinates,
                    soil_type=field.soil_type,
                    drainage_class=field.drainage_class,
                    elevation_meters=field.elevation_meters,
                    slope_percentage=field.slope_percentage,
                    created_at=field.created_at,
                    updated_at=field.updated_at,
                )
                for field in field_list
            ]

    except Exception as e:
        logger.error(f"Error listing fields: {e}")
        raise HTTPException(status_code=500, detail="Failed to list fields")


@router.post(
    "/fields",
    response_model=FieldResponse,
    tags=["fields"],
    summary="Create new field",
    description="Add a new agricultural field to the system.",
)
async def create_field(
    field_data: FieldCreateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> FieldResponse:
    """
    Create a new field record.
    """
    try:
        # Validate input data
        validate_field_data(field_data.model_dump())

        async with UnitOfWork(session) as uow:
            field_repo = uow.field

            # Check if field ID already exists
            existing = await field_repo.get_field_by_id(field_data.field_id)
            if existing:
                raise HTTPException(
                    status_code=400, detail=f"Field with ID {field_data.field_id} already exists"
                )

            # Create field
            field = await field_repo.create_field(
                field_id=field_data.field_id,
                field_name=field_data.field_name,
                crop_type=field_data.crop_type,
                field_area_hectares=field_data.field_area_hectares,
                boundary_coordinates=field_data.boundary_coordinates,
                soil_type=field_data.soil_type,
                drainage_class=field_data.drainage_class,
                elevation_meters=field_data.elevation_meters,
                slope_percentage=field_data.slope_percentage,
            )

            return FieldResponse(
                field_id=field.field_id,
                field_name=field.field_name,
                crop_type=field.crop_type,
                field_area_hectares=field.field_area_hectares,
                boundary_coordinates=field.boundary_coordinates,
                soil_type=field.soil_type,
                drainage_class=field.drainage_class,
                elevation_meters=field.elevation_meters,
                slope_percentage=field.slope_percentage,
                created_at=field.created_at,
                updated_at=field.updated_at,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating field: {e}")
        raise HTTPException(status_code=500, detail="Failed to create field")


@router.get(
    "/fields/{field_id}",
    response_model=FieldResponse,
    tags=["fields"],
    summary="Get field by ID",
    description="Retrieve detailed information about a specific field.",
)
async def get_field(
    field_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> FieldResponse:
    """
    Get field details by ID.
    """
    try:
        async with UnitOfWork(session) as uow:
            field_repo = uow.field

            field = await field_repo.get_field_by_id(field_id)
            if not field:
                raise HTTPException(status_code=404, detail=f"Field with ID {field_id} not found")

            return FieldResponse(
                field_id=field.field_id,
                field_name=field.field_name,
                crop_type=field.crop_type,
                field_area_hectares=field.field_area_hectares,
                boundary_coordinates=field.boundary_coordinates,
                soil_type=field.soil_type,
                drainage_class=field.drainage_class,
                elevation_meters=field.elevation_meters,
                slope_percentage=field.slope_percentage,
                created_at=field.created_at,
                updated_at=field.updated_at,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting field: {e}")
        raise HTTPException(status_code=500, detail="Failed to get field")


@router.put(
    "/fields/{field_id}",
    response_model=FieldResponse,
    tags=["fields"],
    summary="Update field",
    description="Update information for an existing field.",
)
async def update_field(
    field_id: str,
    field_data: FieldUpdateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> FieldResponse:
    """
    Update field information.
    """
    try:
        # Validate input data
        validate_field_data(field_data.model_dump())

        async with UnitOfWork(session) as uow:
            field_repo = uow.field

            # Check if field exists
            field = await field_repo.get_field_by_id(field_id)
            if not field:
                raise HTTPException(status_code=404, detail=f"Field with ID {field_id} not found")

            # Update field
            updated_field = await field_repo.update_field(
                field_id=field_id,
                field_name=field_data.field_name,
                crop_type=field_data.crop_type,
                field_area_hectares=field_data.field_area_hectares,
                boundary_coordinates=field_data.boundary_coordinates,
                soil_type=field_data.soil_type,
                drainage_class=field_data.drainage_class,
                elevation_meters=field_data.elevation_meters,
                slope_percentage=field_data.slope_percentage,
            )

            return FieldResponse(
                field_id=updated_field.field_id,
                field_name=updated_field.field_name,
                crop_type=updated_field.crop_type,
                field_area_hectares=updated_field.field_area_hectares,
                boundary_coordinates=updated_field.boundary_coordinates,
                soil_type=updated_field.soil_type,
                drainage_class=updated_field.drainage_class,
                elevation_meters=updated_field.elevation_meters,
                slope_percentage=updated_field.slope_percentage,
                created_at=updated_field.created_at,
                updated_at=updated_field.updated_at,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating field: {e}")
        raise HTTPException(status_code=500, detail="Failed to update field")


@router.delete(
    "/fields/{field_id}",
    response_model=StandardResponse,
    tags=["fields"],
    summary="Delete field",
    description="Remove a field from the system.",
)
async def delete_field(
    field_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> StandardResponse:
    """
    Delete field by ID.
    """
    try:
        async with UnitOfWork(session) as uow:
            field_repo = uow.field

            # Check if field exists
            field = await field_repo.get_field_by_id(field_id)
            if not field:
                raise HTTPException(status_code=404, detail=f"Field with ID {field_id} not found")

            # Delete field
            success = await field_repo.delete_field(field_id)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to delete field")

            return StandardResponse(success=True, message=f"Field {field_id} deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting field: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete field")
