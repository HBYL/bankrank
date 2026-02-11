-- 银行对公信用评估业务系统数据库初始化脚本
-- 数据库: py_bccabusinesssystem
-- 用户名: root
-- 密码: root

CREATE DATABASE IF NOT EXISTS py_bccabusinesssystem DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE py_bccabusinesssystem;

-- 用户表
DROP TABLE IF EXISTS user;
CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    username VARCHAR(50) COMMENT '用户名',
    password VARCHAR(255) COMMENT '密码',
    name VARCHAR(100) COMMENT '姓名/企业名称',
    role VARCHAR(20) COMMENT '角色: enterprise/employee/admin',
    phone VARCHAR(20) COMMENT '联系电话',
    email VARCHAR(100) COMMENT '邮箱',
    status INT DEFAULT 1 COMMENT '状态: 1启用 0禁用',
    create_time DATETIME COMMENT '创建时间',
    update_time DATETIME COMMENT '更新时间'
) COMMENT='用户表';

-- 企业信息表
DROP TABLE IF EXISTS enterprise;
CREATE TABLE enterprise (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '企业ID',
    user_id INT COMMENT '关联用户ID',
    company_name VARCHAR(200) COMMENT '企业名称',
    credit_code VARCHAR(18) COMMENT '统一社会信用代码',
    legal_person VARCHAR(50) COMMENT '法定代表人',
    registered_capital DECIMAL(15,2) COMMENT '注册资本(万元)',
    industry VARCHAR(50) COMMENT '所属行业',
    address VARCHAR(500) COMMENT '企业地址',
    business_license VARCHAR(255) COMMENT '营业执照图片路径',
    license_status INT DEFAULT 0 COMMENT '执照审核状态: 0待审核 1通过 2拒绝',
    review_comment VARCHAR(500) COMMENT '审核意见',
    create_time DATETIME COMMENT '创建时间',
    update_time DATETIME COMMENT '更新时间'
) COMMENT='企业信息表';

-- 虚拟账户表
DROP TABLE IF EXISTS account;
CREATE TABLE account (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '账户ID',
    enterprise_id INT COMMENT '企业ID',
    account_no VARCHAR(20) COMMENT '账户号',
    balance DECIMAL(15,2) DEFAULT 0 COMMENT '账户余额',
    create_time DATETIME COMMENT '创建时间',
    update_time DATETIME COMMENT '更新时间'
) COMMENT='虚拟对公账户表';

-- 交易流水表
DROP TABLE IF EXISTS transaction;
CREATE TABLE transaction (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '交易ID',
    account_id INT COMMENT '账户ID',
    enterprise_id INT COMMENT '企业ID',
    trans_type VARCHAR(20) COMMENT '交易类型: deposit存入/withdraw支取',
    amount DECIMAL(15,2) COMMENT '交易金额',
    balance_after DECIMAL(15,2) COMMENT '交易后余额',
    remark VARCHAR(500) COMMENT '备注',
    create_time DATETIME COMMENT '交易时间'
) COMMENT='交易流水表';

-- 贷款表
DROP TABLE IF EXISTS loan;
CREATE TABLE loan (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '贷款ID',
    enterprise_id INT COMMENT '企业ID',
    loan_no VARCHAR(30) COMMENT '贷款编号',
    loan_amount DECIMAL(15,2) COMMENT '贷款金额',
    interest_rate DECIMAL(5,2) COMMENT '年利率(%)',
    loan_term INT COMMENT '贷款期限(月)',
    remaining_amount DECIMAL(15,2) COMMENT '剩余本金',
    status VARCHAR(20) COMMENT '状态: pending待审批/approved已批准/rejected已拒绝/repaying还款中/completed已结清',
    apply_time DATETIME COMMENT '申请时间',
    approve_time DATETIME COMMENT '审批时间',
    create_time DATETIME COMMENT '创建时间'
) COMMENT='贷款表';

-- 还款记录表
DROP TABLE IF EXISTS repayment;
CREATE TABLE repayment (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '还款ID',
    loan_id INT COMMENT '贷款ID',
    enterprise_id INT COMMENT '企业ID',
    repay_amount DECIMAL(15,2) COMMENT '还款金额',
    principal DECIMAL(15,2) COMMENT '本金部分',
    interest DECIMAL(15,2) COMMENT '利息部分',
    repay_date DATE COMMENT '还款日期',
    status VARCHAR(20) COMMENT '状态: pending待还款/paid已还款/overdue逾期',
    actual_repay_time DATETIME COMMENT '实际还款时间',
    create_time DATETIME COMMENT '创建时间'
) COMMENT='还款记录表';

-- 信用评估表
DROP TABLE IF EXISTS credit_assessment;
CREATE TABLE credit_assessment (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '评估ID',
    enterprise_id INT COMMENT '企业ID',
    score INT COMMENT '信用评分(0-100)',
    grade VARCHAR(1) COMMENT '信用等级: A/B/C/D',
    industry_score INT COMMENT '行业评分',
    debt_score INT COMMENT '负债评分',
    cashflow_score INT COMMENT '现金流评分',
    litigation_score INT COMMENT '诉讼评分',
    questionnaire_data TEXT COMMENT '问卷数据JSON',
    assess_time DATETIME COMMENT '评估时间',
    create_time DATETIME COMMENT '创建时间'
) COMMENT='信用评估表';

-- 征信记录表
DROP TABLE IF EXISTS credit_history;
CREATE TABLE credit_history (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    enterprise_id INT COMMENT '企业ID',
    record_type VARCHAR(50) COMMENT '记录类型: inquiry查询/negative负面/positive正面',
    record_source VARCHAR(100) COMMENT '记录来源',
    record_content TEXT COMMENT '记录内容',
    record_date DATE COMMENT '记录日期',
    create_time DATETIME COMMENT '创建时间'
) COMMENT='征信记录表';

-- 外链管理表
DROP TABLE IF EXISTS external_link;
CREATE TABLE external_link (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '链接ID',
    link_name VARCHAR(100) COMMENT '链接名称',
    link_url VARCHAR(500) COMMENT '链接地址',
    link_type VARCHAR(50) COMMENT '链接类型',
    status INT DEFAULT 1 COMMENT '状态: 1启用 0禁用',
    create_time DATETIME COMMENT '创建时间',
    update_time DATETIME COMMENT '更新时间'
) COMMENT='外链管理表';

-- 内容审核表
DROP TABLE IF EXISTS content_review;
CREATE TABLE content_review (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '审核ID',
    enterprise_id INT COMMENT '企业ID',
    content_type VARCHAR(50) COMMENT '内容类型: license营业执照/screenshot截图',
    content_path VARCHAR(255) COMMENT '内容文件路径',
    status INT DEFAULT 0 COMMENT '审核状态: 0待审核 1通过 2拒绝',
    review_comment VARCHAR(500) COMMENT '审核意见',
    reviewer_id INT COMMENT '审核人ID',
    review_time DATETIME COMMENT '审核时间',
    create_time DATETIME COMMENT '创建时间'
) COMMENT='内容审核表';

-- AI咨询记录表
DROP TABLE IF EXISTS ai_consultation;
CREATE TABLE ai_consultation (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '咨询ID',
    enterprise_id INT COMMENT '企业ID',
    question TEXT COMMENT '问题内容',
    answer TEXT COMMENT '回答内容',
    create_time DATETIME COMMENT '咨询时间'
) COMMENT='AI咨询记录表';

-- 插入初始数据

-- 管理员账户
INSERT INTO user (username, password, name, role, phone, email, status, create_time, update_time) VALUES
('admin', 'admin123', '系统管理员', 'admin', '13800000000', 'admin@bank.com', 1, NOW(), NOW()),
('employee1', '123456', '张三', 'employee', '13800000001', 'zhangsan@bank.com', 1, NOW(), NOW()),
('employee2', '123456', '李四', 'employee', '13800000002', 'lisi@bank.com', 1, NOW(), NOW()),
('enterprise1', '123456', '测试企业A', 'enterprise', '13800000003', 'companya@test.com', 1, NOW(), NOW()),
('enterprise2', '123456', '测试企业B', 'enterprise', '13800000004', 'companyb@test.com', 1, NOW(), NOW());

-- 企业信息
INSERT INTO enterprise (user_id, company_name, credit_code, legal_person, registered_capital, industry, address, license_status, create_time, update_time) VALUES
(4, '测试企业A有限公司', '91110000MA00AAAA00', '王五', 1000.00, 'technology', '北京市朝阳区xxx路xxx号', 1, NOW(), NOW()),
(5, '测试企业B有限公司', '91110000MA00BBBB00', '赵六', 500.00, 'manufacturing', '上海市浦东新区xxx路xxx号', 1, NOW(), NOW());

-- 虚拟账户
INSERT INTO account (enterprise_id, account_no, balance, create_time, update_time) VALUES
(1, '6222000000000001', 100000.00, NOW(), NOW()),
(2, '6222000000000002', 50000.00, NOW(), NOW());

-- 交易流水
INSERT INTO transaction (account_id, enterprise_id, trans_type, amount, balance_after, remark, create_time) VALUES
(1, 1, 'deposit', 100000.00, 100000.00, '初始存款', NOW()),
(2, 2, 'deposit', 50000.00, 50000.00, '初始存款', NOW());

-- 贷款记录
INSERT INTO loan (enterprise_id, loan_no, loan_amount, interest_rate, loan_term, remaining_amount, status, apply_time, create_time) VALUES
(1, 'LN202401001', 500000.00, 4.35, 12, 500000.00, 'repaying', NOW(), NOW()),
(2, 'LN202401002', 200000.00, 4.35, 6, 200000.00, 'pending', NOW(), NOW());

-- 信用评估记录
INSERT INTO credit_assessment (enterprise_id, score, grade, industry_score, debt_score, cashflow_score, litigation_score, assess_time, create_time) VALUES
(1, 85, 'A', 23, 22, 20, 20, NOW(), NOW()),
(2, 65, 'B', 20, 15, 18, 12, NOW(), NOW());

-- 征信记录
INSERT INTO credit_history (enterprise_id, record_type, record_source, record_content, record_date, create_time) VALUES
(1, 'inquiry', '银行查询', '贷款审批查询', CURDATE(), NOW()),
(1, 'positive', '纳税记录', '连续3年纳税信用A级', CURDATE(), NOW()),
(2, 'inquiry', '银行查询', '贷款审批查询', CURDATE(), NOW());

-- 外链管理
INSERT INTO external_link (link_name, link_url, link_type, status, create_time, update_time) VALUES
('全国法院被执行人信息查询', 'https://zxgk.court.gov.cn/', 'credit', 1, NOW(), NOW()),
('国家企业信用信息公示系统', 'https://www.gsxt.gov.cn/', 'credit', 1, NOW(), NOW()),
('中国人民银行征信中心', 'https://www.pbccrc.org.cn/', 'credit', 1, NOW(), NOW());
