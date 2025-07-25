from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.core.database import get_session
from src.services.warehouse_service import WarehouseService
from src.api.schemas import MovementResponse, WarehouseStockResponse
from src.models.warehouse import WarehouseStock
from sqlalchemy.future import select
from sqlalchemy import and_

router = APIRouter(
    prefix="/api",
    tags=["Warehouse API"],
)


@router.get("/movements/{movement_id}", response_model=MovementResponse, summary="Получить детали перемещения")
async def get_movement_details(
    movement_id: UUID = Depends(lambda movement_id: movement_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Возвращает полную информацию о перемещении по его **movement_id**.

    Этот эндпоинт агрегирует данные из событий отправки (`departure`) и прибытия (`arrival`).
    - `source_warehouse`: Склад-отправитель.
    - `destination_warehouse`: Склад-получатель.
    - `time_in_transit`: Время, прошедшее между отправкой и приемкой.
    - `quantity_difference`: Разница между отправленным и полученным количеством.
      - Положительное значение: недостача.
      - Отрицательное значение: излишек.
      - 0: расхождений нет.

    Даже если одно из событий еще не произошло, эндпоинт вернет частичную информацию.
    """
    service = WarehouseService(session)
    movement_details = await service.get_movement_details(movement_id)

    if not movement_details:
        raise HTTPException(status_code=404, detail="Movement not found")

    return MovementResponse(**movement_details)


@router.get("/warehouses/{warehouse_id}/products/{product_id}", response_model=WarehouseStockResponse, summary="Получить остатки товара на складе")
async def get_warehouse_stock(
    warehouse_id: UUID,
    product_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Возвращает информацию о текущем запасе (остатке) конкретного товара
    на конкретном складе.
    """
    stmt = select(WarehouseStock).where(
        and_(
            WarehouseStock.warehouse_id == warehouse_id,
            WarehouseStock.product_id == product_id
        )
    )
    result = await session.execute(stmt)
    stock = result.scalars().first()

    if not stock:
        raise HTTPException(status_code=404, detail="Stock for this product in this warehouse not found")

    return stock
