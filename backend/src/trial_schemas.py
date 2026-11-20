from datetime import datetime
from pydantic import BaseModel,Field,field_validator,model_validator
from typing import Literal
import math
class TrialSampleInput(BaseModel):
    phase:Literal['pre','post']
    measured_at:datetime
    position:str=Field(min_length=2,max_length=60)
    duration_s:int=Field(ge=1,le=3600)
    energies:list[float]=Field(min_length=8,max_length=8)
    note:str=Field(default='试装对比采样，无原始录音',min_length=6,max_length=300)
    @field_validator('energies')
    @classmethod
    def finite(cls,v):
        if not all(math.isfinite(x) and 0<=x<=1000 for x in v) or sum(v)<=0:raise ValueError('8个频带须非负、有限且总能量大于0')
        return v
    @field_validator('measured_at')
    @classmethod
    def naive(cls,v):
        if v.tzinfo:raise ValueError('使用本地无时区时间')
        return v
class PlanInput(BaseModel):
    name:str=Field(min_length=2,max_length=60)
    cost:float=Field(ge=0,le=1000000,allow_inf_nan=False)
    reductions:list[float]=Field(min_length=8,max_length=8)
    note:str=Field(default='',max_length=300)
    @field_validator('name')
    @classmethod
    def stripped(cls,v):
        if not v.strip():raise ValueError('不可全为空格')
        return v.strip()
    @field_validator('reductions')
    @classmethod
    def ratios(cls,v):
        if not all(math.isfinite(x) and 0<=x<=0.95 for x in v):raise ValueError('各频带附加降幅须为0至0.95之间的有限数')
        return v
class EstimateInput(BaseModel):
    budget:float=Field(gt=0,le=10000000,allow_inf_nan=False)
    threshold:float=Field(gt=0,le=5000,allow_inf_nan=False)
    quiet_from:int=Field(ge=0,le=1439)
    quiet_to:int=Field(ge=0,le=1439)
    @model_validator(mode='after')
    def distinct(self):
        if self.quiet_from==self.quiet_to:raise ValueError('起止时刻不可相同')
        return self
