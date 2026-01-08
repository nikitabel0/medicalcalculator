from datetime import datetime, date
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.models import SDAIRecord, User, DoctorPatient
from app.schemas import SDAIRecordCreate, SDAIRecordUpdate


class SDAIService:
    @staticmethod
    async def create_record(
        db: AsyncSession, 
        record_data: SDAIRecordCreate, 
        doctor_id: int
    ) -> SDAIRecord:
        """Создание новой записи SDAI"""
        # Проверяем, что пациент существует
        patient_stmt = select(User).where(
            User.id == record_data.patient_id,
            User.is_active == True
        )
        patient_result = await db.execute(patient_stmt)
        patient = patient_result.scalar_one_or_none()
        
        if not patient:
            raise ValueError("Пациент не найден или неактивен")
        
        # Проверяем, что пациент не медик
        if patient.is_medical:
            raise ValueError("Медик не может быть пациентом")
        
        # Проверяем связь медик-пациент (если нужно)
        # Можно добавить проверку, что медик имеет доступ к этому пациенту
        
        # Создаем запись
        db_record = SDAIRecord(
            **record_data.dict(),
            doctor_id=doctor_id,
            measurement_date=record_data.measurement_date
        )
        
        # Рассчитываем SDAI
        db_record.sdai_score = db_record.calculate_sdai()
        
        db.add(db_record)
        await db.commit()
        await db.refresh(db_record)
        
        return db_record
    
    @staticmethod
    async def get_record(db: AsyncSession, record_id: int) -> Optional[SDAIRecord]:
        """Получение записи по ID"""
        stmt = select(SDAIRecord).where(SDAIRecord.id == record_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_record(
        db: AsyncSession, 
        record_id: int, 
        record_data: SDAIRecordUpdate
    ) -> Optional[SDAIRecord]:
        """Обновление записи SDAI"""
        stmt = select(SDAIRecord).where(SDAIRecord.id == record_id)
        result = await db.execute(stmt)
        record = result.scalar_one_or_none()
        
        if not record:
            return None
        
        # Обновляем поля
        update_data = record_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(record, field, value)
        
        # Пересчитываем SDAI если изменились данные
        record.sdai_score = record.calculate_sdai()
        
        record.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(record)
        
        return record
    
    @staticmethod
    async def delete_record(db: AsyncSession, record_id: int) -> bool:
        """Удаление записи SDAI"""
        stmt = select(SDAIRecord).where(SDAIRecord.id == record_id)
        result = await db.execute(stmt)
        record = result.scalar_one_or_none()
        
        if not record:
            return False
        
        await db.delete(record)
        await db.commit()
        
        return True
    
    @staticmethod
    async def get_patient_records(
        db: AsyncSession, 
        patient_id: int,
        skip: int = 0, 
        limit: int = 100
    ) -> List[SDAIRecord]:
        """Получение записей пациента"""
        stmt = (
            select(SDAIRecord)
            .where(SDAIRecord.patient_id == patient_id)
            .order_by(desc(SDAIRecord.measurement_date))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def get_doctor_records(
        db: AsyncSession, 
        doctor_id: int,
        skip: int = 0, 
        limit: int = 100
    ) -> List[SDAIRecord]:
        """Получение записей, созданных медиком"""
        stmt = (
            select(SDAIRecord)
            .where(SDAIRecord.doctor_id == doctor_id)
            .order_by(desc(SDAIRecord.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def get_patient_statistics(
        db: AsyncSession, 
        patient_id: int
    ) -> Dict[str, Any]:
        """Статистика по пациенту"""
        # Общее количество записей
        count_stmt = select(func.count()).where(SDAIRecord.patient_id == patient_id)
        count_result = await db.execute(count_stmt)
        record_count = count_result.scalar()
        
        if record_count == 0:
            return {
                "record_count": 0,
                "avg_sdai_score": 0,
                "min_sdai_score": 0,
                "max_sdai_score": 0,
                "latest_record": None
            }
        
        # Средний, минимальный и максимальный SDAI
        stats_stmt = select(
            func.avg(SDAIRecord.sdai_score).label("avg"),
            func.min(SDAIRecord.sdai_score).label("min"),
            func.max(SDAIRecord.sdai_score).label("max")
        ).where(SDAIRecord.patient_id == patient_id)
        
        stats_result = await db.execute(stats_stmt)
        stats = stats_result.first()
        
        # Последняя запись
        latest_stmt = (
            select(SDAIRecord)
            .where(SDAIRecord.patient_id == patient_id)
            .order_by(desc(SDAIRecord.measurement_date))
            .limit(1)
        )
        latest_result = await db.execute(latest_stmt)
        latest_record = latest_result.scalar_one_or_none()
        
        return {
            "record_count": record_count,
            "avg_sdai_score": float(stats.avg) if stats.avg else 0,
            "min_sdai_score": float(stats.min) if stats.min else 0,
            "max_sdai_score": float(stats.max) if stats.max else 0,
            "latest_record": latest_record
        }
    
    @staticmethod
    async def search_records(
        db: AsyncSession,
        doctor_id: Optional[int] = None,
        patient_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        min_sdai: Optional[float] = None,
        max_sdai: Optional[float] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[SDAIRecord]:
        """Поиск записей с фильтрами"""
        stmt = select(SDAIRecord)
        
        if doctor_id:
            stmt = stmt.where(SDAIRecord.doctor_id == doctor_id)
        
        if patient_id:
            stmt = stmt.where(SDAIRecord.patient_id == patient_id)
        
        if start_date:
            stmt = stmt.where(SDAIRecord.measurement_date >= start_date)
        
        if end_date:
            stmt = stmt.where(SDAIRecord.measurement_date <= end_date)
        
        if min_sdai is not None:
            stmt = stmt.where(SDAIRecord.sdai_score >= min_sdai)
        
        if max_sdai is not None:
            stmt = stmt.where(SDAIRecord.sdai_score <= max_sdai)
        
        stmt = stmt.order_by(desc(SDAIRecord.measurement_date))
        stmt = stmt.offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()