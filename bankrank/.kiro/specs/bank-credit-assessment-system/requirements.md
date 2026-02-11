# Requirements Document

## Introduction

基于Flask的银行对公信用评估业务系统，采用青蓝色商务风主题白色背景风格。系统分为三个角色端：企业端、银行员工端、后台管理员端。使用Flask+PyMySQL+HTML技术栈，数据库为py_bccabusinesssystem（用户名密码均为root）。

## Glossary

- **Enterprise_User**: 企业用户，使用系统进行存取款、贷款还款、信用评估等操作
- **Bank_Employee**: 银行员工，管理企业账户、征信记录、贷款还款等
- **System_Admin**: 系统管理员，管理用户、审核内容、管理外链
- **Credit_Assessment_System**: 信用评估系统，提供企业信用评分和等级评定
- **Virtual_Account**: 虚拟对公账户，用于模拟企业资金变动
- **Scorecard_Model**: 评分卡模型，用于计算企业信用评分

## Requirements

### Requirement 1: 用户认证与角色管理

**User Story:** As a user, I want to login with my credentials and access role-specific features, so that I can use the system according to my permissions.

#### Acceptance Criteria

1. WHEN a user submits valid credentials, THE System SHALL authenticate the user and redirect to role-specific dashboard
2. WHEN a user submits invalid credentials, THE System SHALL display an error message and remain on login page
3. THE System SHALL support three user roles: enterprise (企业), employee (银行员工), admin (管理员)
4. WHEN a user logs out, THE System SHALL clear session and redirect to login page

### Requirement 2: 企业端 - 存取款模块

**User Story:** As an enterprise user, I want to manage my virtual corporate account, so that I can track fund movements and provide transaction data for credit assessment.

#### Acceptance Criteria

1. WHEN an enterprise user accesses the deposit/withdrawal module, THE System SHALL display current account balance
2. WHEN an enterprise user deposits funds, THE System SHALL increase account balance and create a transaction record
3. WHEN an enterprise user withdraws funds, THE System SHALL decrease account balance and create a transaction record
4. IF an enterprise user attempts to withdraw more than available balance, THEN THE System SHALL reject the transaction and display an error
5. WHEN an enterprise user views transaction history, THE System SHALL display all deposit/withdrawal records with date, type, amount, and balance

### Requirement 3: 企业端 - 贷款还款模块

**User Story:** As an enterprise user, I want to view my loan and repayment progress, so that I can track my financial obligations.

#### Acceptance Criteria

1. WHEN an enterprise user accesses the loan module, THE System SHALL display all active loans with amount, interest rate, and remaining balance
2. WHEN an enterprise user views repayment schedule, THE System SHALL display payment dates, amounts, and status
3. WHEN an enterprise user makes a repayment, THE System SHALL update loan balance and create a repayment record

### Requirement 4: 企业端 - 企业信息管理模块

**User Story:** As an enterprise user, I want to maintain my company information, so that the bank has accurate data for credit assessment.

#### Acceptance Criteria

1. WHEN an enterprise user accesses company info module, THE System SHALL display current company information
2. WHEN an enterprise user updates company information, THE System SHALL save changes including name, unified social credit code, legal representative, registered capital, and industry
3. WHEN an enterprise user uploads business license image, THE System SHALL store the image and mark it as pending review
4. THE System SHALL validate unified social credit code format (18 characters)

### Requirement 5: 企业端 - 征信信息查询模块

**User Story:** As an enterprise user, I want to access external credit information, so that I can check court records and other credit data.

#### Acceptance Criteria

1. WHEN an enterprise user clicks credit inquiry link, THE System SHALL redirect to the configured external credit information website
2. THE System SHALL display the external link in a new browser tab

### Requirement 6: 企业端 - 信用评估动态可视化模块

**User Story:** As an enterprise user, I want to view my credit assessment results visually, so that I can understand my credit position among bank customers.

#### Acceptance Criteria

1. WHEN an enterprise user accesses credit visualization, THE System SHALL display credit score using ECharts gauge chart
2. THE System SHALL display credit grade (A/B/C/D) with corresponding color coding
3. THE System SHALL display risk structure analysis using radar chart
4. THE System SHALL display historical credit score trend using line chart
5. THE System SHALL display enterprise ranking among all customers using bar chart

### Requirement 7: 企业端 - AI咨询模块

**User Story:** As an enterprise user, I want to ask questions about credit assessment and loan rules, so that I can get accurate business-related answers.

#### Acceptance Criteria

1. WHEN an enterprise user opens AI consultation, THE System SHALL display a floating chat window
2. WHEN an enterprise user asks business-related questions, THE System SHALL provide accurate answers about credit assessment, information upload, and loan rules
3. WHEN an enterprise user asks unrelated questions, THE System SHALL politely decline and redirect to business topics
4. THE System SHALL maintain conversation context within the session

### Requirement 8: 企业端 - 信用评估问卷模块

**User Story:** As an enterprise user, I want to complete credit assessment questionnaire, so that I can receive my credit score and grade.

#### Acceptance Criteria

1. WHEN an enterprise user starts credit assessment, THE System SHALL display questionnaire covering industry, debt, cash flow, and litigation
2. WHEN an enterprise user submits questionnaire, THE System SHALL calculate credit score (0-100) using scorecard model
3. THE System SHALL assign credit grade based on score: A (80-100), B (60-79), C (40-59), D (0-39)
4. THE System SHALL store assessment results and display them immediately

### Requirement 9: 银行员工端 - 企业账户信息管理模块

**User Story:** As a bank employee, I want to view and manage enterprise customer accounts, so that I can provide customer service.

#### Acceptance Criteria

1. WHEN a bank employee accesses enterprise management, THE System SHALL display list of all enterprise customers
2. WHEN a bank employee searches for enterprise, THE System SHALL filter results by name or credit code
3. WHEN a bank employee views enterprise details, THE System SHALL display registration info, contact details, and account status

### Requirement 10: 银行员工端 - 企业征信记录管理模块

**User Story:** As a bank employee, I want to view enterprise credit records, so that I can assess customer creditworthiness.

#### Acceptance Criteria

1. WHEN a bank employee accesses credit records, THE System SHALL display enterprise credit history
2. THE System SHALL display credit inquiry records with date and source
3. THE System SHALL display any negative credit events

### Requirement 11: 银行员工端 - 企业信用评估结果管理模块

**User Story:** As a bank employee, I want to view and manage credit assessment results, so that I can make lending decisions.

#### Acceptance Criteria

1. WHEN a bank employee accesses assessment results, THE System SHALL display all enterprise credit scores and grades
2. WHEN a bank employee filters by grade, THE System SHALL show only enterprises with selected grade
3. THE System SHALL display assessment history for each enterprise

### Requirement 12: 银行员工端 - 企业贷款与还款管理模块

**User Story:** As a bank employee, I want to manage enterprise loans and repayments, so that I can track lending activities.

#### Acceptance Criteria

1. WHEN a bank employee accesses loan management, THE System SHALL display all enterprise loans
2. WHEN a bank employee creates a new loan, THE System SHALL record loan details including amount, interest rate, term, and enterprise
3. WHEN a bank employee views repayment records, THE System SHALL display all repayment transactions
4. THE System SHALL calculate and display overdue status for each loan

### Requirement 13: 银行员工端 - 企业存取款管理模块

**User Story:** As a bank employee, I want to view enterprise deposit/withdrawal records, so that I can monitor account activities.

#### Acceptance Criteria

1. WHEN a bank employee accesses transaction records, THE System SHALL display all enterprise deposit/withdrawal transactions
2. WHEN a bank employee filters by enterprise, THE System SHALL show only selected enterprise transactions
3. WHEN a bank employee filters by date range, THE System SHALL show transactions within the specified period

### Requirement 14: 后台管理员端 - 用户信息管理模块

**User Story:** As an admin, I want to manage all user accounts, so that I can control system access.

#### Acceptance Criteria

1. WHEN an admin accesses user management, THE System SHALL display all users with role information
2. WHEN an admin creates a new user, THE System SHALL save user with specified role (enterprise/employee/admin)
3. WHEN an admin updates user information, THE System SHALL save changes
4. WHEN an admin deletes a user, THE System SHALL remove user from system
5. THE System SHALL support searching users by username or role

### Requirement 15: 后台管理员端 - 内容审核管理模块

**User Story:** As an admin, I want to review uploaded content, so that I can ensure data quality and compliance.

#### Acceptance Criteria

1. WHEN an admin accesses content review, THE System SHALL display all pending review items
2. WHEN an admin approves content, THE System SHALL mark content as approved and notify enterprise
3. WHEN an admin rejects content, THE System SHALL mark content as rejected with reason and notify enterprise
4. THE System SHALL display business license images and information screenshots for review

### Requirement 16: 后台管理员端 - 外链管理模块

**User Story:** As an admin, I want to manage external credit information links, so that I can keep links up to date.

#### Acceptance Criteria

1. WHEN an admin accesses link management, THE System SHALL display all configured external links
2. WHEN an admin updates a link URL, THE System SHALL save the new URL
3. WHEN an admin adds a new link, THE System SHALL create new link entry with name and URL
4. WHEN an admin deletes a link, THE System SHALL remove the link from system

### Requirement 18: 后台管理员端 - 企业数据管理模块

**User Story:** As an admin, I want to manage all enterprise data, so that I can maintain data integrity.

#### Acceptance Criteria

1. WHEN an admin accesses enterprise data management, THE System SHALL display all enterprise records
2. WHEN an admin creates enterprise record, THE System SHALL save new enterprise information
3. WHEN an admin updates enterprise record, THE System SHALL save changes
4. WHEN an admin deletes enterprise record, THE System SHALL remove the record
5. THE System SHALL support searching and filtering enterprise records

### Requirement 19: 后台管理员端 - 交易数据管理模块

**User Story:** As an admin, I want to manage all transaction data, so that I can maintain accurate financial records.

#### Acceptance Criteria

1. WHEN an admin accesses transaction data management, THE System SHALL display all deposit/withdrawal records
2. WHEN an admin creates transaction record, THE System SHALL save new transaction
3. WHEN an admin updates transaction record, THE System SHALL save changes
4. WHEN an admin deletes transaction record, THE System SHALL remove the record
5. THE System SHALL support filtering by enterprise, date range, and transaction type

### Requirement 20: 后台管理员端 - 贷款数据管理模块

**User Story:** As an admin, I want to manage all loan data, so that I can oversee lending activities.

#### Acceptance Criteria

1. WHEN an admin accesses loan data management, THE System SHALL display all loan records
2. WHEN an admin creates loan record, THE System SHALL save new loan information
3. WHEN an admin updates loan record, THE System SHALL save changes
4. WHEN an admin deletes loan record, THE System SHALL remove the record
5. THE System SHALL support filtering by enterprise, status, and date range

### Requirement 21: 后台管理员端 - 还款数据管理模块

**User Story:** As an admin, I want to manage all repayment data, so that I can track payment activities.

#### Acceptance Criteria

1. WHEN an admin accesses repayment data management, THE System SHALL display all repayment records
2. WHEN an admin creates repayment record, THE System SHALL save new repayment
3. WHEN an admin updates repayment record, THE System SHALL save changes
4. WHEN an admin deletes repayment record, THE System SHALL remove the record
5. THE System SHALL support filtering by loan, enterprise, and date range

### Requirement 22: 后台管理员端 - 评估数据管理模块

**User Story:** As an admin, I want to manage all credit assessment data, so that I can maintain assessment records.

#### Acceptance Criteria

1. WHEN an admin accesses assessment data management, THE System SHALL display all assessment records
2. WHEN an admin creates assessment record, THE System SHALL save new assessment with score and grade
3. WHEN an admin updates assessment record, THE System SHALL save changes
4. WHEN an admin deletes assessment record, THE System SHALL remove the record
5. THE System SHALL support filtering by enterprise, grade, and date range

### Requirement 23: 后台管理员端 - 征信数据管理模块

**User Story:** As an admin, I want to manage all credit history data, so that I can maintain credit records.

#### Acceptance Criteria

1. WHEN an admin accesses credit history data management, THE System SHALL display all credit history records
2. WHEN an admin creates credit history record, THE System SHALL save new record
3. WHEN an admin updates credit history record, THE System SHALL save changes
4. WHEN an admin deletes credit history record, THE System SHALL remove the record
5. THE System SHALL support filtering by enterprise and record type

### Requirement 17: 系统界面风格

**User Story:** As a user, I want a professional business-style interface, so that I can use the system comfortably.

#### Acceptance Criteria

1. THE System SHALL use cyan-blue (青蓝色) business theme with white background
2. THE System SHALL NOT display icons inside input fields
3. THE System SHALL use components from the static folder
4. THE System SHALL follow the base.html template structure with modified color scheme
5. THE System SHALL be responsive and work on different screen sizes
6. WHEN a user visits the login page, THE System SHALL display a background image using static/img/image.png
7. THE System SHALL provide visually appealing login interface with background image overlay

### Requirement 24: 企业端风险预警模块

**User Story:** As an enterprise user, I want to view risk warnings based on my assessment data, so that I can understand and manage potential risks.

#### Acceptance Criteria

1. WHEN an enterprise user accesses risk warning module, THE System SHALL display risk indicators from database
2. THE System SHALL calculate and display overall risk level (low/medium/high) based on credit assessment data
3. THE System SHALL display financial risk, legal risk, operational risk, and credit risk indicators
4. THE System SHALL display risk radar chart using ECharts with data from database
5. THE System SHALL display credit score trend chart with historical assessment data
6. THE System SHALL display cash flow analysis chart with transaction data from database
7. THE System SHALL display loan risk analysis with data from loan table
8. THE System SHALL provide risk warning suggestions based on risk indicators

### Requirement 25: 银行员工端风险预警监控模块

**User Story:** As a bank employee, I want to monitor enterprise risk warnings, so that I can identify and manage high-risk customers.

#### Acceptance Criteria

1. WHEN a bank employee accesses risk warning module, THE System SHALL display loan statistics from database
2. THE System SHALL display credit grade distribution pie chart with data from credit_assessment table
3. THE System SHALL display assessment trend analysis chart with recent 30 days data
4. THE System SHALL display risk heatmap showing risk distribution across enterprises
5. THE System SHALL display high-risk enterprise warning list (score below 50) from database
6. THE System SHALL display enterprise risk ranking sorted by credit score ascending
7. THE System SHALL show total debt amount for each enterprise from loan table
