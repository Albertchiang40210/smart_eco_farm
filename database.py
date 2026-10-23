from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

from settings import DATABASE_URL

_engine_kwargs = {"pool_recycle": 3600, "pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs.update(pool_size=10, max_overflow=20)

engine = create_engine(DATABASE_URL, **_engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class SensorLog(Base):
    __tablename__ = "sensor_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(50), index=True)
    temperature = Column(Float)
    humidity = Column(Float)
    soil_moisture = Column(Float)
    lux = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class FarmTask(Base):
    __tablename__ = "farm_tasks_v2"
    
    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String(255))
    status = Column(String(50))
    diagnosis_result = Column(String(100))
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemAuditLog(Base):
    __tablename__ = "system_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user = Column(String(50))
    action = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

class EnvironmentRule(Base):
    __tablename__ = "environment_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(50), unique=True)
    sensor_type = Column(String(50))  # e.g., 'temperature', 'humidity'
    condition_operator = Column(String(10)) # e.g., '>', '<'
    threshold_value = Column(Float)
    action_target = Column(String(50)) # e.g., 'fan', 'pump'
    action_command = Column(String(10)) # 'ON', 'OFF'
    created_at = Column(DateTime, default=datetime.utcnow)

# Initialize database tables
def init_db():
    Base.metadata.create_all(bind=engine)
    
    # 寫入預設規則
    with SessionLocal() as db:
        if db.query(EnvironmentRule).count() == 0:
            default_rules = [
                EnvironmentRule(rule_name="High Temp Fan On", sensor_type="temperature", condition_operator=">", threshold_value=28.0, action_target="fan", action_command="ON"),
                EnvironmentRule(rule_name="Low Humidity Pump On", sensor_type="humidity", condition_operator="<", threshold_value=65.0, action_target="pump", action_command="ON")
            ]
            db.add_all(default_rules)
            db.commit()
