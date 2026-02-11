# Implementation Plan: 银行对公信用评估业务系统

## Overview

基于Flask+PyMySQL+HTML实现银行对公信用评估业务系统，采用青蓝色商务风白色背景主题。

## Tasks

- [x] 1. 数据库初始化和项目结构搭建
  - [x] 1.1 创建数据库初始化SQL脚本
    - 创建所有数据表（user, enterprise, account, transaction, loan, repayment, credit_assessment, credit_history, external_link, content_review, ai_consultation）
    - 插入初始管理员账户和测试数据
    - _Requirements: 全部数据模型_

  - [x] 1.2 创建Flask应用主文件和数据库连接
    - 配置Flask应用
    - 实现PyMySQL数据库连接函数
    - 实现登录验证装饰器
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. 基础模板和认证模块
  - [x] 2.1 更新base.html为青蓝色商务风白色背景主题
    - 修改颜色方案为青蓝色+白色背景
    - 移除输入框图标样式
    - 实现三种角色的导航布局
    - _Requirements: 17.1, 17.2, 17.3, 17.4_

  - [x] 2.2 实现登录注册页面
    - 创建login.html登录页面
    - 创建register.html注册页面
    - 实现登录注册路由和逻辑
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 3. 企业端功能模块
  - [x] 3.1 实现企业仪表盘
    - 创建enterprise/dashboard.html
    - 显示账户余额、贷款状态、信用评分概览
    - _Requirements: 2.1, 3.1, 6.1_

  - [x] 3.2 实现存取款模块
    - 创建enterprise/account.html
    - 实现余额查询、存入、支取功能
    - 实现交易流水明细展示
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 3.3 实现贷款还款模块
    - 创建enterprise/loan.html
    - 显示贷款列表和还款进度
    - 实现还款功能
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 3.4 实现企业信息管理模块
    - 创建enterprise/company_info.html
    - 实现企业信息编辑和保存
    - 实现营业执照图片上传
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [x] 3.5 实现征信信息查询模块
    - 创建enterprise/credit_query.html
    - 实现外链跳转功能
    - _Requirements: 5.1, 5.2_

  - [x] 3.6 实现信用评估动态可视化模块
    - 创建enterprise/credit_visual.html
    - 使用ECharts实现仪表盘图表
    - 实现雷达图、折线图、柱状图
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 3.7 实现信用评估问卷模块
    - 创建enterprise/assessment.html
    - 实现问卷表单
    - 实现评分卡模型计算逻辑
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [x] 3.8 实现AI咨询模块
    - 创建浮窗聊天组件
    - 实现业务问答逻辑
    - 实现非业务问题拒绝回答
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] 4. 银行员工端功能模块
  - [x] 4.1 实现员工仪表盘
    - 创建employee/dashboard.html
    - 显示企业客户统计、贷款统计等
    - _Requirements: 9.1_

  - [x] 4.2 实现企业账户信息管理
    - 创建employee/enterprise_list.html
    - 实现企业列表查看和搜索
    - 实现企业详情查看
    - _Requirements: 9.1, 9.2, 9.3_

  - [x] 4.3 实现企业征信记录管理
    - 创建employee/credit_records.html
    - 显示企业征信历史
    - _Requirements: 10.1, 10.2, 10.3_

  - [x] 4.4 实现企业信用评估结果管理
    - 创建employee/assessment_results.html
    - 显示评估结果列表
    - 实现按等级筛选
    - _Requirements: 11.1, 11.2, 11.3_

  - [x] 4.5 实现企业贷款与还款管理
    - 创建employee/loan_manage.html
    - 实现贷款审批功能
    - 显示还款记录
    - _Requirements: 12.1, 12.2, 12.3, 12.4_

  - [x] 4.6 实现企业存取款管理
    - 创建employee/transaction_records.html
    - 显示交易记录列表
    - 实现筛选功能
    - _Requirements: 13.1, 13.2, 13.3_

- [x] 5. 后台管理员端功能模块
  - [x] 5.1 实现管理员仪表盘
    - 创建admin/dashboard.html
    - 显示系统统计数据
    - _Requirements: 14.1_

  - [x] 5.2 实现用户信息管理
    - 创建admin/user_manage.html
    - 实现用户增删改查
    - 实现角色筛选
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

  - [x] 5.3 实现内容审核管理
    - 创建admin/content_review.html
    - 显示待审核内容列表
    - 实现审核通过/拒绝功能
    - _Requirements: 15.1, 15.2, 15.3, 15.4_

  - [x] 5.4 实现外链管理
    - 创建admin/link_manage.html
    - 实现外链增删改查
    - _Requirements: 16.1, 16.2, 16.3, 16.4_

  - [x] 5.5 实现企业数据管理
    - 创建admin/enterprise_data.html
    - 实现企业数据增删改查
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_

  - [x] 5.6 实现交易数据管理
    - 创建admin/transaction_data.html
    - 实现交易数据增删改查
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5_

  - [x] 5.7 实现贷款数据管理
    - 创建admin/loan_data.html
    - 实现贷款数据增删改查
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5_

  - [x] 5.8 实现还款数据管理
    - 创建admin/repayment_data.html
    - 实现还款数据增删改查
    - _Requirements: 21.1, 21.2, 21.3, 21.4, 21.5_

  - [x] 5.9 实现评估数据管理
    - 创建admin/assessment_data.html
    - 实现评估数据增删改查
    - _Requirements: 22.1, 22.2, 22.3, 22.4, 22.5_

  - [x] 5.10 实现征信数据管理
    - 创建admin/credit_history_data.html
    - 实现征信数据增删改查
    - _Requirements: 23.1, 23.2, 23.3, 23.4, 23.5_

- [x] 6. 最终检查
  - [x] 6.1 确保所有功能正常运行
    - 测试所有角色登录
    - 测试所有CRUD操作
    - 测试文件上传功能

- [x] 7. 风险预警模块和UI优化
  - [x] 7.1 更新登录页面添加背景图片
    - 使用static/img/image.png作为登录页面背景
    - 添加半透明遮罩层提升可读性
    - 优化登录表单样式
    - _Requirements: 17.6, 17.7_

  - [x] 7.2 确保企业端风险预警数据来自数据库
    - 验证风险指标从credit_assessment表获取
    - 验证历史趋势数据从数据库查询
    - 验证贷款风险数据从loan表获取
    - 验证现金流数据从transaction表获取
    - _Requirements: 24.1, 24.2, 24.3, 24.4, 24.5, 24.6, 24.7, 24.8_

  - [x] 7.3 确保银行员工端风险预警数据来自数据库
    - 验证贷款统计从loan表获取
    - 验证信用等级分布从credit_assessment表获取
    - 验证评估趋势从数据库查询
    - 验证高风险企业列表从数据库查询
    - _Requirements: 25.1, 25.2, 25.3, 25.4, 25.5, 25.6, 25.7_

## Notes

- 使用Flask+PyMySQL+HTML技术栈
- 数据库: py_bccabusinesssystem (root/root)
- 青蓝色商务风白色背景主题
- 输入框不显示图标
- 使用ECharts实现可视化图表
