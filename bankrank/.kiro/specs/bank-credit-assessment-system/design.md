# Design Document

## Overview

银行对公信用评估业务系统是一个基于Flask的Web应用，采用青蓝色商务风主题白色背景风格。系统支持三种角色：企业用户、银行员工、系统管理员，分别提供不同的功能模块。

技术栈：
- 后端：Flask + PyMySQL
- 前端：HTML + TailwindCSS + jQuery + ECharts + Layer.js
- 数据库：MySQL (py_bccabusinesssystem)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Presentation Layer                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Enterprise  │  │  Employee   │  │       Admin         │  │
│  │   Portal    │  │   Portal    │  │      Portal         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Application Layer                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │  Auth    │ │ Account  │ │  Loan    │ │   Credit     │   │
│  │ Module   │ │ Module   │ │ Module   │ │  Assessment  │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │Enterprise│ │  Admin   │ │   AI     │ │ External     │   │
│  │  Info    │ │  CRUD    │ │ Consult  │ │   Links      │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                       Data Layer                             │
│              ┌─────────────────────────┐                    │
│              │    MySQL Database       │                    │
│              │  py_bccabusinesssystem     │                    │
│              └─────────────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Flask Application (app.py)

主应用入口，包含路由定义和视图函数。

```python
# 配置
app.config['SECRET_KEY'] = 'bank_credit_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# 数据库连接
def get_db():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='123456',
        database='py_bccabusinesssystem',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
```

### 2. Authentication Module

```python
# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 角色验证装饰器
def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('role') != role:
                flash('无权访问')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

### 3. Credit Assessment Scorecard Model

```python
def calculate_credit_score(questionnaire_data):
    """
    评分卡模型计算信用评分
    输入：问卷数据（行业、负债、现金流、诉讼等）
    输出：0-100分数和A/B/C/D等级
    """
    score = 0
    
    # 行业评分 (0-25分)
    industry_scores = {
        'finance': 25, 'technology': 23, 'manufacturing': 20,
        'retail': 18, 'construction': 15, 'other': 12
    }
    score += industry_scores.get(questionnaire_data['industry'], 12)
    
    # 负债率评分 (0-25分)
    debt_ratio = questionnaire_data['debt_ratio']
    if debt_ratio < 30:
        score += 25
    elif debt_ratio < 50:
        score += 20
    elif debt_ratio < 70:
        score += 15
    else:
        score += 5
    
    # 现金流评分 (0-25分)
    cash_flow = questionnaire_data['cash_flow_status']
    cash_flow_scores = {'excellent': 25, 'good': 20, 'normal': 15, 'poor': 5}
    score += cash_flow_scores.get(cash_flow, 10)
    
    # 诉讼记录评分 (0-25分)
    litigation_count = questionnaire_data['litigation_count']
    if litigation_count == 0:
        score += 25
    elif litigation_count <= 2:
        score += 15
    elif litigation_count <= 5:
        score += 8
    else:
        score += 0
    
    # 确定等级
    if score >= 80:
        grade = 'A'
    elif score >= 60:
        grade = 'B'
    elif score >= 40:
        grade = 'C'
    else:
        grade = 'D'
    
    return score, grade
```

### 4. AI Consultation Module

```python
def get_ai_response(question):
    """
    AI咨询模块 - 仅回答业务相关问题
    """
    # 业务关键词
    business_keywords = ['信用', '评估', '贷款', '还款', '征信', '上传', 
                        '营业执照', '企业信息', '存款', '取款', '账户']
    
    # 检查是否为业务相关问题
    is_business_related = any(kw in question for kw in business_keywords)
    
    if not is_business_related:
        return "抱歉，我只能回答与信用评估、贷款、企业信息等业务相关的问题。请问您有什么业务方面的疑问？"
    
    # 预设问答库
    qa_database = {
        '信用评估': '信用评估是根据企业的行业类型、负债率、现金流状况、诉讼记录等因素，通过评分卡模型计算0-100分的信用评分，并给出A/B/C/D等级。',
        '贷款': '企业可以在贷款还款模块查看当前贷款状态、还款进度。贷款审批需要银行员工根据信用评估结果进行。',
        # ... 更多预设回答
    }
    
    # 匹配回答
    for keyword, answer in qa_database.items():
        if keyword in question:
            return answer
    
    return "感谢您的提问。关于这个问题，建议您联系银行客服获取更详细的解答。"
```

## Data Models

### Database Schema (MySQL)

```sql
-- 数据库: py_bccabusinesssystem
-- 用户名: root
-- 密码: root

-- 用户表
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
CREATE TABLE account (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '账户ID',
    enterprise_id INT COMMENT '企业ID',
    account_no VARCHAR(20) COMMENT '账户号',
    balance DECIMAL(15,2) DEFAULT 0 COMMENT '账户余额',
    create_time DATETIME COMMENT '创建时间',
    update_time DATETIME COMMENT '更新时间'
) COMMENT='虚拟对公账户表';

-- 交易流水表
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
CREATE TABLE ai_consultation (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '咨询ID',
    enterprise_id INT COMMENT '企业ID',
    question TEXT COMMENT '问题内容',
    answer TEXT COMMENT '回答内容',
    create_time DATETIME COMMENT '咨询时间'
) COMMENT='AI咨询记录表';
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Transaction Balance Integrity
*For any* deposit or withdrawal transaction, the account balance after the transaction SHALL equal the balance before plus the deposit amount (or minus the withdrawal amount).
**Validates: Requirements 2.2, 2.3**

### Property 2: Withdrawal Validation
*For any* withdrawal attempt where the amount exceeds the current balance, the system SHALL reject the transaction and the balance SHALL remain unchanged.
**Validates: Requirements 2.4**

### Property 3: Credit Score Calculation Consistency
*For any* valid questionnaire submission, the calculated credit score SHALL be between 0 and 100, and the sum of component scores (industry + debt + cashflow + litigation) SHALL equal the total score.
**Validates: Requirements 8.1**

### Property 4: Credit Grade Assignment
*For any* credit score, the assigned grade SHALL follow: A for 80-100, B for 60-79, C for 40-59, D for 0-39.
**Validates: Requirements 8.2**

### Property 5: Unified Social Credit Code Validation
*For any* enterprise information submission, the unified social credit code SHALL be exactly 18 characters.
**Validates: Requirements 4.2**

### Property 6: Repayment Balance Update
*For any* loan repayment, the remaining loan amount SHALL decrease by the principal portion of the repayment.
**Validates: Requirements 3.2**

### Property 7: User CRUD Data Integrity
*For any* user creation, the user SHALL be retrievable with all submitted fields intact. For any update, only the modified fields SHALL change. For any deletion, the user SHALL no longer be retrievable.
**Validates: Requirements 14.1-14.4**

### 5. Risk Warning Module

```python
# 企业端风险预警路由
@app.route('/enterprise/risk_warning')
@login_required
@role_required('enterprise')
def enterprise_risk_warning():
    # 从数据库获取风险数据
    # 1. 获取最新评估数据
    # 2. 获取历史评估趋势
    # 3. 获取贷款风险数据
    # 4. 获取交易波动数据
    # 5. 计算风险指标
    pass

# 员工端风险预警路由
@app.route('/employee/risk_warning')
@login_required
@role_required('employee')
def employee_risk_warning():
    # 从数据库获取风险监控数据
    # 1. 获取高风险企业列表
    # 2. 获取各等级企业数量分布
    # 3. 获取贷款风险统计
    # 4. 获取最近30天评估趋势
    # 5. 获取风险预警企业（评分低于50分）
    pass
```

### 6. Login Page Background

登录页面使用 `static/img/image.png` 作为背景图片，通过CSS实现全屏背景覆盖效果。

```css
/* 登录页面背景样式 */
.login-background {
    background-image: url('/static/img/image.png');
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    min-height: 100vh;
}

.login-overlay {
    background: rgba(0, 0, 0, 0.4);
    min-height: 100vh;
}
```

## Error Handling

### Authentication Errors
- Invalid credentials: Display error message, remain on login page
- Session expired: Redirect to login page
- Unauthorized access: Redirect to appropriate dashboard with error message

### Transaction Errors
- Insufficient balance: Reject withdrawal, display error
- Invalid amount: Reject transaction, display validation error
- Database error: Rollback transaction, display system error

### File Upload Errors
- Invalid file type: Reject upload, display allowed types
- File too large: Reject upload, display size limit
- Upload failure: Display error, allow retry

### API Errors
- AI consultation timeout: Display fallback message
- External link unavailable: Display error with retry option

## Testing Strategy

### Unit Tests
- Test individual functions for credit score calculation
- Test validation functions for input data
- Test database CRUD operations

### Property-Based Tests
- Use pytest with hypothesis library
- Minimum 100 iterations per property test
- Test transaction integrity across random amounts
- Test credit score calculation with random questionnaire data

### Integration Tests
- Test complete user flows (login → action → logout)
- Test role-based access control
- Test file upload and review workflow

