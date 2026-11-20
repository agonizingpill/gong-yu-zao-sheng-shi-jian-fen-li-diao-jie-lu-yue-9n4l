"""隔振试装评估的纯计算部分：不依赖数据库与框架，可独立测试。

口径约定：
- 只取静音时段内的试装采样，按测点分组比较试装前/后，即"同测点同一时段"。
- 每个测点试装前、试装后各至少 MIN_SAMPLES 条，否则证据不足，等待补测。
- 基线取试装前各频带均值；残余取试装后各频带最不利（最大）一次采样，即保守口径。
- 方案申报的各频带附加降幅作用于保守残余，预测各测点总量；
  预算内且所有测点预测都不超阈值的方案中，推荐费用最低者。
"""
from .constants import BANDS

MIN_SAMPLES=2
EPS=1e-9

def in_window(minute,a,b):
    return a<=minute<b if a<b else minute>=a or minute<b

def evaluate(samples,plans,budget,threshold,quiet_from,quiet_to):
    """samples:[{position,phase,minute,energies}] plans:[{id,name,cost,reductions}]"""
    scoped=[s for s in samples if in_window(s['minute'],quiet_from,quiet_to)]
    grouped={}
    for s in scoped:
        grouped.setdefault(s['position'],{'pre':[],'post':[]})[s['phase']].append(s['energies'])
    positions={};reasons=[];ready=True
    for pos in sorted(grouped):
        pre=grouped[pos]['pre'];post=grouped[pos]['post']
        gaps=[]
        if len(pre)<MIN_SAMPLES:gaps.append(f'试装前采样{len(pre)}/{MIN_SAMPLES}条')
        if len(post)<MIN_SAMPLES:gaps.append(f'试装后采样{len(post)}/{MIN_SAMPLES}条')
        baseline=[0.0]*8;residual=[0.0]*8;reduction=[None]*8
        if not gaps:
            baseline=[sum(e[i] for e in pre)/len(pre) for i in range(8)]
            residual=[max(e[i] for e in post) for i in range(8)]
            for i in range(8):
                if baseline[i]<=EPS:
                    if residual[i]>EPS:gaps.append(f'{BANDS[i]}试装前为零而试装后出现能量，需补测核实')
                    else:residual[i]=0.0
                else:reduction[i]=round(1-residual[i]/baseline[i],4)
        if gaps:ready=False;reasons.append(f'{pos}：'+'；'.join(gaps))
        positions[pos]={'pre_count':len(pre),'post_count':len(post),'baseline':baseline,'residual':residual,'reduction':reduction,'gaps':gaps}
    if not positions:
        ready=False;reasons.append('静音时段内尚无试装采样，请先登记试装前后采样')
    plan_evals=[];recommended=None
    if ready:
        for p in plans:
            predicted={}
            for pos,info in positions.items():
                predicted[pos]=round(sum(info['residual'][i]*(1-p['reductions'][i]) for i in range(8)),4)
            plan_evals.append({'plan_id':p['id'],'name':p['name'],'cost':p['cost'],
                'within_budget':p['cost']<=budget+EPS,
                'compliant':all(v<=threshold+EPS for v in predicted.values()),
                'predicted':predicted})
        ok=[e for e in plan_evals if e['within_budget'] and e['compliant']]
        if ok:recommended=min(ok,key=lambda e:(e['cost'],e['plan_id']))['plan_id']
    return {'status':'ready' if ready else 'insufficient',
            'detail':{'positions':positions,'plans':plan_evals,'recommended_plan_id':recommended,'reasons':reasons,'sample_count':len(scoped)}}
