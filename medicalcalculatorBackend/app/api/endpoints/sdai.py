from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import (
    SDAIRecordCreate, 
    SDAIRecordResponse, 
    SDAIRecordUpdate,
    SDAIRecordWithPatient,
    PatientWithRecords,
    SDAIStatistics,
    DoctorPatientCreate,
    DoctorPatientResponse
)
from app.services.sdai_service import SDAIService
from app.services.doctor_patient_service import DoctorPatientService
from app.api.dependencies import get_current_user, get_current_medical_user

router = APIRouter(prefix="/api/sdai", tags=["sdai"])


@router.post("/records", response_model=SDAIRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_sdai_record(
    record_data: SDAIRecordCreate,
    current_user = Depends(get_current_medical_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание новой записи SDAI (только для медиков)"""
    try:
        record = await SDAIService.create_record(
            db=db,
            record_data=record_data,
            doctor_id=current_user.id
        )
        return record
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/records", response_model=List[SDAIRecordWithPatient])
async def get_sdai_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение записей SDAI"""
    if current_user.is_medical:
        # Медик видит все записи, которые он создал
        records = await SDAIService.get_doctor_records(
            db=db,
            doctor_id=current_user.id,
            skip=skip,
            limit=limit
        )
    else:
        # Пациент видит только свои записи
        records = await SDAIService.get_patient_records(
            db=db,
            patient_id=current_user.id,
            skip=skip,
            limit=limit
        )
    
    return records


@router.get("/records/{record_id}", response_model=SDAIRecordWithPatient)
async def get_sdai_record(
    record_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение конкретной записи SDAI"""
    record = await SDAIService.get_record(db, record_id)
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запись не найдена"
        )
    
    # Проверяем права доступа
    if not current_user.is_superuser:
        if current_user.is_medical:
            if record.doctor_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Нет доступа к этой записи"
                )
        else:
            if record.patient_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Нет доступа к этой записи"
                )
    
    return record


@router.put("/records/{record_id}", response_model=SDAIRecordResponse)
async def update_sdai_record(
    record_id: int,
    record_data: SDAIRecordUpdate,
    current_user = Depends(get_current_medical_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновление записи SDAI (только для медиков)"""
    # Проверяем, что запись существует и принадлежит этому медику
    record = await SDAIService.get_record(db, record_id)
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запись не найдена"
        )
    
    if record.doctor_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав для обновления этой записи"
        )
    
    updated_record = await SDAIService.update_record(
        db=db,
        record_id=record_id,
        record_data=record_data
    )
    
    if not updated_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запись не найдена"
        )
    
    return updated_record


@router.delete("/records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sdai_record(
    record_id: int,
    current_user = Depends(get_current_medical_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаление записи SDAI (только для медиков)"""
    # Проверяем, что запись существует и принадлежит этому медику
    record = await SDAIService.get_record(db, record_id)
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запись не найдена"
        )
    
    if record.doctor_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав для удаления этой записи"
        )
    
    success = await SDAIService.delete_record(db, record_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запись не найдена"
        )


@router.get("/patients", response_model=List[PatientWithRecords])
async def get_doctor_patients_with_records(
    current_user = Depends(get_current_medical_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение пациентов медика с их последними записями"""
    patients = await DoctorPatientService.get_doctor_patients(db, current_user.id)
    
    result = []
    for patient in patients:
        # Получаем записи пациента
        records = await SDAIService.get_patient_records(
            db=db,
            patient_id=patient.id,
            limit=10
        )
        
        # Получаем последнюю запись
        latest_record = records[0] if records else None
        
        result.append({
            "patient": patient,
            "records": records,
            "last_record": latest_record
        })
    
    return result


@router.get("/statistics", response_model=SDAIStatistics)
async def get_sdai_statistics(
    patient_id: Optional[int] = None,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение статистики SDAI"""
    if patient_id:
        # Проверяем права доступа к статистике пациента
        if current_user.is_medical:
            # Медик может смотреть статистику своих пациентов
            patients = await DoctorPatientService.get_doctor_patients(db, current_user.id)
            patient_ids = [p.id for p in patients]
            
            if patient_id not in patient_ids and not current_user.is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Нет доступа к статистике этого пациента"
                )
        else:
            # Пациент может смотреть только свою статистику
            if patient_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Нет доступа к статистике этого пациента"
                )
        
        target_patient_id = patient_id
    else:
        # Если patient_id не указан, используем ID текущего пользователя
        if current_user.is_medical:
            # Для медиков без указания пациента - общая статистика по всем пациентам
            patients = await DoctorPatientService.get_doctor_patients(db, current_user.id)
            patient_ids = [p.id for p in patients]
            
            if not patient_ids:
                return {
                    "patient_count": 0,
                    "record_count": 0,
                    "avg_sdai_score": 0,
                    "min_sdai_score": 0,
                    "max_sdai_score": 0,
                    "latest_records": []
                }
            
            # Получаем записи всех пациентов
            all_records = []
            for pid in patient_ids:
                records = await SDAIService.get_patient_records(db, pid, limit=100)
                all_records.extend(records)
            
            if not all_records:
                return {
                    "patient_count": len(patient_ids),
                    "record_count": 0,
                    "avg_sdai_score": 0,
                    "min_sdai_score": 0,
                    "max_sdai_score": 0,
                    "latest_records": []
                }
            
            # Рассчитываем статистику
            sdai_scores = [r.sdai_score for r in all_records]
            
            # Последние 10 записей
            latest_records = sorted(
                all_records, 
                key=lambda x: x.measurement_date, 
                reverse=True
            )[:10]
            
            return {
                "patient_count": len(patient_ids),
                "record_count": len(all_records),
                "avg_sdai_score": sum(sdai_scores) / len(sdai_scores),
                "min_sdai_score": min(sdai_scores),
                "max_sdai_score": max(sdai_scores),
                "latest_records": latest_records
            }
        else:
            # Для пациентов - статистика по себе
            target_patient_id = current_user.id
    
    # Статистика по конкретному пациенту
    stats = await SDAIService.get_patient_statistics(db, target_patient_id)
    
    # Получаем последние записи
    latest_records = await SDAIService.get_patient_records(
        db=db,
        patient_id=target_patient_id,
        limit=10
    )
    
    return {
        "patient_count": 1,
        "record_count": stats["record_count"],
        "avg_sdai_score": stats["avg_sdai_score"],
        "min_sdai_score": stats["min_sdai_score"],
        "max_sdai_score": stats["max_sdai_score"],
        "latest_records": latest_records
    }


@router.post("/patients", response_model=DoctorPatientResponse, status_code=status.HTTP_201_CREATED)
async def add_patient(
    patient_data: DoctorPatientCreate,
    current_user = Depends(get_current_medical_user),
    db: AsyncSession = Depends(get_db)
):
    """Добавление пациента к медику"""
    try:
        relation = await DoctorPatientService.add_patient_to_doctor(
            db=db,
            doctor_id=current_user.id,
            patient_data=patient_data
        )
        return relation
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/search")
async def search_sdai_records(
    patient_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    min_sdai: Optional[float] = Query(None, ge=0),
    max_sdai: Optional[float] = Query(None, ge=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user = Depends(get_current_medical_user),
    db: AsyncSession = Depends(get_db)
):
    """Поиск записей SDAI с фильтрами"""
    records = await SDAIService.search_records(
        db=db,
        doctor_id=current_user.id,
        patient_id=patient_id,
        start_date=start_date,
        end_date=end_date,
        min_sdai=min_sdai,
        max_sdai=max_sdai,
        skip=skip,
        limit=limit
    )
    
    return records


@router.get("/export")
async def export_sdai_data(
    format: str = Query("csv", regex="^(csv|json)$"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user = Depends(get_current_medical_user),
    db: AsyncSession = Depends(get_db)
):
    """Экспорт данных SDAI"""
    records = await SDAIService.search_records(
        db=db,
        doctor_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        limit=10000  # Ограничение на экспорт
    )
    
    if format == "csv":
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        writer.writerow([
            "ID", "Дата измерения", "ID пациента", "Пациент",
            "Болезненные суставы", "Припухшие суставы",
            "Оценка врача", "Оценка пациента", "СРБ", "SDAI"
        ])
        
        # Данные
        for record in records:
            writer.writerow([
                record.id,
                record.measurement_date.strftime("%Y-%m-%d"),
                record.patient_id,
                record.patient.full_name or record.patient.username,
                record.tender_joint_count,
                record.swollen_joint_count,
                record.doctor_activity_assessment,
                record.patient_activity_assessment,
                record.crp,
                record.sdai_score
            ])
        
        content = output.getvalue()
        output.close()
        
        return {
            "content": content,
            "filename": f"sdai_export_{date.today()}.csv",
            "content_type": "text/csv"
        }
    
    elif format == "json":
        # JSON экспорт
        data = []
        for record in records:
            data.append({
                "id": record.id,
                "measurement_date": record.measurement_date.strftime("%Y-%m-%d"),
                "patient_id": record.patient_id,
                "patient_name": record.patient.full_name or record.patient.username,
                "tender_joint_count": record.tender_joint_count,
                "swollen_joint_count": record.swollen_joint_count,
                "doctor_activity_assessment": record.doctor_activity_assessment,
                "patient_activity_assessment": record.patient_activity_assessment,
                "crp": record.crp,
                "sdai_score": record.sdai_score
            })
        
        return {
            "data": data,
            "count": len(data),
            "export_date": date.today().isoformat()
        }