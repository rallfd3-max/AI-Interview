-- 姓名允许重复，因此这里只创建普通索引，不能创建唯一索引。
CREATE INDEX idx_candidate_real_name ON candidate (real_name);
