from sqlalchemy import select
from .models import TrialSample,Plan,Estimate,Agreement
from .common import require,lock_case,record,now,dump
from .trial_math import evaluate

def create_sample(db,user,caseid,data):
    case=lock_case(db,caseid)
    require(case.consent,'监测授权已撤回或尚未取得，不能登记试装采样')
    require(case.status!='closed','已结案，请主管先重开')
    require(data.measured_at<=now(db),'采样时间不可晚于演示时钟')
    require(not db.scalar(select(TrialSample).where(TrialSample.complaint_id==caseid,TrialSample.phase==data.phase,TrialSample.measured_at==data.measured_at,TrialSample.position==data.position)),'同测点同一时刻同阶段已登记采样，禁止重复计数')
    row=TrialSample(complaint_id=caseid,**data.model_dump(),total=sum(data.energies));db.add(row);db.flush()
    # 补测录入后，本卷未生效草案与双方签名即刻失效，须按新采样重算；已生效协议不受影响。
    for a in db.scalars(select(Agreement).where(Agreement.complaint_id==caseid,Agreement.state=='draft')).all():
        a.state='superseded';record(db,user,'agreement.supersede',a.id,f'补测采样#{row.id}录入，原草案与签名失效')
    record(db,user,'trial.sample',row.id,f'{data.phase}@{data.position}');db.commit();return dump(row)
def create_plan(db,user,caseid,data):
    case=lock_case(db,caseid);require(case.status!='closed','已结案卷宗不能新增方案')
    require(not db.scalar(select(Plan).where(Plan.complaint_id==caseid,Plan.name==data.name)),'同名方案已存在')
    row=Plan(complaint_id=caseid,**data.model_dump());db.add(row);db.flush();record(db,user,'plan.create',row.id,data.name);db.commit();return dump(row)
def compute_estimate(db,user,caseid,data):
    case=lock_case(db,caseid)
    require(case.consent,'撤回监测授权后不能新增估算处理')
    require(case.status!='closed','已结案卷宗不能重新估算')
    samples=db.scalars(select(TrialSample).where(TrialSample.complaint_id==caseid).order_by(TrialSample.id)).all()
    plans=db.scalars(select(Plan).where(Plan.complaint_id==caseid).order_by(Plan.id)).all()
    scoped=[{'position':s.position,'phase':s.phase,'minute':s.measured_at.hour*60+s.measured_at.minute,'energies':s.energies} for s in samples]
    result=evaluate(scoped,[{'id':p.id,'name':p.name,'cost':p.cost,'reductions':p.reductions} for p in plans],data.budget,data.threshold,data.quiet_from,data.quiet_to)
    detail={**result['detail'],'budget':data.budget,'threshold':data.threshold}
    row=Estimate(complaint_id=caseid,budget=data.budget,threshold=data.threshold,quiet_from=data.quiet_from,quiet_to=data.quiet_to,status=result['status'],latest_sample_id=samples[-1].id if samples else 0,detail=detail)
    db.add(row);db.flush();record(db,user,'estimate.compute',row.id,result['status']);db.commit();return dump(row)
