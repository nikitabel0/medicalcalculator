from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Text,UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(200))
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_medical = Column(Boolean, default=False)  # Флаг медика
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    doctor_patients = relationship("DoctorPatient", foreign_keys="DoctorPatient.doctor_id", back_populates="doctor")
    patient_doctors = relationship("DoctorPatient", foreign_keys="DoctorPatient.patient_id", back_populates="patient")
    patient_records = relationship("SDAIRecord", foreign_keys="SDAIRecord.patient_id", back_populates="patient")
    doctor_records = relationship("SDAIRecord", foreign_keys="SDAIRecord.doctor_id", back_populates="doctor")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"


class DoctorPatient(Base):
    """Связь между медиком и пациентом"""
    __tablename__ = "doctor_patients"
    
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Отношения
    doctor = relationship("User", foreign_keys=[doctor_id], back_populates="doctor_patients")
    patient = relationship("User", foreign_keys=[patient_id], back_populates="patient_doctors")
    
    # Уникальная связь
    __table_args__ = (UniqueConstraint('doctor_id', 'patient_id', name='unique_doctor_patient'),)


class SDAIRecord(Base):
    """Запись расчета SDAI"""
    __tablename__ = "sdai_records"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Поля анкеты
    tender_joint_count = Column(Integer, nullable=False)  # 0-28
    swollen_joint_count = Column(Integer, nullable=False)  # 0-28
    doctor_activity_assessment = Column(Float, nullable=False)  # 0-100
    patient_activity_assessment = Column(Float, nullable=False)  # 0-100
    crp = Column(Float, nullable=False)  # мг/дл
    
    # Расчетные поля
    sdai_score = Column(Float)  # Рассчитанный SDAI
    
    # Метаданные
    measurement_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    notes = Column(Text)  # Дополнительные заметки
    
    # Отношения
    patient = relationship("User", foreign_keys=[patient_id], back_populates="patient_records")
    doctor = relationship("User", foreign_keys=[doctor_id], back_populates="doctor_records")
    
    def calculate_sdai(self):
        """Рассчет SDAI по формуле"""
        return (
            self.tender_joint_count +
            self.swollen_joint_count +
            (self.doctor_activity_assessment / 10) +
            (self.patient_activity_assessment / 10) +
            (self.crp * 10)
        )