/*
 Navicat Premium Data Transfer

 Source Server         : localhost_3306
 Source Server Type    : MySQL
 Source Server Version : 80036
 Source Host           : localhost:3306
 Source Schema         : py_bccabusinesssystem

 Target Server Type    : MySQL
 Target Server Version : 80036
 File Encoding         : 65001

 Date: 06/01/2026 13:41:54
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for account
-- ----------------------------
DROP TABLE IF EXISTS `account`;
CREATE TABLE `account`  (
  `id` int(0) NOT NULL AUTO_INCREMENT COMMENT '账户ID',
  `enterprise_id` int(0) NULL DEFAULT NULL COMMENT '企业ID',
  `account_no` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '账户号',
  `balance` decimal(15, 2) NULL DEFAULT 0.00 COMMENT '账户余额',
  `create_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime(0) NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '虚拟对公账户表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of account
-- ----------------------------
INSERT INTO `account` VALUES (1, 1, '6222000000000001', 100000.00, '2026-01-06 12:15:42', '2026-01-06 12:15:42');
INSERT INTO `account` VALUES (2, 2, '6222000000000002', 50000.00, '2026-01-06 12:15:42', '2026-01-06 12:15:42');
INSERT INTO `account` VALUES (3, 3, '6222000000000003', 0.00, '2026-01-06 13:27:57', '2026-01-06 13:27:57');

-- ----------------------------
-- Table structure for ai_consultation
-- ----------------------------
DROP TABLE IF EXISTS `ai_consultation`;
CREATE TABLE `ai_consultation`  (
  `id` int(0) NOT NULL AUTO_INCREMENT COMMENT '咨询ID',
  `enterprise_id` int(0) NULL DEFAULT NULL COMMENT '企业ID',
  `question` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '问题内容',
  `answer` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '回答内容',
  `create_time` datetime(0) NULL DEFAULT NULL COMMENT '咨询时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = 'AI咨询记录表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ai_consultation
-- ----------------------------
INSERT INTO `ai_consultation` VALUES (1, 3, '信用评定', '感谢您的提问。关于这个问题，建议您联系银行客服获取更详细的解答，或查看相关功能模块的帮助说明。', '2026-01-06 13:29:39');
INSERT INTO `ai_consultation` VALUES (2, 3, '利率', '贷款利率根据企业信用等级确定，A级企业可享受基准利率，其他等级会有相应上浮。具体利率以审批结果为准。', '2026-01-06 13:30:15');
INSERT INTO `ai_consultation` VALUES (3, 3, '利率怎么算', '利率计算因业务而异。贷款一般利息=本金×利率×期限。若按日利率算，日利息=本金×日利率；按月利率算，月利息=本金×月利率。存款同理，只是利息归属不同。具体以业务规则为准。 ', '2026-01-06 13:39:48');

-- ----------------------------
-- Table structure for content_review
-- ----------------------------
DROP TABLE IF EXISTS `content_review`;
CREATE TABLE `content_review`  (
  `id` int(0) NOT NULL AUTO_INCREMENT COMMENT '审核ID',
  `enterprise_id` int(0) NULL DEFAULT NULL COMMENT '企业ID',
  `content_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '内容类型: license营业执照/screenshot截图',
  `content_path` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '内容文件路径',
  `status` int(0) NULL DEFAULT 0 COMMENT '审核状态: 0待审核 1通过 2拒绝',
  `review_comment` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '审核意见',
  `reviewer_id` int(0) NULL DEFAULT NULL COMMENT '审核人ID',
  `review_time` datetime(0) NULL DEFAULT NULL COMMENT '审核时间',
  `create_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '内容审核表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of content_review
-- ----------------------------

-- ----------------------------
-- Table structure for credit_assessment
-- ----------------------------
DROP TABLE IF EXISTS `credit_assessment`;
CREATE TABLE `credit_assessment`  (
  `id` int(0) NOT NULL AUTO_INCREMENT COMMENT '评估ID',
  `enterprise_id` int(0) NULL DEFAULT NULL COMMENT '企业ID',
  `score` int(0) NULL DEFAULT NULL COMMENT '信用评分(0-100)',
  `grade` varchar(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '信用等级: A/B/C/D',
  `industry_score` int(0) NULL DEFAULT NULL COMMENT '行业评分',
  `debt_score` int(0) NULL DEFAULT NULL COMMENT '负债评分',
  `cashflow_score` int(0) NULL DEFAULT NULL COMMENT '现金流评分',
  `litigation_score` int(0) NULL DEFAULT NULL COMMENT '诉讼评分',
  `questionnaire_data` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '问卷数据JSON',
  `assess_time` datetime(0) NULL DEFAULT NULL COMMENT '评估时间',
  `create_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '信用评估表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of credit_assessment
-- ----------------------------
INSERT INTO `credit_assessment` VALUES (1, 1, 85, 'A', 23, 22, 20, 20, NULL, '2026-01-06 12:15:42', '2026-01-06 12:15:42');
INSERT INTO `credit_assessment` VALUES (2, 2, 65, 'B', 20, 15, 18, 12, NULL, '2026-01-06 12:15:42', '2026-01-06 12:15:42');

-- ----------------------------
-- Table structure for credit_history
-- ----------------------------
DROP TABLE IF EXISTS `credit_history`;
CREATE TABLE `credit_history`  (
  `id` int(0) NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  `enterprise_id` int(0) NULL DEFAULT NULL COMMENT '企业ID',
  `record_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '记录类型: inquiry查询/negative负面/positive正面',
  `record_source` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '记录来源',
  `record_content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '记录内容',
  `record_date` date NULL DEFAULT NULL COMMENT '记录日期',
  `create_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '征信记录表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of credit_history
-- ----------------------------
INSERT INTO `credit_history` VALUES (1, 1, 'inquiry', '银行查询', '贷款审批查询', '2026-01-06', '2026-01-06 12:15:42');
INSERT INTO `credit_history` VALUES (2, 1, 'positive', '纳税记录', '连续3年纳税信用A级', '2026-01-06', '2026-01-06 12:15:42');
INSERT INTO `credit_history` VALUES (3, 2, 'inquiry', '银行查询', '贷款审批查询', '2026-01-06', '2026-01-06 12:15:42');

-- ----------------------------
-- Table structure for enterprise
-- ----------------------------
DROP TABLE IF EXISTS `enterprise`;
CREATE TABLE `enterprise`  (
  `id` int(0) NOT NULL AUTO_INCREMENT COMMENT '企业ID',
  `user_id` int(0) NULL DEFAULT NULL COMMENT '关联用户ID',
  `company_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '企业名称',
  `credit_code` varchar(18) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '统一社会信用代码',
  `legal_person` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '法定代表人',
  `registered_capital` decimal(15, 2) NULL DEFAULT NULL COMMENT '注册资本(万元)',
  `industry` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '所属行业',
  `address` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '企业地址',
  `business_license` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '营业执照图片路径',
  `license_status` int(0) NULL DEFAULT 0 COMMENT '执照审核状态: 0待审核 1通过 2拒绝',
  `review_comment` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '审核意见',
  `create_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime(0) NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '企业信息表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of enterprise
-- ----------------------------
INSERT INTO `enterprise` VALUES (1, 4, '测试企业A有限公司', '91110000MA00AAAA00', '王五', 1000.00, 'technology', '北京市朝阳区xxx路xxx号', NULL, 1, NULL, '2026-01-06 12:15:42', '2026-01-06 12:15:42');
INSERT INTO `enterprise` VALUES (2, 5, '测试企业B有限公司', '91110000MA00BBBB00', '赵六', 500.00, 'manufacturing', '上海市浦东新区xxx路xxx号', NULL, 1, NULL, '2026-01-06 12:15:42', '2026-01-06 12:15:42');
INSERT INTO `enterprise` VALUES (3, 6, '123公司', NULL, NULL, NULL, NULL, NULL, NULL, 0, NULL, '2026-01-06 13:27:57', '2026-01-06 13:27:57');

-- ----------------------------
-- Table structure for external_link
-- ----------------------------
DROP TABLE IF EXISTS `external_link`;
CREATE TABLE `external_link`  (
  `id` int(0) NOT NULL AUTO_INCREMENT COMMENT '链接ID',
  `link_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '链接名称',
  `link_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '链接地址',
  `link_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '链接类型',
  `status` int(0) NULL DEFAULT 1 COMMENT '状态: 1启用 0禁用',
  `create_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime(0) NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '外链管理表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of external_link
-- ----------------------------
INSERT INTO `external_link` VALUES (1, '全国法院被执行人信息查询', 'https://zxgk.court.gov.cn/', 'credit', 1, '2026-01-06 12:15:42', '2026-01-06 12:15:42');
INSERT INTO `external_link` VALUES (2, '国家企业信用信息公示系统', 'https://www.gsxt.gov.cn/', 'credit', 1, '2026-01-06 12:15:42', '2026-01-06 12:15:42');
INSERT INTO `external_link` VALUES (3, '中国人民银行征信中心', 'https://www.pbccrc.org.cn/', 'credit', 1, '2026-01-06 12:15:42', '2026-01-06 12:15:42');

-- ----------------------------
-- Table structure for loan
-- ----------------------------
DROP TABLE IF EXISTS `loan`;
CREATE TABLE `loan`  (
  `id` int(0) NOT NULL AUTO_INCREMENT COMMENT '贷款ID',
  `enterprise_id` int(0) NULL DEFAULT NULL COMMENT '企业ID',
  `loan_no` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '贷款编号',
  `loan_amount` decimal(15, 2) NULL DEFAULT NULL COMMENT '贷款金额',
  `interest_rate` decimal(5, 2) NULL DEFAULT NULL COMMENT '年利率(%)',
  `loan_term` int(0) NULL DEFAULT NULL COMMENT '贷款期限(月)',
  `remaining_amount` decimal(15, 2) NULL DEFAULT NULL COMMENT '剩余本金',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '状态: pending待审批/approved已批准/rejected已拒绝/repaying还款中/completed已结清',
  `apply_time` datetime(0) NULL DEFAULT NULL COMMENT '申请时间',
  `approve_time` datetime(0) NULL DEFAULT NULL COMMENT '审批时间',
  `create_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '贷款表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of loan
-- ----------------------------
INSERT INTO `loan` VALUES (1, 1, 'LN202401001', 500000.00, 4.35, 12, 500000.00, 'repaying', '2026-01-06 12:15:42', NULL, '2026-01-06 12:15:42');
INSERT INTO `loan` VALUES (2, 2, 'LN202401002', 200000.00, 4.35, 6, 200000.00, 'pending', '2026-01-06 12:15:42', NULL, '2026-01-06 12:15:42');

-- ----------------------------
-- Table structure for repayment
-- ----------------------------
DROP TABLE IF EXISTS `repayment`;
CREATE TABLE `repayment`  (
  `id` int(0) NOT NULL AUTO_INCREMENT COMMENT '还款ID',
  `loan_id` int(0) NULL DEFAULT NULL COMMENT '贷款ID',
  `enterprise_id` int(0) NULL DEFAULT NULL COMMENT '企业ID',
  `repay_amount` decimal(15, 2) NULL DEFAULT NULL COMMENT '还款金额',
  `principal` decimal(15, 2) NULL DEFAULT NULL COMMENT '本金部分',
  `interest` decimal(15, 2) NULL DEFAULT NULL COMMENT '利息部分',
  `repay_date` date NULL DEFAULT NULL COMMENT '还款日期',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '状态: pending待还款/paid已还款/overdue逾期',
  `actual_repay_time` datetime(0) NULL DEFAULT NULL COMMENT '实际还款时间',
  `create_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '还款记录表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of repayment
-- ----------------------------

-- ----------------------------
-- Table structure for transaction
-- ----------------------------
DROP TABLE IF EXISTS `transaction`;
CREATE TABLE `transaction`  (
  `id` int(0) NOT NULL AUTO_INCREMENT COMMENT '交易ID',
  `account_id` int(0) NULL DEFAULT NULL COMMENT '账户ID',
  `enterprise_id` int(0) NULL DEFAULT NULL COMMENT '企业ID',
  `trans_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '交易类型: deposit存入/withdraw支取',
  `amount` decimal(15, 2) NULL DEFAULT NULL COMMENT '交易金额',
  `balance_after` decimal(15, 2) NULL DEFAULT NULL COMMENT '交易后余额',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '备注',
  `create_time` datetime(0) NULL DEFAULT NULL COMMENT '交易时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '交易流水表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of transaction
-- ----------------------------
INSERT INTO `transaction` VALUES (1, 1, 1, 'deposit', 100000.00, 100000.00, '初始存款', '2026-01-06 12:15:42');
INSERT INTO `transaction` VALUES (2, 2, 2, 'deposit', 50000.00, 50000.00, '初始存款', '2026-01-06 12:15:42');

-- ----------------------------
-- Table structure for user
-- ----------------------------
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user`  (
  `id` int(0) NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户名',
  `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '密码',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '姓名/企业名称',
  `role` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '角色: enterprise/employee/admin',
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '联系电话',
  `email` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '邮箱',
  `status` int(0) NULL DEFAULT 1 COMMENT '状态: 1启用 0禁用',
  `create_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime(0) NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 7 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '用户表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of user
-- ----------------------------
INSERT INTO `user` VALUES (1, 'admin', 'admin123', '系统管理员', 'admin', '13800000000', 'admin@bank.com', 1, '2026-01-06 12:15:42', '2026-01-06 12:15:42');
INSERT INTO `user` VALUES (2, 'a1', '123456', '张三', 'employee', '13800000001', 'zhangsan@bank.com', 1, '2026-01-06 12:15:42', '2026-01-06 12:15:42');
INSERT INTO `user` VALUES (3, 'a2', '123456', '李四', 'employee', '13800000002', 'lisi@bank.com', 1, '2026-01-06 12:15:42', '2026-01-06 12:15:42');
INSERT INTO `user` VALUES (4, '2', '2', '测试企业A', 'enterprise', '13800000003', 'companya@test.com', 1, '2026-01-06 12:15:42', '2026-01-06 12:15:42');
INSERT INTO `user` VALUES (5, '3', '3', '测试企业B', 'enterprise', '13800000004', 'companyb@test.com', 1, '2026-01-06 12:15:42', '2026-01-06 12:15:42');
INSERT INTO `user` VALUES (6, '1', '1', '123公司', 'enterprise', '13888888888', '1@qq.com', 1, '2026-01-06 13:27:57', '2026-01-06 13:27:57');

SET FOREIGN_KEY_CHECKS = 1;
ALTER TABLE credit_assessment ADD COLUMN score_type VARCHAR(10) DEFAULT 'rule' COMMENT '评分类型：rule-规则化，ml-机器学习';