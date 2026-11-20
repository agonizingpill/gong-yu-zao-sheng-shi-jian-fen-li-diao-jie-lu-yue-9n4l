from datetime import datetime,timedelta
from sqlalchemy import select,func
from src.database import Base,engine,Session
from src.models import User,DemoClock,Complaint,NoiseEvent,TrialSample,Plan
from src.auth import password_hash

def seed():
    Base.metadata.create_all(engine)
    with Session() as db:
        for role in ('operator','supervisor','viewer'):
            if not db.scalar(select(User).where(User.username==role)):
                db.add(User(username=role,role=role,password_hash=password_hash('Quiet2026!')))
        if not db.get(DemoClock,1):db.add(DemoClock(id=1,at=datetime(2026,11,18,16,0)))
        items=[('QT031','访客青叶','3栋北侧','22:30设备低频持续，申请协调减振时段',True),('QT032','访客杉木','6栋东侧','午间装修冲击频带，尚未授权监测',False),('QT033','访客白榆','1栋走廊','晚间人声频带事件，希望双方协调安静时段',True)]
        for code,alias,building,summary,consent in items:
            if not db.scalar(select(Complaint).where(Complaint.code==code)):
                c=Complaint(code=code,alias=alias,building=building,summary=summary,consent=consent,consent_note='书面授权QTC-031' if consent else '待取得授权');db.add(c);db.flush()
                if consent:
                    for j in range(6):
                        energy=[8+j*.1,6,1.6,.5,.3,.2,.1,.05] if code=='QT031' else [.2,.3,.8,3,6+j*.1,7,4,1]
                        db.add(NoiseEvent(complaint_id=c.id,measured_at=datetime(2026,11,17,22,30)+timedelta(minutes=j*5),position='窗台测点A',duration_s=60,energies=energy,total=sum(energy),note='合成频带示例，无录音及真实住户信息'))
        # QT031隔振试装：同测点同静音时段的试装前后采样；床头测点B故意只备1条试装后采样，演示待补测与补测后重算。
        qt031=db.scalar(select(Complaint).where(Complaint.code=='QT031'))
        if qt031 and not db.scalar(select(TrialSample).where(TrialSample.complaint_id==qt031.id)):
            samples=[('pre',datetime(2026,11,17,22,30),'窗台测点A',[8.4,6,1.6,.5,.3,.2,.1,.05]),
                ('pre',datetime(2026,11,17,22,40),'窗台测点A',[8.1,5.8,1.5,.5,.3,.2,.1,.05]),
                ('pre',datetime(2026,11,17,22,30),'床头测点B',[10.2,7.5,2.2,.7,.4,.25,.12,.06]),
                ('pre',datetime(2026,11,17,22,40),'床头测点B',[9.8,7.2,2.1,.7,.4,.25,.12,.06]),
                ('post',datetime(2026,11,18,6,30),'窗台测点A',[2.9,2.1,.6,.2,.12,.08,.04,.02]),
                ('post',datetime(2026,11,18,6,40),'窗台测点A',[3.0,2.2,.6,.2,.12,.08,.04,.02]),
                ('post',datetime(2026,11,18,6,30),'床头测点B',[5.2,3.8,1.1,.35,.2,.12,.06,.03])]
            for phase,at,pos,energy in samples:
                db.add(TrialSample(complaint_id=qt031.id,phase=phase,measured_at=at,position=pos,duration_s=60,energies=energy,total=sum(energy),note='隔振试装对比采样，合成频带，无录音'))
        if qt031 and not db.scalar(select(Plan).where(Plan.complaint_id==qt031.id)):
            plans=[('标准减振垫组换装',6000,[.06,.06,.05,.05,.05,.05,.04,.04],'更换标准减振垫并紧固连接件'),('弹性支座加双层减振垫',15000,[.16,.16,.15,.15,.14,.14,.12,.12],'弹性支座配合双层减振垫，覆盖低频段'),('整机浮筑基础改造',30000,[.3,.3,.28,.28,.25,.25,.22,.22],'设备整机浮筑基础，工期较长')]
            for name,cost,reductions,note in plans:
                db.add(Plan(complaint_id=qt031.id,name=name,cost=cost,reductions=reductions,note=note))
        db.commit()
        counts={m.__tablename__:db.scalar(select(func.count()).select_from(m)) for m in (User,Complaint,NoiseEvent,TrialSample,Plan,DemoClock)}
        print(counts)
        return counts
if __name__=='__main__':seed()
