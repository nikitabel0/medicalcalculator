from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=200)

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=200)
    password: str = Field(..., min_length=6)
    is_medical: bool = Field(default=False)  # По умолчанию не медик
    
    @validator('password')
    def validate_password_length(cls, v):
        password_bytes = v.encode('utf-8')
        if len(password_bytes) > 72:
            v = v.encode('utf-8')[:72].decode('utf-8', 'ignore')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=200)
    password: Optional[str] = Field(None, min_length=6)
    is_medical: Optional[bool] = None

class UserInDB(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    is_medical: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserResponse(UserInDB):
    pass

# Схемы для SDAI записей
class SDAIRecordBase(BaseModel):
    patient_id: int
    tender_joint_count: int = Field(..., ge=0, le=28)
    swollen_joint_count: int = Field(..., ge=0, le=28)
    doctor_activity_assessment: float = Field(..., ge=0, le=100)
    patient_activity_assessment: float = Field(..., ge=0, le=100)
    crp: float = Field(..., ge=0)
    measurement_date: date
    notes: Optional[str] = None

class SDAIRecordCreate(SDAIRecordBase):
    pass

class SDAIRecordUpdate(BaseModel):
    tender_joint_count: Optional[int] = Field(None, ge=0, le=28)
    swollen_joint_count: Optional[int] = Field(None, ge=0, le=28)
    doctor_activity_assessment: Optional[float] = Field(None, ge=0, le=100)
    patient_activity_assessment: Optional[float] = Field(None, ge=0, le=100)
    crp: Optional[float] = Field(None, ge=0)
    measurement_date: Optional[date] = None
    notes: Optional[str] = None

class SDAIRecordInDB(SDAIRecordBase):
    id: int
    doctor_id: int
    sdai_score: float
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class SDAIRecordResponse(SDAIRecordInDB):
    pass

# Схемы для связей медик-пациент
class DoctorPatientBase(BaseModel):
    patient_id: int

class DoctorPatientCreate(DoctorPatientBase):
    pass

class DoctorPatientResponse(BaseModel):
    id: int
    doctor_id: int
    patient_id: int
    patient: UserResponse
    created_at: datetime
    
    class Config:
        from_attributes = True

class PatientWithRecords(BaseModel):
    patient: UserResponse
    records: List[SDAIRecordResponse]
    last_record: Optional[SDAIRecordResponse] = None

class SDAIRecordWithPatient(SDAIRecordResponse):
    patient: UserResponse
    doctor: UserResponse
    
    class Config:
        from_attributes = True

# Схемы для статистики
class SDAIStatistics(BaseModel):
    patient_count: int
    record_count: int
    avg_sdai_score: float
    min_sdai_score: float
    max_sdai_score: float
    latest_records: List[SDAIRecordResponse]

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None

class HealthCheck(BaseModel):
    status: str
    database: str
    timestamp: datetime