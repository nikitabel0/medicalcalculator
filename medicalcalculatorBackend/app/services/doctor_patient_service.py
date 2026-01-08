from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models import DoctorPatient, User
from app.schemas import DoctorPatientCreate


class DoctorPatientService:
    @staticmethod
    async def add_patient_to_doctor(
        db: AsyncSession, 
        doctor_id: int, 
        patient_data: DoctorPatientCreate
    ) -> DoctorPatient:
        """Добавление пациента к медику"""
        # Проверяем, что врач существует и является медиком
        doctor_stmt = select(User).where(
            User.id == doctor_id,
            User.is_medical == True,
            User.is_active == True
        )
        doctor_result = await db.execute(doctor_stmt)
        doctor = doctor_result.scalar_one_or_none()
        
        if not doctor:
            raise ValueError("Медик не найден или неактивен")
        
        # Проверяем, что пациент существует и не является медиком
        patient_stmt = select(User).where(
            User.id == patient_data.patient_id,
            User.is_medical == False,
            User.is_active == True
        )
        patient_result = await db.execute(patient_stmt)
        patient = patient_result.scalar_one_or_none()
        
        if not patient:
            raise ValueError("Пациент не найден, неактивен или является медиком")
        
        # Проверяем, что связь еще не существует
        existing_stmt = select(DoctorPatient).where(
            and_(
                DoctorPatient.doctor_id == doctor_id,
                DoctorPatient.patient_id == patient_data.patient_id
            )
        )
        existing_result = await db.execute(existing_stmt)
        existing = existing_result.scalar_one_or_none()
        
        if existing:
            raise ValueError("Пациент уже привязан к этому медику")
        
        # Создаем связь
        db_relation = DoctorPatient(
            doctor_id=doctor_id,
            patient_id=patient_data.patient_id
        )
        
        db.add(db_relation)
        await db.commit()
        await db.refresh(db_relation)
        
        return db_relation
    
    @staticmethod
    async def get_doctor_patients(
        db: AsyncSession, 
        doctor_id: int
    ) -> List[User]:
        """Получение всех пациентов медика"""
        stmt = (
            select(User)
            .join(DoctorPatient, DoctorPatient.patient_id == User.id)
            .where(
                DoctorPatient.doctor_id == doctor_id,
                User.is_active == True
            )
            .order_by(User.full_name)
        )
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def get_patient_doctors(
        db: AsyncSession, 
        patient_id: int
    ) -> List[User]:
        """Получение всех медиков пациента"""
        stmt = (
            select(User)
            .join(DoctorPatient, DoctorPatient.doctor_id == User.id)
            .where(
                DoctorPatient.patient_id == patient_id,
                User.is_active == True,
                User.is_medical == True
            )
            .order_by(User.full_name)
        )
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def remove_patient_from_doctor(
        db: AsyncSession, 
        doctor_id: int, 
        patient_id: int
    ) -> bool:
        """Удаление пациента у медика"""
        stmt = select(DoctorPatient).where(
            and_(
                DoctorPatient.doctor_id == doctor_id,
                DoctorPatient.patient_id == patient_id
            )
        )
        result = await db.execute(stmt)
        relation = result.scalar_one_or_none()
        
        if not relation:
            return False
        
        await db.delete(relation)
        await db.commit()
        
        return True
    
    @staticmethod
    async def search_patients(
        db: AsyncSession,
        doctor_id: int,
        search_term: str = "",
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Поиск пациентов медика"""
        stmt = (
            select(User)
            .join(DoctorPatient, DoctorPatient.patient_id == User.id)
            .where(
                DoctorPatient.doctor_id == doctor_id,
                User.is_active == True
            )
        )
        
        if search_term:
            stmt = stmt.where(
                User.full_name.ilike(f"%{search_term}%") |
                User.email.ilike(f"%{search_term}%") |
                User.username.ilike(f"%{search_term}%")
            )
        
        stmt = stmt.order_by(User.full_name).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()