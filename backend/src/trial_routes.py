from fastapi import APIRouter,Depends
from sqlalchemy import select
from .database import session
from .auth import current,operator
from .models import TrialSample,Plan,Estimate
from .common import dump
from .trial_schemas import TrialSampleInput,PlanInput,EstimateInput
from . import trial_service as service
router=APIRouter()
@router.get('/complaints/{id}/trial-samples')
def samples(id:int,db=Depends(session),u=Depends(current)):return [dump(x) for x in db.scalars(select(TrialSample).where(TrialSample.complaint_id==id).order_by(TrialSample.measured_at,TrialSample.id))]
@router.post('/complaints/{id}/trial-samples')
def sample(id:int,data:TrialSampleInput,db=Depends(session),u=Depends(operator)):return service.create_sample(db,u,id,data)
@router.get('/complaints/{id}/plans')
def plans(id:int,db=Depends(session),u=Depends(current)):return [dump(x) for x in db.scalars(select(Plan).where(Plan.complaint_id==id).order_by(Plan.id))]
@router.post('/complaints/{id}/plans')
def plan(id:int,data:PlanInput,db=Depends(session),u=Depends(operator)):return service.create_plan(db,u,id,data)
@router.get('/complaints/{id}/estimates')
def estimates(id:int,db=Depends(session),u=Depends(current)):return [dump(x) for x in db.scalars(select(Estimate).where(Estimate.complaint_id==id).order_by(Estimate.id.desc()))]
@router.post('/complaints/{id}/estimates')
def estimate(id:int,data:EstimateInput,db=Depends(session),u=Depends(operator)):return service.compute_estimate(db,u,id,data)
