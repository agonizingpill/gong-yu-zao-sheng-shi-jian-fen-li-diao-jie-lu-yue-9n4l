# 002 隔振试装评估与方案选型

在001之上新增3张表，并为 `agreements` 增加3列。全新部署仍由create_all一次建成；已有库需执行下列显式迁移（MySQL8），不能依赖create_all改列。

```sql
CREATE TABLE trial_samples (
  id INT AUTO_INCREMENT PRIMARY KEY,
  complaint_id INT NOT NULL,
  phase VARCHAR(8) NOT NULL,
  measured_at DATETIME NOT NULL,
  position VARCHAR(60) NOT NULL,
  duration_s INT NOT NULL,
  energies JSON NOT NULL,
  total FLOAT NOT NULL,
  note VARCHAR(300) NOT NULL DEFAULT '试装对比采样，无原始录音',
  created_at DATETIME NOT NULL,
  CONSTRAINT sample_same_slot UNIQUE (complaint_id, phase, measured_at, position),
  CONSTRAINT sample_duration_positive CHECK (duration_s > 0),
  FOREIGN KEY (complaint_id) REFERENCES complaints(id)
);
CREATE TABLE plans (
  id INT AUTO_INCREMENT PRIMARY KEY,
  complaint_id INT NOT NULL,
  name VARCHAR(60) NOT NULL,
  cost FLOAT NOT NULL,
  reductions JSON NOT NULL,
  note VARCHAR(300) NOT NULL DEFAULT '',
  CONSTRAINT plan_name_unique UNIQUE (complaint_id, name),
  FOREIGN KEY (complaint_id) REFERENCES complaints(id)
);
CREATE TABLE estimates (
  id INT AUTO_INCREMENT PRIMARY KEY,
  complaint_id INT NOT NULL,
  created_at DATETIME NOT NULL,
  budget FLOAT NOT NULL,
  threshold FLOAT NOT NULL,
  quiet_from INT NOT NULL,
  quiet_to INT NOT NULL,
  status VARCHAR(12) NOT NULL,
  latest_sample_id INT NOT NULL DEFAULT 0,
  detail JSON NOT NULL,
  FOREIGN KEY (complaint_id) REFERENCES complaints(id)
);
ALTER TABLE agreements
  ADD COLUMN plan_id INT NULL,
  ADD COLUMN estimate_id INT NULL,
  ADD COLUMN basis JSON NULL,
  ADD CONSTRAINT fk_agreement_plan FOREIGN KEY (plan_id) REFERENCES plans(id),
  ADD CONSTRAINT fk_agreement_estimate FOREIGN KEY (estimate_id) REFERENCES estimates(id);
```

要点：

- `trial_samples` 与 `noise_events` 分离：试装对比采样不触发复发检查，按（卷，阶段，时刻，测点）去重。
- `estimates.latest_sample_id` 记录估算时最新采样id；起草协议时与当前最大值比对，不一致即"按新采样重算"。
- `agreements.basis` 保存签约时的方案、预算、阈值、各测点预测与采样规模快照；协议生效后按此履行，调解页据此展示。`estimates`/`plans` 行只增不改，历史可追。
- 协议状态新增 `superseded`（补测录入后原草案与签名失效）；在途协议判定排除 `superseded`。
