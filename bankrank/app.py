from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import pymysql
import os
from datetime import datetime
import json
import requests
from decimal import Decimal, ROUND_HALF_UP  # 新增：导入Decimal相关工具
# 新增机器学习相关导入
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
import joblib
import os

app = Flask(__name__)
app.secret_key = 'bank_credit_secret_key_2024'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


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


# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('请先登录')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


# 角色验证装饰器
def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('role') != role:
                flash('无权访问该页面')
                return redirect(url_for('login'))
            return f(*args, **kwargs)

        return decorated_function

    return decorator


# 信用评分计算函数 - 15题评估
def calculate_credit_score(data):
    scores = {}

    # 1. 行业评分 (0-7分)
    industry_scores = {'finance': 7, 'technology': 6, 'manufacturing': 5, 'retail': 4, 'construction': 3, 'other': 2}
    scores['industry'] = industry_scores.get(data.get('industry', 'other'), 2)

    # 2. 负债率评分 (0-7分)
    try:
        debt_ratio = float(data.get('debt_ratio', 50))
    except (ValueError, TypeError):
        debt_ratio = 50.0
    if debt_ratio < 30:
        scores['debt'] = 7
    elif debt_ratio < 50:
        scores['debt'] = 5
    elif debt_ratio < 70:
        scores['debt'] = 3
    else:
        scores['debt'] = 1

    # 3. 现金流评分 (0-7分)
    cashflow_scores = {'excellent': 7, 'good': 5, 'normal': 3, 'poor': 1}
    scores['cashflow'] = cashflow_scores.get(data.get('cash_flow', 'normal'), 3)

    # 4. 诉讼记录评分 (0-7分)
    try:
        litigation = int(data.get('litigation_count', 0))
    except (ValueError, TypeError):
        litigation = 0
    if litigation == 0:
        scores['litigation'] = 7
    elif litigation <= 2:
        scores['litigation'] = 5
    elif litigation <= 5:
        scores['litigation'] = 2
    else:
        scores['litigation'] = 0

    # 5. 企业成立年限 (0-7分)
    try:
        years = int(data.get('company_years', 3))
    except (ValueError, TypeError):
        years = 3
    if years >= 10:
        scores['years'] = 7
    elif years >= 5:
        scores['years'] = 5
    elif years >= 3:
        scores['years'] = 3
    else:
        scores['years'] = 1

    # 6. 注册资本规模 (0-7分)
    capital_scores = {'above_5000': 7, '1000_5000': 5, '500_1000': 4, '100_500': 3, 'below_100': 1}
    scores['capital'] = capital_scores.get(data.get('registered_capital_range', 'below_100'), 1)

    # 7. 年营业收入 (0-7分)
    revenue_scores = {'above_1y': 7, '5000w_1y': 6, '1000w_5000w': 5, '500w_1000w': 3, 'below_500w': 1}
    scores['revenue'] = revenue_scores.get(data.get('annual_revenue', 'below_500w'), 1)

    # 8. 净利润率 (0-7分)
    profit_scores = {'above_20': 7, '10_20': 5, '5_10': 4, '0_5': 2, 'negative': 0}
    scores['profit'] = profit_scores.get(data.get('profit_rate', '0_5'), 2)

    # 9. 资产负债结构 (0-7分)
    asset_scores = {'excellent': 7, 'good': 5, 'normal': 3, 'poor': 1}
    scores['asset_structure'] = asset_scores.get(data.get('asset_structure', 'normal'), 3)

    # 10. 银行信贷记录 (0-7分)
    credit_scores = {'excellent': 7, 'good': 5, 'normal': 3, 'poor': 1, 'none': 2}
    scores['bank_credit'] = credit_scores.get(data.get('bank_credit_record', 'normal'), 3)

    # 11. 税务信用等级 (0-6分)
    tax_scores = {'A': 6, 'B': 5, 'C': 3, 'D': 1, 'M': 4}
    scores['tax_credit'] = tax_scores.get(data.get('tax_credit_level', 'B'), 3)

    # 12. 社保缴纳情况 (0-6分)
    social_scores = {'full': 6, 'partial': 4, 'irregular': 2, 'none': 0}
    scores['social_security'] = social_scores.get(data.get('social_security', 'partial'), 2)

    # 13. 供应链稳定性 (0-6分)
    supply_scores = {'very_stable': 6, 'stable': 5, 'normal': 3, 'unstable': 1}
    scores['supply_chain'] = supply_scores.get(data.get('supply_chain', 'normal'), 3)

    # 14. 市场竞争力 (0-6分)
    market_scores = {'leader': 6, 'strong': 5, 'normal': 3, 'weak': 1}
    scores['market_position'] = market_scores.get(data.get('market_position', 'normal'), 3)

    # 15. 管理团队经验 (0-6分)
    team_scores = {'excellent': 6, 'experienced': 5, 'normal': 3, 'inexperienced': 1}
    scores['management_team'] = team_scores.get(data.get('management_team', 'normal'), 3)

    # 计算总分
    total_score = sum(scores.values())

    # 确定等级
    if total_score >= 80:
        grade = 'A'
    elif total_score >= 60:
        grade = 'B'
    elif total_score >= 40:
        grade = 'C'
    else:
        grade = 'D'

    # 计算风险预警指标
    risk_indicators = calculate_risk_indicators(data, scores, total_score)

    return total_score, grade, scores, risk_indicators


# 1. 模拟训练数据生成（实际可替换为真实历史评分/违约数据）
def generate_training_data(n_samples=10000):
    """生成企业信用评分训练数据（含特征+标签：是否违约）"""
    np.random.seed(42)
    # 特征：与规则化模型15个维度对齐
    data = {
        'industry': np.random.choice(['finance', 'technology', 'manufacturing', 'retail', 'construction', 'other'],
                                     n_samples),
        'debt_ratio': np.random.uniform(0, 100, n_samples),
        'cash_flow': np.random.choice(['excellent', 'good', 'normal', 'poor'], n_samples),
        'litigation_count': np.random.poisson(lam=1, size=n_samples),
        'company_years': np.random.randint(1, 15, n_samples),
        'registered_capital_range': np.random.choice(['above_5000', '1000_5000', '500_1000', '100_500', 'below_100'],
                                                     n_samples),
        'annual_revenue': np.random.choice(['above_1y', '5000w_1y', '1000w_5000w', '500w_1000w', 'below_500w'],
                                           n_samples),
        'profit_rate': np.random.choice(['above_20', '10_20', '5_10', '0_5', 'negative'], n_samples),
        'asset_structure': np.random.choice(['excellent', 'good', 'normal', 'poor'], n_samples),
        'bank_credit_record': np.random.choice(['excellent', 'good', 'normal', 'poor', 'none'], n_samples),
        'tax_credit_level': np.random.choice(['A', 'B', 'C', 'D', 'M'], n_samples),
        'social_security': np.random.choice(['full', 'partial', 'irregular', 'none'], n_samples),
        'supply_chain': np.random.choice(['very_stable', 'stable', 'normal', 'unstable'], n_samples),
        'market_position': np.random.choice(['leader', 'strong', 'normal', 'weak'], n_samples),
        'management_team': np.random.choice(['excellent', 'experienced', 'normal', 'inexperienced'], n_samples),
    }
    df = pd.DataFrame(data)

    # 标签：是否违约（1=违约，0=正常）——基于规则化评分反向生成（模拟真实业务标签）
    df['rule_score'] = df.apply(lambda x: sum(calculate_credit_score(x)[2].values()), axis=1)
    df['label'] = (df['rule_score'] < 50).astype(int)  # 规则分<50视为违约
    return df


# 2. 模型训练函数
def train_credit_model(force_retrain=False):
    """训练逻辑回归评分模型（首次训练/强制重训）"""
    # 若模型已存在且不强制重训，直接返回
    if os.path.exists(MODEL_PATH) and not force_retrain:
        return

    # 生成训练数据
    df = generate_training_data()

    # 特征工程：分类特征编码 + 数值特征标准化
    # 分类特征列表
    cat_features = ['industry', 'cash_flow', 'registered_capital_range', 'annual_revenue',
                    'profit_rate', 'asset_structure', 'bank_credit_record', 'tax_credit_level',
                    'social_security', 'supply_chain', 'market_position', 'management_team']
    # 数值特征列表
    num_features = ['debt_ratio', 'litigation_count', 'company_years']

    # 标签编码器（保存用于推理）
    encoders = {}
    for feat in cat_features:
        le = LabelEncoder()
        df[feat] = le.fit_transform(df[feat])
        encoders[feat] = le

    # 数值特征标准化（保存用于推理）
    scaler = StandardScaler()
    df[num_features] = scaler.fit_transform(df[num_features])

    # 划分训练集/测试集
    X = df.drop(['rule_score', 'label'], axis=1)
    y = df['label']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 训练逻辑回归模型（金融风控首选，可解释性强）
    model = LogisticRegression(class_weight='balanced', random_state=42)
    model.fit(X_train, y_train)

    # 模型评估
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    print(f"模型准确率：{accuracy_score(y_test, y_pred):.4f}")
    print(f"模型AUC：{roc_auc_score(y_test, y_prob):.4f}")
    print("分类报告：\n", classification_report(y_test, y_pred))

    # 保存模型/编码器/标准化器
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    joblib.dump(encoders, ENCODER_PATH)


# 3. 机器学习评分推理函数
def calculate_ml_credit_score(data):
    """基于机器学习模型的信用评分（输出：评分、等级、风险、特征权重）"""
    # 首次运行自动训练模型
    train_credit_model()

    # 加载模型/编码器/标准化器
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    encoders = joblib.load(ENCODER_PATH)

    # 构造特征DataFrame（与训练数据格式对齐）
    feat_df = pd.DataFrame([data])

    # 特征预处理（与训练时一致）
    cat_features = ['industry', 'cash_flow', 'registered_capital_range', 'annual_revenue',
                    'profit_rate', 'asset_structure', 'bank_credit_record', 'tax_credit_level',
                    'social_security', 'supply_chain', 'market_position', 'management_team']
    num_features = ['debt_ratio', 'litigation_count', 'company_years']

    # 分类特征编码（处理未知类别）
    for feat in cat_features:
        le = encoders[feat]
        # 未知类别映射为-1
        feat_df[feat] = feat_df[feat].apply(lambda x: le.transform([x])[0] if x in le.classes_ else -1)

    # 数值特征标准化（处理异常值）
    for feat in num_features:
        try:
            feat_df[feat] = float(feat_df[feat].iloc[0])
        except (ValueError, TypeError):
            feat_df[feat] = 0.0
    feat_df[num_features] = scaler.transform(feat_df[num_features])

    # 模型推理：违约概率
    default_prob = model.predict_proba(feat_df)[0][1]
    # 转换为0-100分（反向映射：违约概率越低，评分越高）
    ml_score = int((1 - default_prob) * 100)

    # 等级划分（与规则化模型对齐）
    if ml_score >= 80:
        ml_grade = 'A'
    elif ml_score >= 60:
        ml_grade = 'B'
    elif ml_score >= 40:
        ml_grade = 'C'
    else:
        ml_grade = 'D'

    # 风险指标（基于机器学习评分）
    ml_risk = {
        'overall_risk': 'low' if ml_score >= 70 else ('medium' if ml_score >= 50 else 'high'),
        'default_probability': f"{default_prob:.4f}"  # 新增：违约概率（机器学习特有）
    }

    # 特征重要性（可解释性）
    feat_importance = dict(zip(model.feature_names_in_, model.coef_[0]))

    return ml_score, ml_grade, ml_risk, feat_importance


# ==================== 改造原有评分接口：支持双模型对比 ====================
@app.route('/enterprise/credit_assessment', methods=['GET', 'POST'])
@login_required
@role_required('enterprise')
def credit_assessment():
    if request.method == 'POST':
        # 获取表单数据
        data = {
            'industry': request.form.get('industry'),
            'debt_ratio': request.form.get('debt_ratio'),
            'cash_flow': request.form.get('cash_flow'),
            'litigation_count': request.form.get('litigation_count'),
            'company_years': request.form.get('company_years'),
            'registered_capital_range': request.form.get('registered_capital_range'),
            'annual_revenue': request.form.get('annual_revenue'),
            'profit_rate': request.form.get('profit_rate'),
            'asset_structure': request.form.get('asset_structure'),
            'bank_credit_record': request.form.get('bank_credit_record'),
            'tax_credit_level': request.form.get('tax_credit_level'),
            'social_security': request.form.get('social_security'),
            'supply_chain': request.form.get('supply_chain'),
            'market_position': request.form.get('market_position'),
            'management_team': request.form.get('management_team'),
        }

        # 1. 原有规则化评分
        rule_score, rule_grade, rule_scores, rule_risk = calculate_credit_score(data)

        # 2. 新增机器学习评分
        ml_score, ml_grade, ml_risk, feat_importance = calculate_ml_credit_score(data)

        # 保存评分结果到数据库
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM enterprise WHERE user_id=%s", (session['user_id'],))
        ent_id = cursor.fetchone()['id']
        # 保存规则化评分
        cursor.execute(
            "INSERT INTO credit_assessment (enterprise_id, score_type, score, grade, risk_indicators, assess_time) VALUES (%s, 'rule', %s, %s, %s, NOW())",
            (ent_id, rule_score, rule_grade, json.dumps(rule_risk))
        )
        # 保存机器学习评分
        cursor.execute(
            "INSERT INTO credit_assessment (enterprise_id, score_type, score, grade, risk_indicators, assess_time) VALUES (%s, 'ml', %s, %s, %s, NOW())",
            (ent_id, ml_score, ml_grade, json.dumps(ml_risk))
        )
        db.commit()
        db.close()

        # 传递双模型结果到前端
        return render_template('enterprise/credit_result.html',
                               rule_score=rule_score, rule_grade=rule_grade, rule_risk=rule_risk,
                               ml_score=ml_score, ml_grade=ml_grade, ml_risk=ml_risk,
                               feat_importance=feat_importance)
    return render_template('enterprise/credit_assessment.html')

# 风险预警指标计算
def calculate_risk_indicators(data, scores, total_score):
    indicators = {
        'overall_risk': 'low' if total_score >= 70 else ('medium' if total_score >= 50 else 'high'),
        'financial_risk': 'low' if scores.get('debt', 0) + scores.get('cashflow', 0) + scores.get('profit',
                                                                                                  0) >= 15 else (
            'medium' if scores.get('debt', 0) + scores.get('cashflow', 0) + scores.get('profit', 0) >= 10 else 'high'),
        'legal_risk': 'low' if scores.get('litigation', 0) >= 5 else (
            'medium' if scores.get('litigation', 0) >= 2 else 'high'),
        'operational_risk': 'low' if scores.get('supply_chain', 0) + scores.get('market_position', 0) >= 8 else (
            'medium' if scores.get('supply_chain', 0) + scores.get('market_position', 0) >= 5 else 'high'),
        'credit_risk': 'low' if scores.get('bank_credit', 0) + scores.get('tax_credit', 0) >= 10 else (
            'medium' if scores.get('bank_credit', 0) + scores.get('tax_credit', 0) >= 6 else 'high'),
    }
    return indicators


# AI咨询回答函数 - 使用火山引擎API
def get_ai_response(question):
    # 业务关键词过滤
    business_keywords = ['信用', '评估', '贷款', '还款', '征信', '上传', '营业执照', '企业信息', '存款', '取款', '账户',
                         '利率', '审核', '评分', '银行', '企业', '资金', '申请', '审批']
    is_business = any(kw in question for kw in business_keywords)
    if not is_business:
        return "抱歉，我只能回答与信用评估、贷款、企业信息等业务相关的问题。请问您有什么业务方面的疑问？"

    try:
        # 火山引擎API配置
        api_key = "34eb5f5a-bee1-488f-a9b2-e31d7420fd77"
        model = "ep-20250126163455-8xrmx"
        api_url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        # 构建请求体
        data = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是银行对公信用评估业务系统的智能客服助手。你专门负责解答企业客户关于信用评估、贷款申请、还款、征信查询、企业信息管理、账户存取款等业务问题。请用专业、友好的语气回答问题。"
                },
                {
                    "role": "user",
                    "content": question + ",简略回答，一定不超过100字"
                }
            ]
        }

        # 发送请求
        response = requests.post(api_url, headers=headers, json=data, timeout=30)

        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            else:
                return "抱歉，暂时无法获取回答，请稍后再试。"
        else:
            # API调用失败时使用本地回答
            return get_local_response(question)
    except Exception as e:
        # 异常时使用本地回答
        print(f"AI API调用异常: {e}")
        return get_local_response(question)


# 本地备用回答函数
def get_local_response(question):
    qa = {
        '信用评估': '信用评估根据企业的行业类型、负债率、现金流状况、诉讼记录等因素，通过评分卡模型计算0-100分的信用评分，并给出A/B/C/D等级。',
        '贷款': '企业可在贷款还款模块查看当前贷款状态、还款进度。贷款审批需要银行员工根据信用评估结果进行。',
        '还款': '还款可通过贷款还款模块进行，系统会自动计算本金和利息。建议按时还款以维护良好的信用记录。',
        '征信': '征信信息可通过征信查询模块跳转至全国法院信息综合查询等外部平台查询。',
        '上传': '企业可在企业信息管理模块上传营业执照等资料，上传后需等待管理员审核通过。',
        '营业执照': '营业执照上传后会进入审核流程，审核通过后企业信息才会更新。请确保上传的图片清晰可辨。',
        '账户': '虚拟对公账户用于模拟企业资金变动，支持存入和支取操作，所有交易都会记录在流水明细中。',
        '利率': '贷款利率根据企业信用等级确定，A级企业可享受基准利率，其他等级会有相应上浮。'
    }
    for kw, ans in qa.items():
        if kw in question: return ans
    return "感谢您的提问。关于这个问题，建议您联系银行客服获取更详细的解答，或查看相关功能模块的帮助说明。"


# ==================== 认证路由 ====================
@app.route('/')
def index():
    if 'username' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif role == 'employee':
            return redirect(url_for('employee_dashboard'))
        else:
            return redirect(url_for('enterprise_dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM user WHERE username=%s AND password=%s AND status=1", (username, password))
        user = cursor.fetchone()
        db.close()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['name'] = user['name']
            session['role'] = user['role']
            flash('登录成功')
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'employee':
                return redirect(url_for('employee_dashboard'))
            else:
                return redirect(url_for('enterprise_dashboard'))
        else:
            flash('用户名或密码错误')
    return render_template('auth/login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM user WHERE username=%s", (username,))
        if cursor.fetchone():
            flash('用户名已存在')
            db.close()
            return render_template('auth/register.html')
        cursor.execute(
            "INSERT INTO user (username, password, name, role, phone, email, status, create_time, update_time) VALUES (%s, %s, %s, 'enterprise', %s, %s, 1, NOW(), NOW())",
            (username, password, name, phone, email))
        user_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO enterprise (user_id, company_name, create_time, update_time) VALUES (%s, %s, NOW(), NOW())",
            (user_id, name))
        enterprise_id = cursor.lastrowid
        account_no = f"6222{str(enterprise_id).zfill(12)}"
        cursor.execute(
            "INSERT INTO account (enterprise_id, account_no, balance, create_time, update_time) VALUES (%s, %s, 0, NOW(), NOW())",
            (enterprise_id, account_no))
        db.commit()
        db.close()
        flash('注册成功，请登录')
        return redirect(url_for('login'))
    return render_template('auth/register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('已退出登录')
    return redirect(url_for('login'))


# ==================== 企业端路由 ====================
@app.route('/enterprise/dashboard')
@login_required
@role_required('enterprise')
def enterprise_dashboard():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM enterprise WHERE user_id=%s", (session['user_id'],))
    ent = cursor.fetchone()
    if not ent:
        db.close()
        flash('企业信息不存在')
        return redirect(url_for('logout'))
    ent_id = ent['id']
    cursor.execute("SELECT balance FROM account WHERE enterprise_id=%s", (ent_id,))
    account = cursor.fetchone()
    balance = account['balance'] if account else 0
    cursor.execute(
        "SELECT COUNT(*) as cnt, SUM(remaining_amount) as total FROM loan WHERE enterprise_id=%s AND status='repaying'",
        (ent_id,))
    loan_info = cursor.fetchone()
    cursor.execute(
        "SELECT score, grade FROM credit_assessment WHERE enterprise_id=%s ORDER BY assess_time DESC LIMIT 1",
        (ent_id,))
    credit = cursor.fetchone()
    db.close()
    return render_template('enterprise/dashboard.html', balance=balance, loan_count=loan_info['cnt'] or 0,
                           loan_total=loan_info['total'] or 0, credit=credit)


@app.route('/enterprise/account', methods=['GET', 'POST'])
@login_required
@role_required('enterprise')
def enterprise_account():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM enterprise WHERE user_id=%s", (session['user_id'],))
    ent = cursor.fetchone()
    ent_id = ent['id']
    cursor.execute("SELECT * FROM account WHERE enterprise_id=%s", (ent_id,))
    account = cursor.fetchone()
    if request.method == 'POST':
        action = request.form.get('action')
        try:
            amount = Decimal(request.form.get('amount', 0))  # 修改：使用Decimal
        except (ValueError, TypeError):
            flash('金额格式错误，请输入数字')
            db.close()
            return redirect(url_for('enterprise_account'))

        if amount <= 0:
            flash('金额必须大于0')
        elif action == 'withdraw' and amount > Decimal(str(account['balance'])):  # 修改：类型统一
            flash('余额不足')
        else:
            # 修改：使用Decimal计算，保证精度
            current_balance = Decimal(str(account['balance']))
            new_balance = current_balance + amount if action == 'deposit' else current_balance - amount
            # 保留两位小数（金融计算标准）
            new_balance = new_balance.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)

            cursor.execute("UPDATE account SET balance=%s, update_time=NOW() WHERE id=%s",
                           (float(new_balance), account['id']))
            trans_type = 'deposit' if action == 'deposit' else 'withdraw'
            cursor.execute(
                "INSERT INTO transaction (account_id, enterprise_id, trans_type, amount, balance_after, remark, create_time) VALUES (%s, %s, %s, %s, %s, %s, NOW())",
                (account['id'], ent_id, trans_type, float(amount), float(new_balance), request.form.get('remark', '')))
            db.commit()
            flash('存入成功' if action == 'deposit' else '支取成功')
            cursor.execute("SELECT * FROM account WHERE enterprise_id=%s", (ent_id,))
            account = cursor.fetchone()
    cursor.execute("SELECT * FROM transaction WHERE enterprise_id=%s ORDER BY create_time DESC LIMIT 50", (ent_id,))
    transactions = cursor.fetchall()
    db.close()
    return render_template('enterprise/account.html', account=account, transactions=transactions)


@app.route('/enterprise/loan', methods=['GET', 'POST'])
@login_required
@role_required('enterprise')
def enterprise_loan():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM enterprise WHERE user_id=%s", (session['user_id'],))
    ent = cursor.fetchone()
    ent_id = ent['id']
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'apply':
            try:
                amount = Decimal(request.form.get('loan_amount', 0))  # 修改：使用Decimal
                term = int(request.form.get('loan_term', 12))
                if amount <= 0:
                    flash('贷款金额必须大于0')
                else:
                    loan_no = f"LN{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    # 修改：存入数据库时转成float（兼容数据库字段类型）
                    cursor.execute(
                        "INSERT INTO loan (enterprise_id, loan_no, loan_amount, interest_rate, loan_term, remaining_amount, status, apply_time, create_time) VALUES (%s, %s, %s, 4.35, %s, %s, 'pending', NOW(), NOW())",
                        (ent_id, loan_no, float(amount), term, float(amount)))
                    db.commit()
                    flash('贷款申请已提交')
            except (ValueError, TypeError):
                flash('贷款金额格式错误，请输入数字')
        elif action == 'repay':
            loan_id = request.form.get('loan_id')
            try:
                repay_amount = Decimal(request.form.get('repay_amount', 0))  # 修改：使用Decimal
                if repay_amount <= 0:
                    flash('还款金额必须大于0')
                    db.close()
                    return redirect(url_for('enterprise_loan'))
            except (ValueError, TypeError):
                flash('还款金额格式错误，请输入数字')
                db.close()
                return redirect(url_for('enterprise_loan'))

            cursor.execute("SELECT * FROM loan WHERE id=%s AND enterprise_id=%s", (loan_id, ent_id))
            loan = cursor.fetchone()
            if loan:
                # 修改：统一使用Decimal进行金融计算
                remaining_amount = Decimal(str(loan['remaining_amount']))
                interest_rate = Decimal('0.1')  # 10%利率
                interest = (repay_amount * interest_rate).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
                principal = (repay_amount - interest).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)

                # 核心修改：解决Decimal和float相减问题
                new_remaining = max(Decimal('0'), remaining_amount - principal)
                new_status = 'completed' if new_remaining == Decimal('0') else 'repaying'

                # 转回float存入数据库（兼容原有字段类型）
                cursor.execute("UPDATE loan SET remaining_amount=%s, status=%s WHERE id=%s",
                               (float(new_remaining), new_status, loan_id))
                cursor.execute(
                    "INSERT INTO repayment (loan_id, enterprise_id, repay_amount, principal, interest, repay_date, status, actual_repay_time, create_time) VALUES (%s, %s, %s, %s, %s, CURDATE(), 'paid', NOW(), NOW())",
                    (loan_id, ent_id, float(repay_amount), float(principal), float(interest)))
                db.commit()
                flash('还款成功')
    cursor.execute("SELECT * FROM loan WHERE enterprise_id=%s ORDER BY create_time DESC", (ent_id,))
    loans = cursor.fetchall()
    cursor.execute("SELECT * FROM repayment WHERE enterprise_id=%s ORDER BY create_time DESC LIMIT 20", (ent_id,))
    repayments = cursor.fetchall()
    db.close()
    return render_template('enterprise/loan.html', loans=loans, repayments=repayments)


@app.route('/enterprise/company_info', methods=['GET', 'POST'])
@login_required
@role_required('enterprise')
def enterprise_company_info():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM enterprise WHERE user_id=%s", (session['user_id'],))
    enterprise = cursor.fetchone()
    if request.method == 'POST':
        company_name = request.form.get('company_name')
        credit_code = request.form.get('credit_code')
        legal_person = request.form.get('legal_person')
        registered_capital = request.form.get('registered_capital')
        industry = request.form.get('industry')
        address = request.form.get('address')
        if credit_code and len(credit_code) != 18:
            flash('统一社会信用代码必须为18位')
        else:
            cursor.execute(
                "UPDATE enterprise SET company_name=%s, credit_code=%s, legal_person=%s, registered_capital=%s, industry=%s, address=%s, update_time=NOW() WHERE user_id=%s",
                (company_name, credit_code, legal_person, registered_capital, industry, address, session['user_id']))
            if 'business_license' in request.files:
                file = request.files['business_license']
                if file and file.filename:
                    filename = f"license_{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    cursor.execute("UPDATE enterprise SET business_license=%s, license_status=0 WHERE user_id=%s",
                                   (filename, session['user_id']))
                    cursor.execute(
                        "INSERT INTO content_review (enterprise_id, content_type, content_path, status, create_time) VALUES (%s, 'license', %s, 0, NOW())",
                        (enterprise['id'], filename))
            db.commit()
            flash('企业信息更新成功')
            cursor.execute("SELECT * FROM enterprise WHERE user_id=%s", (session['user_id'],))
            enterprise = cursor.fetchone()
    db.close()
    return render_template('enterprise/company_info.html', enterprise=enterprise)


@app.route('/enterprise/credit_query')
@login_required
@role_required('enterprise')
def enterprise_credit_query():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM external_link WHERE status=1 ORDER BY id")
    links = cursor.fetchall()
    db.close()
    return render_template('enterprise/credit_query.html', links=links)


@app.route('/enterprise/credit_visual')
@login_required
@role_required('enterprise')
def enterprise_credit_visual():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM enterprise WHERE user_id=%s", (session['user_id'],))
    ent = cursor.fetchone()
    ent_id = ent['id']
    cursor.execute("SELECT * FROM credit_assessment WHERE enterprise_id=%s ORDER BY assess_time DESC LIMIT 1",
                   (ent_id,))
    latest = cursor.fetchone()
    cursor.execute(
        "SELECT score, assess_time FROM credit_assessment WHERE enterprise_id=%s ORDER BY assess_time DESC LIMIT 12",
        (ent_id,))
    history = cursor.fetchall()
    cursor.execute("SELECT grade, COUNT(*) as cnt FROM credit_assessment GROUP BY grade")
    grade_dist = cursor.fetchall()
    cursor.execute("SELECT AVG(score) as avg_score FROM credit_assessment")
    avg = cursor.fetchone()
    # 获取风险预警数据
    cursor.execute(
        "SELECT questionnaire_data FROM credit_assessment WHERE enterprise_id=%s ORDER BY assess_time DESC LIMIT 1",
        (ent_id,))
    latest_data = cursor.fetchone()
    risk_indicators = None
    if latest_data and latest_data.get('questionnaire_data'):
        try:
            data = json.loads(latest_data['questionnaire_data']) if isinstance(latest_data['questionnaire_data'],
                                                                               str) else latest_data[
                'questionnaire_data']
            _, _, scores, risk_indicators = calculate_credit_score(data)
        except:
            risk_indicators = None
    db.close()
    return render_template('enterprise/credit_visual.html', latest=latest, history=list(reversed(history)),
                           grade_dist=grade_dist, avg_score=avg['avg_score'] or 0, risk_indicators=risk_indicators)


# 企业端风险预警路由
@app.route('/enterprise/risk_warning')
@login_required
@role_required('enterprise')
def enterprise_risk_warning():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM enterprise WHERE user_id=%s", (session['user_id'],))
    ent = cursor.fetchone()
    ent_id = ent['id']

    # 获取最新评估数据
    cursor.execute("SELECT * FROM credit_assessment WHERE enterprise_id=%s ORDER BY assess_time DESC LIMIT 1",
                   (ent_id,))
    latest = cursor.fetchone()

    # 获取历史评估趋势
    cursor.execute(
        "SELECT score, grade, assess_time FROM credit_assessment WHERE enterprise_id=%s ORDER BY assess_time DESC LIMIT 12",
        (ent_id,))
    history = cursor.fetchall()

    # 获取贷款风险数据
    cursor.execute(
        "SELECT COUNT(*) as total, SUM(CASE WHEN status='repaying' THEN remaining_amount ELSE 0 END) as debt FROM loan WHERE enterprise_id=%s",
        (ent_id,))
    loan_risk = cursor.fetchone()

    # 获取交易波动数据
    cursor.execute(
        "SELECT DATE(create_time) as date, SUM(CASE WHEN trans_type='deposit' THEN amount ELSE -amount END) as net_flow FROM transaction WHERE enterprise_id=%s AND create_time >= DATE_SUB(NOW(), INTERVAL 30 DAY) GROUP BY DATE(create_time) ORDER BY date",
        (ent_id,))
    cash_flow = cursor.fetchall()

    # 计算风险指标
    risk_indicators = None
    if latest and latest.get('questionnaire_data'):
        try:
            data = json.loads(latest['questionnaire_data']) if isinstance(latest['questionnaire_data'], str) else \
            latest['questionnaire_data']
            _, _, scores, risk_indicators = calculate_credit_score(data)
        except:
            risk_indicators = {'overall_risk': 'medium', 'financial_risk': 'medium', 'legal_risk': 'low',
                               'operational_risk': 'medium', 'credit_risk': 'medium'}

    db.close()
    return render_template('enterprise/risk_warning.html', latest=latest, history=list(reversed(history)),
                           loan_risk=loan_risk, cash_flow=cash_flow, risk_indicators=risk_indicators)


@app.route('/enterprise/assessment', methods=['GET', 'POST'])
@login_required
@role_required('enterprise')
def enterprise_assessment():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM enterprise WHERE user_id=%s", (session['user_id'],))
    enterprise = cursor.fetchone()
    result = None
    risk_indicators = None
    if request.method == 'POST':
        data = {
            'industry': request.form.get('industry'),
            'debt_ratio': request.form.get('debt_ratio'),
            'cash_flow': request.form.get('cash_flow'),
            'litigation_count': request.form.get('litigation_count'),
            'company_years': request.form.get('company_years'),
            'registered_capital_range': request.form.get('registered_capital_range'),
            'annual_revenue': request.form.get('annual_revenue'),
            'profit_rate': request.form.get('profit_rate'),
            'asset_structure': request.form.get('asset_structure'),
            'bank_credit_record': request.form.get('bank_credit_record'),
            'tax_credit_level': request.form.get('tax_credit_level'),
            'social_security': request.form.get('social_security'),
            'supply_chain': request.form.get('supply_chain'),
            'market_position': request.form.get('market_position'),
            'management_team': request.form.get('management_team')
        }
        score, grade, scores, risk_indicators = calculate_credit_score(data)
        cursor.execute(
            "INSERT INTO credit_assessment (enterprise_id, score, grade, industry_score, debt_score, cashflow_score, litigation_score, questionnaire_data, assess_time, create_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())",
            (
            enterprise['id'], score, grade, scores.get('industry', 0), scores.get('debt', 0), scores.get('cashflow', 0),
            scores.get('litigation', 0), json.dumps(data)))
        db.commit()
        result = {'score': score, 'grade': grade, 'scores': scores, 'risk_indicators': risk_indicators}
        flash(f'评估完成！您的信用评分为{score}分，等级为{grade}')
    cursor.execute("SELECT * FROM credit_assessment WHERE enterprise_id=%s ORDER BY assess_time DESC LIMIT 5",
                   (enterprise['id'],))
    assessments = cursor.fetchall()
    db.close()
    return render_template('enterprise/assessment.html', enterprise=enterprise, result=result, assessments=assessments)


@app.route('/api/ai_consult', methods=['POST'])
@login_required
def api_ai_consult():
    question = request.json.get('question', '')
    answer = get_ai_response(question)
    if session.get('role') == 'enterprise':
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM enterprise WHERE user_id=%s", (session['user_id'],))
        ent = cursor.fetchone()
        if ent:
            cursor.execute(
                "INSERT INTO ai_consultation (enterprise_id, question, answer, create_time) VALUES (%s, %s, %s, NOW())",
                (ent['id'], question, answer))
            db.commit()
        db.close()
    return jsonify({'answer': answer})


# ==================== 银行员工端路由 ====================
@app.route('/employee/dashboard')
@login_required
@role_required('employee')
def employee_dashboard():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM enterprise")
    ent_count = cursor.fetchone()['cnt']
    cursor.execute("SELECT COUNT(*) as cnt FROM loan WHERE status='pending'")
    pending_loans = cursor.fetchone()['cnt']
    cursor.execute("SELECT COUNT(*) as cnt FROM loan WHERE status='repaying'")
    active_loans = cursor.fetchone()['cnt']
    cursor.execute("SELECT SUM(loan_amount) as total FROM loan WHERE status IN ('repaying', 'completed')")
    total_loan = cursor.fetchone()['total'] or 0
    cursor.execute(
        "SELECT grade, COUNT(*) as cnt FROM credit_assessment ca INNER JOIN (SELECT enterprise_id, MAX(assess_time) as max_time FROM credit_assessment GROUP BY enterprise_id) latest ON ca.enterprise_id=latest.enterprise_id AND ca.assess_time=latest.max_time GROUP BY grade")
    grade_stats = cursor.fetchall()
    db.close()
    return render_template('employee/dashboard.html', ent_count=ent_count, pending_loans=pending_loans,
                           active_loans=active_loans, total_loan=total_loan, grade_stats=grade_stats)


@app.route('/employee/enterprise_list')
@login_required
@role_required('employee')
def employee_enterprise_list():
    db = get_db()
    cursor = db.cursor()
    search = request.args.get('search', '')
    if search:
        cursor.execute(
            "SELECT e.*, u.phone, u.email FROM enterprise e LEFT JOIN user u ON e.user_id=u.id WHERE e.company_name LIKE %s OR e.credit_code LIKE %s",
            (f'%{search}%', f'%{search}%'))
    else:
        cursor.execute("SELECT e.*, u.phone, u.email FROM enterprise e LEFT JOIN user u ON e.user_id=u.id")
    enterprises = cursor.fetchall()
    db.close()
    return render_template('employee/enterprise_list.html', enterprises=enterprises, search=search)


@app.route('/employee/credit_records')
@login_required
@role_required('employee')
def employee_credit_records():
    db = get_db()
    cursor = db.cursor()
    ent_id = request.args.get('enterprise_id', '')
    if ent_id:
        cursor.execute(
            "SELECT ch.*, e.company_name FROM credit_history ch LEFT JOIN enterprise e ON ch.enterprise_id=e.id WHERE ch.enterprise_id=%s ORDER BY ch.record_date DESC",
            (ent_id,))
    else:
        cursor.execute(
            "SELECT ch.*, e.company_name FROM credit_history ch LEFT JOIN enterprise e ON ch.enterprise_id=e.id ORDER BY ch.record_date DESC LIMIT 100")
    records = cursor.fetchall()
    cursor.execute("SELECT id, company_name FROM enterprise")
    enterprises = cursor.fetchall()
    db.close()
    return render_template('employee/credit_records.html', records=records, enterprises=enterprises,
                           selected_ent=ent_id)


@app.route('/employee/assessment_results')
@login_required
@role_required('employee')
def employee_assessment_results():
    db = get_db()
    cursor = db.cursor()
    grade = request.args.get('grade', '')
    if grade:
        cursor.execute(
            "SELECT ca.*, e.company_name FROM credit_assessment ca LEFT JOIN enterprise e ON ca.enterprise_id=e.id WHERE ca.grade=%s ORDER BY ca.assess_time DESC",
            (grade,))
    else:
        cursor.execute(
            "SELECT ca.*, e.company_name FROM credit_assessment ca LEFT JOIN enterprise e ON ca.enterprise_id=e.id ORDER BY ca.assess_time DESC LIMIT 100")
    assessments = cursor.fetchall()
    db.close()
    return render_template('employee/assessment_results.html', assessments=assessments, selected_grade=grade)


@app.route('/employee/loan_manage', methods=['GET', 'POST'])
@login_required
@role_required('employee')
def employee_loan_manage():
    db = get_db()
    cursor = db.cursor()
    if request.method == 'POST':
        loan_id = request.form.get('loan_id')
        action = request.form.get('action')
        if action == 'approve':
            cursor.execute("UPDATE loan SET status='repaying', approve_time=NOW() WHERE id=%s", (loan_id,))
            flash('贷款已批准')
        elif action == 'reject':
            cursor.execute("UPDATE loan SET status='rejected', approve_time=NOW() WHERE id=%s", (loan_id,))
            flash('贷款已拒绝')
        db.commit()
    status = request.args.get('status', '')
    if status:
        cursor.execute(
            "SELECT l.*, e.company_name FROM loan l LEFT JOIN enterprise e ON l.enterprise_id=e.id WHERE l.status=%s ORDER BY l.apply_time DESC",
            (status,))
    else:
        cursor.execute(
            "SELECT l.*, e.company_name FROM loan l LEFT JOIN enterprise e ON l.enterprise_id=e.id ORDER BY l.apply_time DESC")
    loans = cursor.fetchall()
    db.close()
    return render_template('employee/loan_manage.html', loans=loans, selected_status=status)


@app.route('/employee/transaction_records')
@login_required
@role_required('employee')
def employee_transaction_records():
    db = get_db()
    cursor = db.cursor()
    ent_id = request.args.get('enterprise_id', '')
    if ent_id:
        cursor.execute(
            "SELECT t.*, e.company_name FROM transaction t LEFT JOIN enterprise e ON t.enterprise_id=e.id WHERE t.enterprise_id=%s ORDER BY t.create_time DESC",
            (ent_id,))
    else:
        cursor.execute(
            "SELECT t.*, e.company_name FROM transaction t LEFT JOIN enterprise e ON t.enterprise_id=e.id ORDER BY t.create_time DESC LIMIT 100")
    transactions = cursor.fetchall()
    cursor.execute("SELECT id, company_name FROM enterprise")
    enterprises = cursor.fetchall()
    db.close()
    return render_template('employee/transaction_records.html', transactions=transactions, enterprises=enterprises,
                           selected_ent=ent_id)


# 员工端风险预警路由
@app.route('/employee/risk_warning')
@login_required
@role_required('employee')
def employee_risk_warning():
    db = get_db()
    cursor = db.cursor()

    # 获取高风险企业列表
    cursor.execute("""
        SELECT e.id, e.company_name, ca.score, ca.grade, ca.assess_time,
               (SELECT SUM(remaining_amount) FROM loan WHERE enterprise_id=e.id AND status='repaying') as total_debt
        FROM enterprise e
        LEFT JOIN credit_assessment ca ON e.id = ca.enterprise_id
        WHERE ca.id = (SELECT MAX(id) FROM credit_assessment WHERE enterprise_id = e.id)
        ORDER BY ca.score ASC
        LIMIT 20
    """)
    risk_enterprises = cursor.fetchall()

    # 获取各等级企业数量
    cursor.execute("""
        SELECT ca.grade, COUNT(DISTINCT e.id) as cnt
        FROM enterprise e
        LEFT JOIN credit_assessment ca ON e.id = ca.enterprise_id
        WHERE ca.id = (SELECT MAX(id) FROM credit_assessment WHERE enterprise_id = e.id)
        GROUP BY ca.grade
    """)
    grade_distribution = cursor.fetchall()

    # 获取贷款风险统计
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN status='pending' THEN 1 END) as pending_count,
            COUNT(CASE WHEN status='repaying' THEN 1 END) as repaying_count,
            SUM(CASE WHEN status='repaying' THEN remaining_amount ELSE 0 END) as total_debt,
            SUM(loan_amount) as total_loan
        FROM loan
    """)
    loan_stats = cursor.fetchone()

    # 获取最近30天评估趋势
    cursor.execute("""
        SELECT DATE(assess_time) as date, AVG(score) as avg_score, COUNT(*) as count
        FROM credit_assessment
        WHERE assess_time >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY DATE(assess_time)
        ORDER BY date
    """)
    assessment_trend = cursor.fetchall()

    # 获取风险预警企业（评分低于50分）
    cursor.execute("""
        SELECT e.company_name, ca.score, ca.grade, ca.assess_time
        FROM enterprise e
        JOIN credit_assessment ca ON e.id = ca.enterprise_id
        WHERE ca.id = (SELECT MAX(id) FROM credit_assessment WHERE enterprise_id = e.id)
        AND ca.score < 50
        ORDER BY ca.score ASC
    """)
    warning_enterprises = cursor.fetchall()

    db.close()
    return render_template('employee/risk_warning.html',
                           risk_enterprises=risk_enterprises,
                           grade_distribution=grade_distribution,
                           loan_stats=loan_stats,
                           assessment_trend=assessment_trend,
                           warning_enterprises=warning_enterprises)


# ==================== 管理员端路由 ====================
@app.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM user WHERE role='enterprise'")
    ent_users = cursor.fetchone()['cnt']
    cursor.execute("SELECT COUNT(*) as cnt FROM user WHERE role='employee'")
    emp_users = cursor.fetchone()['cnt']
    cursor.execute("SELECT COUNT(*) as cnt FROM content_review WHERE status=0")
    pending_reviews = cursor.fetchone()['cnt']
    cursor.execute("SELECT COUNT(*) as cnt FROM loan")
    total_loans = cursor.fetchone()['cnt']
    cursor.execute("SELECT SUM(balance) as total FROM account")
    total_balance = cursor.fetchone()['total'] or 0
    db.close()
    return render_template('admin/dashboard.html', ent_users=ent_users, emp_users=emp_users,
                           pending_reviews=pending_reviews, total_loans=total_loans, total_balance=total_balance)


@app.route('/admin/user_manage', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_user_manage():
    db = get_db()
    cursor = db.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            cursor.execute(
                "INSERT INTO user (username, password, name, role, phone, email, status, create_time, update_time) VALUES (%s, %s, %s, %s, %s, %s, 1, NOW(), NOW())",
                (request.form.get('username'), request.form.get('password'), request.form.get('name'),
                 request.form.get('role'), request.form.get('phone'), request.form.get('email')))
            flash('用户添加成功')
        elif action == 'edit':
            cursor.execute(
                "UPDATE user SET name=%s, role=%s, phone=%s, email=%s, status=%s, update_time=NOW() WHERE id=%s", (
                request.form.get('name'), request.form.get('role'), request.form.get('phone'),
                request.form.get('email'), request.form.get('status'), request.form.get('user_id')))
            flash('用户更新成功')
        elif action == 'delete':
            cursor.execute("DELETE FROM user WHERE id=%s", (request.form.get('user_id'),))
            flash('用户删除成功')
        db.commit()
    role_filter = request.args.get('role', '')
    if role_filter:
        cursor.execute("SELECT * FROM user WHERE role=%s ORDER BY id DESC", (role_filter,))
    else:
        cursor.execute("SELECT * FROM user ORDER BY id DESC")
    users = cursor.fetchall()
    db.close()
    return render_template('admin/user_manage.html', users=users, selected_role=role_filter)


@app.route('/admin/content_review', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_content_review():
    db = get_db()
    cursor = db.cursor()
    if request.method == 'POST':
        review_id = request.form.get('review_id')
        action = request.form.get('action')
        comment = request.form.get('comment', '')
        status = 1 if action == 'approve' else 2
        cursor.execute(
            "UPDATE content_review SET status=%s, review_comment=%s, reviewer_id=%s, review_time=NOW() WHERE id=%s",
            (status, comment, session['user_id'], review_id))
        cursor.execute("SELECT enterprise_id, content_type FROM content_review WHERE id=%s", (review_id,))
        review = cursor.fetchone()
        if review and review['content_type'] == 'license':
            cursor.execute("UPDATE enterprise SET license_status=%s, review_comment=%s WHERE id=%s",
                           (status, comment, review['enterprise_id']))
        db.commit()
        flash('审核完成')
    status_filter = request.args.get('status', '0')
    cursor.execute(
        "SELECT cr.*, e.company_name FROM content_review cr LEFT JOIN enterprise e ON cr.enterprise_id=e.id WHERE cr.status=%s ORDER BY cr.create_time DESC",
        (status_filter,))
    reviews = cursor.fetchall()
    db.close()
    return render_template('admin/content_review.html', reviews=reviews, selected_status=status_filter)


@app.route('/admin/link_manage', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_link_manage():
    db = get_db()
    cursor = db.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            cursor.execute(
                "INSERT INTO external_link (link_name, link_url, link_type, status, create_time, update_time) VALUES (%s, %s, %s, 1, NOW(), NOW())",
                (request.form.get('link_name'), request.form.get('link_url'), request.form.get('link_type')))
            flash('链接添加成功')
        elif action == 'edit':
            cursor.execute(
                "UPDATE external_link SET link_name=%s, link_url=%s, link_type=%s, status=%s, update_time=NOW() WHERE id=%s",
                (request.form.get('link_name'), request.form.get('link_url'), request.form.get('link_type'),
                 request.form.get('status'), request.form.get('link_id')))
            flash('链接更新成功')
        elif action == 'delete':
            cursor.execute("DELETE FROM external_link WHERE id=%s", (request.form.get('link_id'),))
            flash('链接删除成功')
        db.commit()
    cursor.execute("SELECT * FROM external_link ORDER BY id DESC")
    links = cursor.fetchall()
    db.close()
    return render_template('admin/link_manage.html', links=links)


# ==================== 管理员数据管理路由 ====================
@app.route('/admin/enterprise_data', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_enterprise_data():
    db = get_db()
    cursor = db.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            cursor.execute(
                "INSERT INTO enterprise (user_id, company_name, credit_code, legal_person, registered_capital, industry, address, license_status, create_time, update_time) VALUES (%s, %s, %s, %s, %s, %s, %s, 0, NOW(), NOW())",
                (request.form.get('user_id'), request.form.get('company_name'), request.form.get('credit_code'),
                 request.form.get('legal_person'), request.form.get('registered_capital'), request.form.get('industry'),
                 request.form.get('address')))
            flash('企业添加成功')
        elif action == 'edit':
            cursor.execute(
                "UPDATE enterprise SET company_name=%s, credit_code=%s, legal_person=%s, registered_capital=%s, industry=%s, address=%s, license_status=%s, update_time=NOW() WHERE id=%s",
                (request.form.get('company_name'), request.form.get('credit_code'), request.form.get('legal_person'),
                 request.form.get('registered_capital'), request.form.get('industry'), request.form.get('address'),
                 request.form.get('license_status'), request.form.get('enterprise_id')))
            flash('企业更新成功')
        elif action == 'delete':
            cursor.execute("DELETE FROM enterprise WHERE id=%s", (request.form.get('enterprise_id'),))
            flash('企业删除成功')
        db.commit()
    search = request.args.get('search', '')
    if search:
        cursor.execute("SELECT * FROM enterprise WHERE company_name LIKE %s OR credit_code LIKE %s ORDER BY id DESC",
                       (f'%{search}%', f'%{search}%'))
    else:
        cursor.execute("SELECT * FROM enterprise ORDER BY id DESC")
    enterprises = cursor.fetchall()
    db.close()
    return render_template('admin/enterprise_data.html', enterprises=enterprises, search=search)


@app.route('/admin/transaction_data', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_transaction_data():
    db = get_db()
    cursor = db.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            cursor.execute(
                "INSERT INTO transaction (account_id, enterprise_id, trans_type, amount, balance_after, remark, create_time) VALUES (%s, %s, %s, %s, %s, %s, NOW())",
                (request.form.get('account_id'), request.form.get('enterprise_id'), request.form.get('trans_type'),
                 request.form.get('amount'), request.form.get('balance_after'), request.form.get('remark')))
            flash('交易添加成功')
        elif action == 'edit':
            cursor.execute("UPDATE transaction SET trans_type=%s, amount=%s, balance_after=%s, remark=%s WHERE id=%s", (
            request.form.get('trans_type'), request.form.get('amount'), request.form.get('balance_after'),
            request.form.get('remark'), request.form.get('trans_id')))
            flash('交易更新成功')
        elif action == 'delete':
            cursor.execute("DELETE FROM transaction WHERE id=%s", (request.form.get('trans_id'),))
            flash('交易删除成功')
        db.commit()
    ent_id = request.args.get('enterprise_id', '')
    if ent_id:
        cursor.execute(
            "SELECT t.*, e.company_name FROM transaction t LEFT JOIN enterprise e ON t.enterprise_id=e.id WHERE t.enterprise_id=%s ORDER BY t.create_time DESC",
            (ent_id,))
    else:
        cursor.execute(
            "SELECT t.*, e.company_name FROM transaction t LEFT JOIN enterprise e ON t.enterprise_id=e.id ORDER BY t.create_time DESC LIMIT 200")
    transactions = cursor.fetchall()
    cursor.execute("SELECT id, company_name FROM enterprise")
    enterprises = cursor.fetchall()
    db.close()
    return render_template('admin/transaction_data.html', transactions=transactions, enterprises=enterprises,
                           selected_ent=ent_id)


@app.route('/admin/loan_data', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_loan_data():
    db = get_db()
    cursor = db.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            loan_no = f"LN{datetime.now().strftime('%Y%m%d%H%M%S')}"
            cursor.execute(
                "INSERT INTO loan (enterprise_id, loan_no, loan_amount, interest_rate, loan_term, remaining_amount, status, apply_time, create_time) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())",
                (request.form.get('enterprise_id'), loan_no, request.form.get('loan_amount'),
                 request.form.get('interest_rate'), request.form.get('loan_term'), request.form.get('loan_amount'),
                 request.form.get('status')))
            flash('贷款添加成功')
        elif action == 'edit':
            cursor.execute(
                "UPDATE loan SET loan_amount=%s, interest_rate=%s, loan_term=%s, remaining_amount=%s, status=%s WHERE id=%s",
                (request.form.get('loan_amount'), request.form.get('interest_rate'), request.form.get('loan_term'),
                 request.form.get('remaining_amount'), request.form.get('status'), request.form.get('loan_id')))
            flash('贷款更新成功')
        elif action == 'delete':
            cursor.execute("DELETE FROM loan WHERE id=%s", (request.form.get('loan_id'),))
            flash('贷款删除成功')
        db.commit()
    status = request.args.get('status', '')
    if status:
        cursor.execute(
            "SELECT l.*, e.company_name FROM loan l LEFT JOIN enterprise e ON l.enterprise_id=e.id WHERE l.status=%s ORDER BY l.create_time DESC",
            (status,))
    else:
        cursor.execute(
            "SELECT l.*, e.company_name FROM loan l LEFT JOIN enterprise e ON l.enterprise_id=e.id ORDER BY l.create_time DESC")
    loans = cursor.fetchall()
    cursor.execute("SELECT id, company_name FROM enterprise")
    enterprises = cursor.fetchall()
    db.close()
    return render_template('admin/loan_data.html', loans=loans, enterprises=enterprises, selected_status=status)


@app.route('/admin/repayment_data', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_repayment_data():
    db = get_db()
    cursor = db.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            cursor.execute(
                "INSERT INTO repayment (loan_id, enterprise_id, repay_amount, principal, interest, repay_date, status, create_time) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())",
                (request.form.get('loan_id'), request.form.get('enterprise_id'), request.form.get('repay_amount'),
                 request.form.get('principal'), request.form.get('interest'), request.form.get('repay_date'),
                 request.form.get('status')))
            flash('还款记录添加成功')
        elif action == 'edit':
            cursor.execute(
                "UPDATE repayment SET repay_amount=%s, principal=%s, interest=%s, repay_date=%s, status=%s WHERE id=%s",
                (request.form.get('repay_amount'), request.form.get('principal'), request.form.get('interest'),
                 request.form.get('repay_date'), request.form.get('status'), request.form.get('repay_id')))
            flash('还款记录更新成功')
        elif action == 'delete':
            cursor.execute("DELETE FROM repayment WHERE id=%s", (request.form.get('repay_id'),))
            flash('还款记录删除成功')
        db.commit()
    loan_id = request.args.get('loan_id', '')
    if loan_id:
        cursor.execute(
            "SELECT r.*, e.company_name, l.loan_no FROM repayment r LEFT JOIN enterprise e ON r.enterprise_id=e.id LEFT JOIN loan l ON r.loan_id=l.id WHERE r.loan_id=%s ORDER BY r.create_time DESC",
            (loan_id,))
    else:
        cursor.execute(
            "SELECT r.*, e.company_name, l.loan_no FROM repayment r LEFT JOIN enterprise e ON r.enterprise_id=e.id LEFT JOIN loan l ON r.loan_id=l.id ORDER BY r.create_time DESC LIMIT 200")
    repayments = cursor.fetchall()
    cursor.execute("SELECT id, loan_no FROM loan")
    loans = cursor.fetchall()
    cursor.execute("SELECT id, company_name FROM enterprise")
    enterprises = cursor.fetchall()
    db.close()
    return render_template('admin/repayment_data.html', repayments=repayments, loans=loans, enterprises=enterprises,
                           selected_loan=loan_id)


@app.route('/admin/assessment_data', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_assessment_data():
    db = get_db()
    cursor = db.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            cursor.execute(
                "INSERT INTO credit_assessment (enterprise_id, score, grade, industry_score, debt_score, cashflow_score, litigation_score, assess_time, create_time) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())",
                (request.form.get('enterprise_id'), request.form.get('score'), request.form.get('grade'),
                 request.form.get('industry_score'), request.form.get('debt_score'), request.form.get('cashflow_score'),
                 request.form.get('litigation_score')))
            flash('评估记录添加成功')
        elif action == 'edit':
            cursor.execute(
                "UPDATE credit_assessment SET score=%s, grade=%s, industry_score=%s, debt_score=%s, cashflow_score=%s, litigation_score=%s WHERE id=%s",
                (request.form.get('score'), request.form.get('grade'), request.form.get('industry_score'),
                 request.form.get('debt_score'), request.form.get('cashflow_score'),
                 request.form.get('litigation_score'), request.form.get('assess_id')))
            flash('评估记录更新成功')
        elif action == 'delete':
            cursor.execute("DELETE FROM credit_assessment WHERE id=%s", (request.form.get('assess_id'),))
            flash('评估记录删除成功')
        db.commit()
    grade = request.args.get('grade', '')
    if grade:
        cursor.execute(
            "SELECT ca.*, e.company_name FROM credit_assessment ca LEFT JOIN enterprise e ON ca.enterprise_id=e.id WHERE ca.grade=%s ORDER BY ca.assess_time DESC",
            (grade,))
    else:
        cursor.execute(
            "SELECT ca.*, e.company_name FROM credit_assessment ca LEFT JOIN enterprise e ON ca.enterprise_id=e.id ORDER BY ca.assess_time DESC LIMIT 200")
    assessments = cursor.fetchall()
    cursor.execute("SELECT id, company_name FROM enterprise")
    enterprises = cursor.fetchall()
    db.close()
    return render_template('admin/assessment_data.html', assessments=assessments, enterprises=enterprises,
                           selected_grade=grade)


@app.route('/admin/credit_history_data', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_credit_history_data():
    db = get_db()
    cursor = db.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            cursor.execute(
                "INSERT INTO credit_history (enterprise_id, record_type, record_source, record_content, record_date, create_time) VALUES (%s, %s, %s, %s, %s, NOW())",
                (request.form.get('enterprise_id'), request.form.get('record_type'), request.form.get('record_source'),
                 request.form.get('record_content'), request.form.get('record_date')))
            flash('征信记录添加成功')
        elif action == 'edit':
            cursor.execute(
                "UPDATE credit_history SET record_type=%s, record_source=%s, record_content=%s, record_date=%s WHERE id=%s",
                (request.form.get('record_type'), request.form.get('record_source'), request.form.get('record_content'),
                 request.form.get('record_date'), request.form.get('record_id')))
            flash('征信记录更新成功')
        elif action == 'delete':
            cursor.execute("DELETE FROM credit_history WHERE id=%s", (request.form.get('record_id'),))
            flash('征信记录删除成功')
        db.commit()
    ent_id = request.args.get('enterprise_id', '')
    if ent_id:
        cursor.execute(
            "SELECT ch.*, e.company_name FROM credit_history ch LEFT JOIN enterprise e ON ch.enterprise_id=e.id WHERE ch.enterprise_id=%s ORDER BY ch.record_date DESC",
            (ent_id,))
    else:
        cursor.execute(
            "SELECT ch.*, e.company_name FROM credit_history ch LEFT JOIN enterprise e ON ch.enterprise_id=e.id ORDER BY ch.record_date DESC LIMIT 200")
    records = cursor.fetchall()
    cursor.execute("SELECT id, company_name FROM enterprise")
    enterprises = cursor.fetchall()
    db.close()
    return render_template('admin/credit_history_data.html', records=records, enterprises=enterprises,
                           selected_ent=ent_id)


if __name__ == '__main__':
    app.run(debug=True, port=5000)# 导入Flask核心模块：Flask(应用实例)、render_template(渲染模板)、request(请求处理)、redirect(重定向)、url_for(URL生成)、session(会话)、flash(消息闪现)、jsonify(JSON响应)
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
# 导入functools.wraps：用于保留被装饰函数的元信息（如函数名、文档字符串）
from functools import wraps
# 导入pymysql：用于连接MySQL数据库
import pymysql
# 导入os：用于操作系统相关操作（如创建目录、文件路径处理）
import os
# 导入datetime：用于处理日期和时间
from datetime import datetime
# 导入json：用于JSON数据的序列化和反序列化
import json
# 导入requests：用于发送HTTP请求（调用AI API）
import requests
# 导入Decimal和ROUND_HALF_UP：用于高精度金融计算，解决浮点精度问题
from decimal import Decimal, ROUND_HALF_UP

# 创建Flask应用实例，__name__表示当前模块名，Flask会根据这个参数确定资源路径
app = Flask(__name__)
# 设置会话密钥，用于加密session数据（生产环境需使用随机且安全的密钥）
app.secret_key = 'bank_credit_secret_key_2024'
# 配置文件上传目录，指定上传文件保存到static/uploads文件夹
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# 使用os.makedirs创建上传目录，exist_ok=True表示目录已存在时不报错
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# 定义数据库连接函数：返回MySQL数据库连接对象
def get_db():
    # 使用pymysql.connect创建数据库连接，参数说明：
    # host：数据库主机地址（本地为localhost）
    # user：数据库用户名（root为默认管理员）
    # password：数据库密码（此处为123456）
    # database：要连接的数据库名（py_bccabusinesssystem）
    # charset：字符集（utf8mb4支持所有Unicode字符，包括emoji）
    # cursorclass：游标类型（DictCursor使查询结果以字典形式返回）
    return pymysql.connect(
        host='localhost',
        user='root',
        password='123456',
        database='py_bccabusinesssystem',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


# 定义登录验证装饰器：保护需要登录才能访问的路由
def login_required(f):
    # 使用@wraps(f)保留原函数f的元信息（避免装饰器修改函数名等属性）
    @wraps(f)
    # 定义装饰器的核心函数，接收任意参数（*args）和关键字参数（**kwargs）
    def decorated_function(*args, **kwargs):
        # 检查session中是否存在username（判断用户是否已登录）
        if 'username' not in session:
            # 未登录时，使用flash发送提示消息
            flash('请先登录')
            # 重定向到登录页面（url_for根据函数名生成URL）
            return redirect(url_for('login'))
        # 已登录时，执行原函数f并传递参数
        return f(*args, **kwargs)
    # 返回装饰后的函数
    return decorated_function


# 定义角色验证装饰器：限制路由仅允许指定角色的用户访问
def role_required(role):
    # 定义外层装饰器，接收需要的角色参数（admin/employee/enterprise）
    def decorator(f):
        # 保留原函数元信息
        @wraps(f)
        # 定义装饰器核心函数
        def decorated_function(*args, **kwargs):
            # 检查session中的用户角色是否与要求的角色匹配
            if session.get('role') != role:
                # 角色不匹配时，发送无权限提示
                flash('无权访问该页面')
                # 重定向到登录页
                return redirect(url_for('login'))
            # 角色匹配时，执行原函数
            return f(*args, **kwargs)
        # 返回装饰后的函数
        return decorated_function
    # 返回外层装饰器
    return decorator


# 定义信用评分计算函数：接收评估数据，返回总分、等级、分项得分、风险指标
def calculate_credit_score(data):
    # 创建空字典，用于存储各维度的得分
    scores = {}

    # 1. 行业评分（0-7分）：定义各行业对应的得分
    industry_scores = {'finance': 7, 'technology': 6, 'manufacturing': 5, 'retail': 4, 'construction': 3, 'other': 2}
    # 从data中获取industry值，若不存在则用'other'，并匹配对应得分
    scores['industry'] = industry_scores.get(data.get('industry', 'other'), 2)

    # 2. 负债率评分（0-7分）：处理负债率数据，避免类型错误
    try:
        # 将data中的debt_ratio转换为浮点数，默认值50
        debt_ratio = float(data.get('debt_ratio', 50))
    # 捕获值错误或类型错误（如输入非数字）
    except (ValueError, TypeError):
        # 异常时默认负债率为50.0
        debt_ratio = 50.0
    # 根据负债率区间赋值得分：<30%得7分
    if debt_ratio < 30:
        scores['debt'] = 7
    # 30%-50%得5分
    elif debt_ratio < 50:
        scores['debt'] = 5
    # 50%-70%得3分
    elif debt_ratio < 70:
        scores['debt'] = 3
    # ≥70%得1分
    else:
        scores['debt'] = 1

    # 3. 现金流评分（0-7分）：定义现金流状况对应的得分
    cashflow_scores = {'excellent': 7, 'good': 5, 'normal': 3, 'poor': 1}
    # 从data中获取cash_flow值，默认normal，匹配对应得分
    scores['cashflow'] = cashflow_scores.get(data.get('cash_flow', 'normal'), 3)

    # 4. 诉讼记录评分（0-7分）：处理诉讼次数数据
    try:
        # 将litigation_count转换为整数，默认0
        litigation = int(data.get('litigation_count', 0))
    # 捕获非数字输入的异常
    except (ValueError, TypeError):
        # 异常时默认诉讼次数为0
        litigation = 0
    # 0次诉讼得7分
    if litigation == 0:
        scores['litigation'] = 7
    # 1-2次得5分
    elif litigation <= 2:
        scores['litigation'] = 5
    # 3-5次得2分
    elif litigation <= 5:
        scores['litigation'] = 2
    # 超过5次得0分
    else:
        scores['litigation'] = 0

    # 5. 企业成立年限评分（0-7分）：处理成立年限数据
    try:
        # 将company_years转换为整数，默认3
        years = int(data.get('company_years', 3))
    # 捕获非数字输入异常
    except (ValueError, TypeError):
        # 异常时默认年限为3
        years = 3
    # ≥10年得7分
    if years >= 10:
        scores['years'] = 7
    # 5-9年得5分
    elif years >= 5:
        scores['years'] = 5
    # 3-4年得3分
    elif years >= 3:
        scores['years'] = 3
    # <3年得1分
    else:
        scores['years'] = 1

    # 6. 注册资本规模评分（0-7分）：定义注册资本区间对应的得分
    capital_scores = {'above_5000': 7, '1000_5000': 5, '500_1000': 4, '100_500': 3, 'below_100': 1}
    # 从data中获取注册资本区间，默认below_100，匹配得分
    scores['capital'] = capital_scores.get(data.get('registered_capital_range', 'below_100'), 1)

    # 7. 年营业收入评分（0-7分）：定义营收区间对应的得分
    revenue_scores = {'above_1y': 7, '5000w_1y': 6, '1000w_5000w': 5, '500w_1000w': 3, 'below_500w': 1}
    # 从data中获取营收区间，默认below_500w，匹配得分
    scores['revenue'] = revenue_scores.get(data.get('annual_revenue', 'below_500w'), 1)

    # 8. 净利润率评分（0-7分）：定义净利润率区间对应的得分
    profit_scores = {'above_20': 7, '10_20': 5, '5_10': 4, '0_5': 2, 'negative': 0}
    # 从data中获取净利润率区间，默认0_5，匹配得分
    scores['profit'] = profit_scores.get(data.get('profit_rate', '0_5'), 2)

    # 9. 资产负债结构评分（0-7分）：定义结构状况对应的得分
    asset_scores = {'excellent': 7, 'good': 5, 'normal': 3, 'poor': 1}
    # 从data中获取资产结构，默认normal，匹配得分
    scores['asset_structure'] = asset_scores.get(data.get('asset_structure', 'normal'), 3)

    # 10. 银行信贷记录评分（0-7分）：定义信贷记录对应的得分
    credit_scores = {'excellent': 7, 'good': 5, 'normal': 3, 'poor': 1, 'none': 2}
    # 从data中获取信贷记录，默认normal，匹配得分
    scores['bank_credit'] = credit_scores.get(data.get('bank_credit_record', 'normal'), 3)

    # 11. 税务信用等级评分（0-6分）：定义税务等级对应的得分
    tax_scores = {'A': 6, 'B': 5, 'C': 3, 'D': 1, 'M': 4}
    # 从data中获取税务等级，默认B，匹配得分
    scores['tax_credit'] = tax_scores.get(data.get('tax_credit_level', 'B'), 3)

    # 12. 社保缴纳情况评分（0-6分）：定义社保缴纳对应的得分
    social_scores = {'full': 6, 'partial': 4, 'irregular': 2, 'none': 0}
    # 从data中获取社保缴纳情况，默认partial，匹配得分
    scores['social_security'] = social_scores.get(data.get('social_security', 'partial'), 2)

    # 13. 供应链稳定性评分（0-6分）：定义供应链稳定性对应的得分
    supply_scores = {'very_stable': 6, 'stable': 5, 'normal': 3, 'unstable': 1}
    # 从data中获取供应链稳定性，默认normal，匹配得分
    scores['supply_chain'] = supply_scores.get(data.get('supply_chain', 'normal'), 3)

    # 14. 市场竞争力评分（0-6分）：定义市场地位对应的得分
    market_scores = {'leader': 6, 'strong': 5, 'normal': 3, 'weak': 1}
    # 从data中获取市场地位，默认normal，匹配得分
    scores['market_position'] = market_scores.get(data.get('market_position', 'normal'), 3)

    # 15. 管理团队经验评分（0-6分）：定义团队经验对应的得分
    team_scores = {'excellent': 6, 'experienced': 5, 'normal': 3, 'inexperienced': 1}
    # 从data中获取团队经验，默认normal，匹配得分
    scores['management_team'] = team_scores.get(data.get('management_team', 'normal'), 3)

    # 计算总分：将所有维度的得分相加
    total_score = sum(scores.values())

    # 根据总分确定信用等级：≥80分为A级（优质）
    if total_score >= 80:
        grade = 'A'
    # 60-79分为B级（良好）
    elif total_score >= 60:
        grade = 'B'
    # 40-59分为C级（一般）
    elif total_score >= 40:
        grade = 'C'
    # <40分为D级（风险）
    else:
        grade = 'D'

    # 调用风险指标计算函数，获取风险预警结果
    risk_indicators = calculate_risk_indicators(data, scores, total_score)

    # 返回计算结果：总分、等级、分项得分、风险指标
    return total_score, grade, scores, risk_indicators


# 定义风险预警指标计算函数：接收评估数据、分项得分、总分，返回各类风险等级
def calculate_risk_indicators(data, scores, total_score):
    # 创建风险指标字典，包含各类风险的等级（low/medium/high）
    indicators = {
        # 整体风险：≥70分低风险，50-69分中风险，<50分高风险
        'overall_risk': 'low' if total_score >= 70 else ('medium' if total_score >= 50 else 'high'),
        # 财务风险：负债率+现金流+净利润率≥15低风险，10-14中风险，<10高风险
        'financial_risk': 'low' if scores.get('debt', 0) + scores.get('cashflow', 0) + scores.get('profit',
                                                                                                  0) >= 15 else (
            'medium' if scores.get('debt', 0) + scores.get('cashflow', 0) + scores.get('profit', 0) >= 10 else 'high'),
        # 法律风险：诉讼记录得分≥5低风险，2-4中风险，<2高风险
        'legal_risk': 'low' if scores.get('litigation', 0) >= 5 else (
            'medium' if scores.get('litigation', 0) >= 2 else 'high'),
        # 运营风险：供应链+市场竞争力≥8低风险，5-7中风险，<5高风险
        'operational_risk': 'low' if scores.get('supply_chain', 0) + scores.get('market_position', 0) >= 8 else (
            'medium' if scores.get('supply_chain', 0) + scores.get('market_position', 0) >= 5 else 'high'),
        # 信用风险：银行信贷+税务等级≥10低风险，6-9中风险，<6高风险
        'credit_risk': 'low' if scores.get('bank_credit', 0) + scores.get('tax_credit', 0) >= 10 else (
            'medium' if scores.get('bank_credit', 0) + scores.get('tax_credit', 0) >= 6 else 'high'),
    }
    # 返回风险指标字典
    return indicators


# 定义AI咨询回答函数：调用火山引擎API获取回答，失败时使用本地回答
def get_ai_response(question):
    # 定义业务关键词列表：仅回答包含这些关键词的问题
    business_keywords = ['信用', '评估', '贷款', '还款', '征信', '上传', '营业执照', '企业信息', '存款', '取款', '账户',
                         '利率', '审核', '评分', '银行', '企业', '资金', '申请', '审批']
    # 判断问题是否包含业务关键词（any()只要有一个匹配就返回True）
    is_business = any(kw in question for kw in business_keywords)
    # 非业务问题返回提示语
    if not is_business:
        return "抱歉，我只能回答与信用评估、贷款、企业信息等业务相关的问题。请问您有什么业务方面的疑问？"

    # 尝试调用AI API
    try:
        # 火山引擎API密钥（生产环境应存入环境变量，避免硬编码）
        api_key = "34eb5f5a-bee1-488f-a9b2-e31d7420fd77"
        # 模型ID（火山引擎平台创建的模型）
        model = "ep-20250126163455-8xrmx"
        # API请求地址
        api_url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

        # 定义请求头：指定内容类型为JSON，授权方式为Bearer+API密钥
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        # 构建API请求体：包含模型名称和对话消息
        data = {
            "model": model,  # 指定使用的模型
            "messages": [    # 对话消息列表
                {
                    "role": "system",  # 系统角色：定义AI的身份和回答规则
                    "content": "你是银行对公信用评估业务系统的智能客服助手。你专门负责解答企业客户关于信用评估、贷款申请、还款、征信查询、企业信息管理、账户存取款等业务问题。请用专业、友好的语气回答问题。"
                },
                {
                    "role": "user",    # 用户角色：传递用户的问题
                    "content": question + ",简略回答，一定不超过100字"  # 限制回答长度
                }
            ]
        }

        # 发送POST请求调用API，timeout=30表示30秒超时
        response = requests.post(api_url, headers=headers, json=data, timeout=30)

        # 检查API响应状态码：200表示成功
        if response.status_code == 200:
            # 将响应内容解析为JSON格式
            result = response.json()
            # 检查是否包含choices字段且有内容
            if 'choices' in result and len(result['choices']) > 0:
                # 返回AI生成的回答内容
                return result['choices'][0]['message']['content']
            else:
                # 无回答内容时返回提示
                return "抱歉，暂时无法获取回答，请稍后再试。"
        else:
            # API响应失败时调用本地回答函数
            return get_local_response(question)
    # 捕获所有异常（如网络错误、超时等）
    except Exception as e:
        # 打印异常信息（便于调试）
        print(f"AI API调用异常: {e}")
        # 异常时调用本地回答函数
        return get_local_response(question)


# 定义本地备用回答函数：API调用失败时使用预设问答库
def get_local_response(question):
    # 定义预设问答字典：关键词 -> 回答
    qa = {
        '信用评估': '信用评估根据企业的行业类型、负债率、现金流状况、诉讼记录等因素，通过评分卡模型计算0-100分的信用评分，并给出A/B/C/D等级。',
        '贷款': '企业可在贷款还款模块查看当前贷款状态、还款进度。贷款审批需要银行员工根据信用评估结果进行。',
        '还款': '还款可通过贷款还款模块进行，系统会自动计算本金和利息。建议按时还款以维护良好的信用记录。',
        '征信': '征信信息可通过征信查询模块跳转至全国法院信息综合查询等外部平台查询。',
        '上传': '企业可在企业信息管理模块上传营业执照等资料，上传后需等待管理员审核通过。',
        '营业执照': '营业执照上传后会进入审核流程，审核通过后企业信息才会更新。请确保上传的图片清晰可辨。',
        '账户': '虚拟对公账户用于模拟企业资金变动，支持存入和支取操作，所有交易都会记录在流水明细中。',
        '利率': '贷款利率根据企业信用等级确定，A级企业可享受基准利率，其他等级会有相应上浮。'
    }
    # 遍历问答字典，匹配问题中的关键词
    for kw, ans in qa.items():
        # 关键词匹配时返回对应的回答
        if kw in question: return ans
    # 无匹配关键词时返回默认回答
    return "感谢您的提问。关于这个问题，建议您联系银行客服获取更详细的解答，或查看相关功能模块的帮助说明。"


# ==================== 认证路由 ====================
# 定义首页路由：URL为/，支持GET请求
@app.route('/')
def index():
    # 检查session中是否有username（用户已登录）
    if 'username' in session:
        # 获取用户角色
        role = session.get('role')
        # 管理员角色跳转到管理员仪表盘
        if role == 'admin':
            return redirect(url_for('admin_dashboard'))
        # 员工角色跳转到员工仪表盘
        elif role == 'employee':
            return redirect(url_for('employee_dashboard'))
        # 企业用户角色跳转到企业仪表盘
        else:
            return redirect(url_for('enterprise_dashboard'))
    # 未登录时跳转到登录页
    return redirect(url_for('login'))


# 定义登录路由：URL为/login，支持GET和POST请求
@app.route('/login', methods=['GET', 'POST'])
def login():
    # 判断请求方法是否为POST（用户提交登录表单）
    if request.method == 'POST':
        # 从表单中获取用户名（name=username）
        username = request.form.get('username')
        # 从表单中获取密码（name=password）
        password = request.form.get('password')
        # 调用get_db()获取数据库连接
        db = get_db()
        # 创建游标对象（用于执行SQL语句）
        cursor = db.cursor()
        # 执行SQL查询：查询用户名、密码匹配且状态为1（启用）的用户
        cursor.execute("SELECT * FROM user WHERE username=%s AND password=%s AND status=1", (username, password))
        # 获取查询结果（单行）
        user = cursor.fetchone()
        # 关闭数据库连接（释放资源）
        db.close()
        # 判断是否查询到用户（用户名密码正确）
        if user:
            # 将用户ID存入session
            session['user_id'] = user['id']
            # 将用户名存入session
            session['username'] = user['username']
            # 将用户姓名存入session
            session['name'] = user['name']
            # 将用户角色存入session
            session['role'] = user['role']
            # 发送登录成功提示
            flash('登录成功')
            # 根据角色跳转：管理员跳转到admin_dashboard
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            # 员工跳转到employee_dashboard
            elif user['role'] == 'employee':
                return redirect(url_for('employee_dashboard'))
            # 企业用户跳转到enterprise_dashboard
            else:
                return redirect(url_for('enterprise_dashboard'))
        else:
            # 用户名或密码错误时发送提示
            flash('用户名或密码错误')
    # GET请求时渲染登录页面（auth/login.html模板）
    return render_template('auth/login.html')


# 定义注册路由：URL为/register，支持GET和POST请求
@app.route('/register', methods=['GET', 'POST'])
def register():
    # 判断请求方法是否为POST（用户提交注册表单）
    if request.method == 'POST':
        # 从表单获取用户名
        username = request.form.get('username')
        # 从表单获取密码
        password = request.form.get('password')
        # 从表单获取姓名
        name = request.form.get('name')
        # 从表单获取手机号
        phone = request.form.get('phone')
        # 从表单获取邮箱
        email = request.form.get('email')
        # 获取数据库连接
        db = get_db()
        # 创建游标
        cursor = db.cursor()
        # 执行SQL：查询用户名是否已存在
        cursor.execute("SELECT * FROM user WHERE username=%s", (username,))
        # 判断用户名是否已存在
        if cursor.fetchone():
            # 发送用户名已存在提示
            flash('用户名已存在')
            # 关闭数据库连接
            db.close()
            # 重新渲染注册页面
            return render_template('auth/register.html')
        # 执行SQL：插入用户记录（角色默认为enterprise，状态为1）
        cursor.execute(
            "INSERT INTO user (username, password, name, role, phone, email, status, create_time, update_time) VALUES (%s, %s, %s, 'enterprise', %s, %s, 1, NOW(), NOW())",
            (username, password, name, phone, email))
        # 获取刚插入的用户ID（lastrowid返回最后插入行的ID）
        user_id = cursor.lastrowid
        # 执行SQL：插入企业记录（关联用户ID，公司名称为姓名）
        cursor.execute(
            "INSERT INTO enterprise (user_id, company_name, create_time, update_time) VALUES (%s, %s, NOW(), NOW())",
            (user_id, name))
        # 获取刚插入的企业ID
        enterprise_id = cursor.lastrowid
        # 生成虚拟账户号：6222 + 12位企业ID（zfill(12)补零到12位）
        account_no = f"6222{str(enterprise_id).zfill(12)}"
        # 执行SQL：插入账户记录（初始余额为0）
        cursor.execute(
            "INSERT INTO account (enterprise_id, account_no, balance, create_time, update_time) VALUES (%s, %s, 0, NOW(), NOW())",
            (enterprise_id, account_no))
        # 提交事务（确保所有插入操作生效）
        db.commit()
        # 关闭数据库连接
        db.close()
        # 发送注册成功提示
        flash('注册成功，请登录')
        # 重定向到登录页
        return redirect(url_for('login'))
    # GET请求时渲染注册页面
    return render_template('auth/register.html')


# 定义登出路由：URL为/logout，支持GET请求
@app.route('/logout')
def logout():
    # 清空session中的所有数据（退出登录）
    session.clear()
    # 发送退出成功提示
    flash('已退出登录')
    # 重定向到登录页
    return redirect(url_for('login'))


# ==================== 企业端路由 ====================
# 定义企业仪表盘路由：URL为/enterprise/dashboard，需登录且角色为enterprise
@app.route('/enterprise/dashboard')
@login_required
@role_required('enterprise')
def enterprise_dashboard():
    # 获取数据库连接
    db = get_db()
    # 创建游标
    cursor = db.cursor()
    # 执行SQL：根据用户ID查询企业ID
    cursor.execute("SELECT id FROM enterprise WHERE user_id=%s", (session['user_id'],))
    # 获取企业记录
    ent = cursor.fetchone()
    # 判断企业记录是否存在
    if not ent:
        # 关闭数据库连接
        db.close()
        # 发送企业信息不存在提示
        flash('企业信息不存在')
        # 重定向到登出页
        return redirect(url_for('logout'))
    # 提取企业ID
    ent_id = ent['id']
    # 执行SQL：查询企业账户余额
    cursor.execute("SELECT balance FROM account WHERE enterprise_id=%s", (ent_id,))
    # 获取账户记录
    account = cursor.fetchone()
    # 提取余额（无记录时为0）
    balance = account['balance'] if account else 0
    # 执行SQL：查询未结清贷款数量和剩余总额
    cursor.execute(
        "SELECT COUNT(*) as cnt, SUM(remaining_amount) as total FROM loan WHERE enterprise_id=%s AND status='repaying'",
        (ent_id,))
    # 获取贷款统计信息
    loan_info = cursor.fetchone()
    # 执行SQL：查询最新的信用评估记录（按评估时间降序，取第一条）
    cursor.execute(
        "SELECT score, grade FROM credit_assessment WHERE enterprise_id=%s ORDER BY assess_time DESC LIMIT 1",
        (ent_id,))
    # 获取信用评估记录
    credit = cursor.fetchone()
    # 关闭数据库连接
    db.close()
    # 渲染企业仪表盘模板，传递余额、贷款数量、贷款总额、信用评估数据
    return render_template('enterprise/dashboard.html', balance=balance, loan_count=loan_info['cnt'] or 0,
                           loan_total=loan_info['total'] or 0, credit=credit)


# 定义企业账户路由：URL为/enterprise/account，支持GET和POST，需登录且角色为enterprise
@app.route('/enterprise/account', methods=['GET', 'POST'])
@login_required
@role_required('enterprise')
def enterprise_account():
    # 获取数据库连接
    db = get_db()
    # 创建游标
    cursor = db.cursor()
    # 执行SQL：查询企业ID
    cursor.execute("SELECT id FROM enterprise WHERE user_id=%s", (session['user_id'],))
    # 获取企业记录
    ent = cursor.fetchone()
    # 提取企业ID
    ent_id = ent['id']
    # 执行SQL：查询企业账户信息
    cursor.execute("SELECT * FROM account WHERE enterprise_id=%s", (ent_id,))
    # 获取账户记录
    account = cursor.fetchone()
    # 判断请求方法是否为POST（用户执行存款/支取操作）
    if request.method == 'POST':
        # 从表单获取操作类型（deposit/withdraw）
        action = request.form.get('action')
        # 尝试转换金额为Decimal（高精度）
        try:
            amount = Decimal(request.form.get('amount', 0))  # 修改：使用Decimal
        # 捕获值错误或类型错误
        except (ValueError, TypeError):
            # 发送金额格式错误提示
            flash('金额格式错误，请输入数字')
            # 关闭数据库连接
            db.close()
            # 重定向到账户页面
            return redirect(url_for('enterprise_account'))

        # 判断金额是否小于等于0
        if amount <= 0:
            # 发送金额必须大于0提示
            flash('金额必须大于0')
        # 支取操作且金额大于账户余额
        elif action == 'withdraw' and amount > Decimal(str(account['balance'])):  # 修改：类型统一
            # 发送余额不足提示
            flash('余额不足')
        else:
            # 转换当前余额为Decimal（避免浮点精度问题）
            current_balance = Decimal(str(account['balance']))
            # 计算新余额：存款加，支取减
            new_balance = current_balance + amount if action == 'deposit' else current_balance - amount
            # 保留两位小数，四舍五入（金融计算标准）
            new_balance = new_balance.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)

            # 执行SQL：更新账户余额
            cursor.execute("UPDATE account SET balance=%s, update_time=NOW() WHERE id=%s",
                           (float(new_balance), account['id']))
            # 定义交易类型
            trans_type = 'deposit' if action == 'deposit' else 'withdraw'
            # 执行SQL：插入交易记录
            cursor.execute(
                "INSERT INTO transaction (account_id, enterprise_id, trans_type, amount, balance_after, remark, create_time) VALUES (%s, %s, %s, %s, %s, %s, NOW())",
                (account['id'], ent_id, trans_type, float(amount), float(new_balance), request.form.get('remark', '')))
            # 提交事务
            db.commit()
            # 发送操作成功提示
            flash('存入成功' if action == 'deposit' else '支取成功')
            # 重新查询账户信息（更新后的数据）
            cursor.execute("SELECT * FROM account WHERE enterprise_id=%s", (ent_id,))
            account = cursor.fetchone()
    # 执行SQL：查询最近50条交易记录（按创建时间降序）
    cursor.execute("SELECT * FROM transaction WHERE enterprise_id=%s ORDER BY create_time DESC LIMIT 50", (ent_id,))
    # 获取交易记录列表
    transactions = cursor.fetchall()
    # 关闭数据库连接
    db.close()
    # 渲染账户页面，传递账户信息和交易记录
    return render_template('enterprise/account.html', account=account, transactions=transactions)


# 定义企业贷款路由：URL为/enterprise/loan，支持GET和POST，需登录且角色为enterprise
@app.route('/enterprise/loan', methods=['GET', 'POST'])
@login_required
@role_required('enterprise')
def enterprise_loan():
    # 获取数据库连接
    db = get_db()
    # 创建游标
    cursor = db.cursor()
    # 执行SQL：查询企业ID
    cursor.execute("SELECT id FROM enterprise WHERE user_id=%s", (session['user_id'],))
    # 获取企业记录
    ent = cursor.fetchone()
    # 提取企业ID
    ent_id = ent['id']
    # 判断请求方法是否为POST
    if request.method == 'POST':
        # 从表单获取操作类型（apply/repay）
        action = request.form.get('action')
        # 处理贷款申请
        if action == 'apply':
            # 尝试转换贷款金额和期限
            try:
                amount = Decimal(request.form.get('loan_amount', 0))  # 修改：使用Decimal
                term = int(request.form.get('loan_term', 12))
                # 判断金额是否小于等于0
                if amount <= 0:
                    flash('贷款金额必须大于0')
                else:
                    # 生成贷款编号：LN + 时间戳（年月日时分秒）
                    loan_no = f"LN{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    # 执行SQL：插入贷款记录（状态为pending，利率4.35%）
                    cursor.execute(
                        "INSERT INTO loan (enterprise_id, loan_no, loan_amount, interest_rate, loan_term, remaining_amount, status, apply_time, create_time) VALUES (%s, %s, %s, 4.35, %s, %s, 'pending', NOW(), NOW())",
                        (ent_id, loan_no, float(amount), term, float(amount)))
                    # 提交事务
                    db.commit()
                    # 发送申请成功提示
                    flash('贷款申请已提交')
            # 捕获值错误或类型错误
            except (ValueError, TypeError):
                # 发送金额格式错误提示
                flash('贷款金额格式错误，请输入数字')
        # 处理还款操作
        elif action == 'repay':
            # 从表单获取贷款ID
            loan_id = request.form.get('loan_id')
            # 尝试转换还款金额为Decimal
            try:
                repay_amount = Decimal(request.form.get('repay_amount', 0))  # 修改：使用Decimal
                # 判断金额是否小于等于0
                if repay_amount <= 0:
                    flash('还款金额必须大于0')
                    db.close()
                    return redirect(url_for('enterprise_loan'))
            # 捕获值错误或类型错误
            except (ValueError, TypeError):
                flash('还款金额格式错误，请输入数字')
                db.close()
                return redirect(url_for('enterprise_loan'))

            # 执行SQL：查询贷款记录（验证归属）
            cursor.execute("SELECT * FROM loan WHERE id=%s AND enterprise_id=%s", (loan_id, ent_id))
            # 获取贷款记录
            loan = cursor.fetchone()
            # 判断贷款记录是否存在
            if loan:
                # 转换剩余金额为Decimal
                remaining_amount = Decimal(str(loan['remaining_amount']))
                # 定义利率（10%）
                interest_rate = Decimal('0.1')
                # 计算利息（四舍五入保留两位小数）
                interest = (repay_amount * interest_rate).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
                # 计算本金（还款金额 - 利息）
                principal = (repay_amount - interest).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)

                # 计算新的剩余本金（最小为0）
                new_remaining = max(Decimal('0'), remaining_amount - principal)
                # 定义新状态：剩余本金为0则完成，否则还款中
                new_status = 'completed' if new_remaining == Decimal('0') else 'repaying'

                # 执行SQL：更新贷款剩余本金和状态
                cursor.execute("UPDATE loan SET remaining_amount=%s, status=%s WHERE id=%s",
                               (float(new_remaining), new_status, loan_id))
                # 执行SQL：插入还款记录
                cursor.execute(
                    "INSERT INTO repayment (loan_id, enterprise_id, repay_amount, principal, interest, repay_date, status, actual_repay_time, create_time) VALUES (%s, %s, %s, %s, %s, CURDATE(), 'paid', NOW(), NOW())",
                    (loan_id, ent_id, float(repay_amount), float(principal), float(interest)))
                # 提交事务
                db.commit()
                # 发送还款成功提示
                flash('还款成功')
    # 执行SQL：查询企业所有贷款记录（按创建时间降序）
    cursor.execute("SELECT * FROM loan WHERE enterprise_id=%s ORDER BY create_time DESC", (ent_id,))
    # 获取贷款记录列表
    loans = cursor.fetchall()
    # 执行SQL：查询最近20条还款记录
    cursor.execute("SELECT * FROM repayment WHERE enterprise_id=%s ORDER BY create_time DESC LIMIT 20", (ent_id,))
    # 获取还款记录列表
    repayments = cursor.fetchall()
    # 关闭数据库连接
    db.close()
    # 渲染贷款页面，传递贷款和还款记录
    return render_template('enterprise/loan.html', loans=loans, repayments=repayments)


# 定义企业信息路由：URL为/enterprise/company_info，支持GET和POST，需登录且角色为enterprise
@app.route('/enterprise/company_info', methods=['GET', 'POST'])
@login_required
@role_required('enterprise')
def enterprise_company_info():
    # 获取数据库连接
    db = get_db()
    # 创建游标
    cursor = db.cursor()
    # 执行SQL：查询企业信息
    cursor.execute("SELECT * FROM enterprise WHERE user_id=%s", (session['user_id'],))
    # 获取企业记录
    enterprise = cursor.fetchone()
    # 判断请求方法是否为POST
    if request.method == 'POST':
        # 从表单获取企业名称
        company_name = request.form.get('company_name')
        # 从表单获取统一社会信用代码
        credit_code = request.form.get('credit_code')
        # 从表单获取法人
        legal_person = request.form.get('legal_person')
        # 从表单获取注册资本
        registered_capital = request.form.get('registered_capital')
        # 从表单获取行业
        industry = request.form.get('industry')
        # 从表单获取地址
        address = request.form.get('address')
        # 验证统一社会信用代码（必须18位）
        if credit_code and len(credit_code) != 18:
            flash('统一社会信用代码必须为18位')
        else:
            # 执行SQL：更新企业基本信息
            cursor.execute(
                "UPDATE enterprise SET company_name=%s, credit_code=%s, legal_person=%s, registered_capital=%s, industry=%s, address=%s, update_time=NOW() WHERE user_id=%s",
                (company_name, credit_code, legal_person, registered_capital, industry, address, session['user_id']))
            # 判断是否有营业执照文件上传
            if 'business_license' in request.files:
                # 获取上传的文件
                file = request.files['business_license']
                # 判断文件是否存在且有文件名
                if file and file.filename:
                    # 生成唯一文件名：license_用户ID_时间戳.jpg
                    filename = f"license_{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                    # 拼接文件保存路径
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    # 保存文件到服务器
                    file.save(filepath)
                    # 执行SQL：更新企业营业执照字段（状态0=待审核）
                    cursor.execute("UPDATE enterprise SET business_license=%s, license_status=0 WHERE user_id=%s",
                                   (filename, session['user_id']))
                    # 执行SQL：插入内容审核记录
                    cursor.execute(
                        "INSERT INTO content_review (enterprise_id, content_type, content_path, status, create_time) VALUES (%s, 'license', %s, 0, NOW())",
                        (enterprise['id'], filename))
            # 提交事务
            db.commit()
            # 发送更新成功提示
            flash('企业信息更新成功')
            # 重新查询企业信息
            cursor.execute("SELECT * FROM enterprise WHERE user_id=%s", (session['user_id'],))
            enterprise = cursor.fetchone()
    # 关闭数据库连接
    db.close()
    # 渲染企业信息页面，传递企业数据
    return render_template('enterprise/company_info.html', enterprise=enterprise)


# 定义征信查询路由：URL为/enterprise/credit_query，需登录且角色为enterprise
@app.route('/enterprise/credit_query')
@login_required
@role_required('enterprise')
def enterprise_credit_query():
    # 获取数据库连接
    db = get_db()
    # 创建游标
    cursor = db.cursor()
    # 执行SQL：查询启用的外部链接（状态=1）
    cursor.execute("SELECT * FROM external_link WHERE status=1 ORDER BY id")
    # 获取链接列表
    links = cursor.fetchall()
    # 关闭数据库连接
    db.close()
    # 渲染征信查询页面，传递链接数据
    return render_template('enterprise/credit_query.html', links=links)


# 定义信用可视化路由：URL为/enterprise/credit_visual，需登录且角色为enterprise
@app.route('/enterprise/credit_visual')
@login_required
@role_required('enterprise')
def enterprise_credit_visual():
    # 获取数据库连接
    db = get_db()
    # 创建游标
    cursor = db.cursor()
    # 执行SQL：查询企业ID
    cursor.execute("SELECT id FROM enterprise WHERE user_id=%s", (session['user_id'],))
    # 获取企业记录
    ent = cursor.fetchone()
    # 提取企业ID
    ent_id = ent['id']
    # 执行SQL：查询最新的信用评估记录
    cursor.execute("SELECT * FROM credit_assessment WHERE enterprise_id=%s ORDER BY assess_time DESC LIMIT 1",
                   (ent_id,))
    # 获取最新评估记录
    latest = cursor.fetchone()
    # 执行SQL：查询最近12次评估记录（用于趋势图）
    cursor.execute(
        "SELECT score, assess_time FROM credit_assessment WHERE enterprise_id=%s ORDER BY assess_time DESC LIMIT 12",
        (ent_id,))
    # 获取历史评估记录
    history = cursor.fetchall()
    # 执行SQL：查询各信用等级的企业数量
    cursor.execute("SELECT grade, COUNT(*) as cnt FROM credit_assessment GROUP BY grade")
    # 获取等级分布数据
    grade_dist = cursor.fetchall()
    # 执行SQL：查询所有评估的平均得分
    cursor.execute("SELECT AVG(score) as avg_score FROM credit_assessment")
    # 获取平均得分
    avg = cursor.fetchone()
    # 初始化风险指标为None
    risk_indicators = None
    # 判断是否有最新评估数据且包含问卷数据
    if latest and latest.get('questionnaire_data'):
        # 尝试解析问卷数据
        try:
            # 若问卷数据是字符串则反序列化为字典，否则直接使用
            data = json.loads(latest_data['questionnaire_data']) if isinstance(latest_data['questionnaire_data'],
                                                                               str) else latest_data[
                'questionnaire_data']
            # 计算信用评分和风险指标
            _, _, scores, risk_indicators = calculate_credit_score(data)
        # 捕获解析异常
        except:
            # 异常时风险指标仍为None
            risk_indicators = None
    # 关闭数据库连接
    db.close()
    # 渲染信用可视化页面，传递各类数据
    return render_template('enterprise/credit_visual.html', latest=latest, history=list(reversed(history)),
                           grade_dist=grade_dist, avg_score=avg['avg_score'] or 0, risk_indicators=risk_indicators)


# 定义企业风险预警路由：URL为/enterprise/risk_warning，需登录且角色为enterprise
@app.route('/enterprise/risk_warning')
@login_required
@role_required('enterprise')
def enterprise_risk_warning():
    # 获取数据库连接
    db = get_db()
    # 创建游标
    cursor = db.cursor()
    # 执行SQL：查询企业ID
    cursor.execute("SELECT id FROM enterprise WHERE user_id=%s", (session['user_id'],))
    # 获取企业记录
    ent = cursor.fetchone()
    # 提取企业ID
    ent_id = ent['id']

    # 执行SQL：查询最新评估数据
    cursor.execute("SELECT * FROM credit_assessment WHERE enterprise_id=%s ORDER BY assess_time DESC LIMIT 1",
                   (ent_id,))
    # 获取最新评估记录
    latest = cursor.fetchone()

    # 执行SQL：查询最近12次评估记录
    cursor.execute(
        "SELECT score, grade, assess_time FROM credit_assessment WHERE enterprise_id=%s ORDER BY assess_time DESC LIMIT 12",
        (ent_id,))
    # 获取历史评估记录
    history = cursor.fetchall()

    # 执行SQL：查询贷款风险数据（总数和未结清总额）
    cursor.execute(
        "SELECT COUNT(*) as total, SUM(CASE WHEN status='repaying' THEN remaining_amount ELSE 0 END) as debt FROM loan WHERE enterprise_id=%s",
        (ent_id,))
    # 获取贷款风险数据
    loan_risk = cursor.fetchone()

    # 执行SQL：查询近30天现金流数据（按日期分组）
    cursor.execute(
        "SELECT DATE(create_time) as date, SUM(CASE WHEN trans_type='deposit' THEN amount ELSE -amount END) as net_flow FROM transaction WHERE enterprise_id=%s AND create_time >= DATE_SUB(NOW(), INTERVAL 30 DAY) GROUP BY DATE(create_time) ORDER BY date",
        (ent_id,))
    # 获取现金流数据
    cash_flow = cursor.fetchall()

    # 初始化风险指标为None
    risk_indicators = None
    # 判断是否有最新评估数据且包含问卷数据
    if latest and latest.get('questionnaire_data'):
        # 尝试解析问卷数据
        try:
            # 解析JSON字符串为字典
            data = json.loads(latest['questionnaire_data']) if isinstance(latest['questionnaire_data'], str) else \
            latest['questionnaire_data']
            # 计算风险指标
            _, _, scores, risk_indicators = calculate_credit_score(data)
        # 捕获异常
        except:
            # 异常时使用默认风险指标
            risk_indicators = {'overall_risk': 'medium', 'financial_risk': 'medium', 'legal_risk': 'low',
                               'operational_risk': 'medium', 'credit_risk': 'medium'}

    # 关闭数据库连接
    db.close()
    # 渲染风险预警页面，传递各类数据
    return render_template('enterprise/risk_warning.html', latest=latest, history=list(reversed(history)),
                           loan_risk=loan_risk, cash_flow=cash_flow, risk_indicators=risk_indicators)


# 定义企业信用评估路由：URL为/enterprise/assessment，支持GET和POST，需登录且角色为enterprise
@app.route('/enterprise/assessment', methods=['GET', 'POST'])
@login_required
@role_required('enterprise')
def enterprise_assessment():
    # 获取数据库连接
    db = get_db()
    # 创建游标
    cursor = db.cursor()
    # 执行SQL：查询企业信息
    cursor.execute("SELECT * FROM enterprise WHERE user_id=%s", (session['user_id'],))
    # 获取企业记录
    enterprise = cursor.fetchone()
    # 初始化评估结果为None
    result = None
    # 初始化风险指标为None
    risk_indicators = None
    # 判断请求方法是否为POST
    if request.method == 'POST':
        # 收集表单中的评估数据
        data = {
            'industry': request.form.get('industry'),
            'debt_ratio': request.form.get('debt_ratio'),
            'cash_flow': request.form.get('cash_flow'),
            'litigation_count': request.form.get('litigation_count'),
            'company_years': request.form.get('company_years'),
            'registered_capital_range': request.form.get('registered_capital_range'),
            'annual_revenue': request.form.get('annual_revenue'),
            'profit_rate': request.form.get('profit_rate'),
            'asset_structure': request.form.get('asset_structure'),
            'bank_credit_record': request.form.get('bank_credit_record'),
            'tax_credit_level': request.form.get('tax_credit_level'),
            'social_security': request.form.get('social_security'),
            'supply_chain': request.form.get('supply_chain'),
            'market_position': request.form.get('market_position'),
            'management_team': request.form.get('management_team')
        }
        # 计算信用评分
        score, grade, scores, risk_indicators = calculate_credit_score(data)
        # 执行SQL：插入信用评估记录
        cursor.execute(
            "INSERT INTO credit_assessment (enterprise_id, score, grade, industry_score, debt_score, cashflow_score, litigation_score, questionnaire_data, assess_time, create_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())",
            (
            enterprise['id'], score, grade, scores.get('industry', 0), scores.get('debt', 0), scores.get('cashflow', 0),
            scores.get('litigation', 0), json.dumps(data)))
        # 提交事务
        db.commit()
        # 组装评估结果
        result = {'score': score, 'grade': grade, 'scores': scores, 'risk_indicators': risk_indicators}
        # 发送评估完成提示
        flash(f'评估完成！您的信用评分为{score}分，等级为{grade}')
    # 执行SQL：查询最近5次评估记录
    cursor.execute("SELECT * FROM credit_assessment WHERE enterprise_id=%s ORDER BY assess_time DESC LIMIT 5",
                   (enterprise['id'],))
    # 获取评估记录列表
    assessments = cursor.fetchall()
    # 关闭数据库连接
    db.close()
    # 渲染评估页面，传递企业信息、评估结果、历史评估记录
    return render_template('enterprise/assessment.html', enterprise=enterprise, result=result, assessments=assessments)


# 定义AI咨询API路由：URL为/api/ai_consult，仅支持POST，需登录
@app.route('/api/ai_consult', methods=['POST'])
@login_required
def api_ai_consult():
    # 从JSON请求体中获取用户问题
    question = request.json.get('question', '')
    # 调用AI回答函数获取回答
    answer = get_ai_response(question)
    # 判断用户角色是否为企业
    if session.get('role') == 'enterprise':
        # 获取数据库连接
        db = get_db()
        # 创建游标
        cursor = db.cursor()
        # 执行SQL：查询企业ID
        cursor.execute("SELECT id FROM enterprise WHERE user_id=%s", (session['user_id'],))
        # 获取企业记录
        ent = cursor.fetchone()
        # 判断企业记录是否存在
        if ent:
            # 执行SQL：插入AI咨询记录
            cursor.execute(
                "INSERT INTO ai_consultation (enterprise_id, question, answer, create_time) VALUES (%s, %s, %s, NOW())",
                (ent['id'], question, answer))
            # 提交事务
            db.commit()
        # 关闭数据库连接
        db.close()
    # 返回JSON格式的回答
    return jsonify({'answer': answer})


# ==================== 银行员工端路由 ====================
# 定义员工仪表盘路由：URL为/employee/dashboard，需登录且角色为employee
@app.route('/employee/dashboard')
@login_required
@role_required('employee')
def employee_dashboard():
    # 获取数据库连接
    db = get_db()
    # 创建游标
    cursor = db.cursor()
    # 执行SQL：查询企业总数
    cursor.execute("SELECT COUNT(*) as cnt FROM enterprise")
    # 获取企业数量
    ent_count = cursor.fetchone()['cnt']
    # 执行SQL：查询待审批贷款数量
    cursor.execute("SELECT COUNT(*) as cnt FROM loan WHERE status='pending'")
    # 获取待审批贷款数量
    pending_loans = cursor.fetchone()['cnt']
    # 执行SQL：查询在贷贷款数量
    cursor.execute("SELECT COUNT(*) as cnt FROM loan WHERE status='repaying'")
    # 获取在贷贷款数量
    active_loans = cursor.fetchone()['cnt']
    # 执行SQL：查询累计放贷金额（在贷+已完成）
    cursor.execute("SELECT SUM(loan_amount) as total FROM loan WHERE status IN ('repaying', 'completed')")
    # 获取累计放贷金额
    total_loan = cursor.fetchone()['total'] or 0
    # 执行SQL：查询各信用等级企业数量（取最新评估）
    cursor.execute(
        "SELECT grade, COUNT(*) as cnt FROM credit_assessment ca INNER JOIN (SELECT enterprise_id, MAX(assess_time) as max_time FROM credit_assessment GROUP BY enterprise_id) latest ON ca.enterprise_id=latest.enterprise_id AND ca.assess_time=latest.max_time GROUP BY grade")
    # 获取等级统计数据
    grade_stats = cursor.fetchall()
    # 关闭数据库连接
    db.close()
    # 渲染员工仪表盘，传递各类统计数据
    return render_template('employee/dashboard.html', ent_count=ent_count, pending_loans=pending_loans,
                           active_loans=active_loans, total_loan=total_loan, grade_stats=grade_stats)


# 定义员工企业列表路由：URL为/employee/enterprise_list，需登录且角色为employee
@app.route('/employee/enterprise_list')
@login_required
@role_required('employee')
def employee_enterprise_list():
    # 获取数据库连接
    db = get_db()
    # 创建游标
    cursor = db.cursor()
    # 从URL参数获取搜索关键词
    search = request.args.get('search', '')
    # 判断是否有搜索关键词
    if search:
        # 执行SQL：模糊查询企业（名称或信用代码）
        cursor.execute(
            "SELECT e.*, u.phone, u.email FROM enterprise e LEFT JOIN user u ON e.user_id=u.id WHERE e.company_name LIKE %s OR e.credit_code LIKE %s",
            (f'%{search}%', f'%{search}%'))
    else:
        # 执行SQL：查询所有企业
        cursor.execute("SELECT e.*, u.phone, u.email FROM enterprise e LEFT JOIN user u ON e.user_id=u.id")
    # 获取企业列表
    enterprises = cursor.fetchall()
    # 关闭数据库连接
    db.close()
    # 渲染企业列表页面，传递企业数据和搜索关键词
    return render_template('employee/enterprise_list.html', enterprises=enterprises, search=search)


# 定义员工征信记录路由：URL为/employee/credit_records，需登录且角色为employee
@app.route('/employee/credit_records')
@login_required
@role_required('employee')
def employee_credit_records():
    # 获取数据库连接
    db = get_db()
    # 创建游标
    cursor = db.cursor()
    # 从URL参数获取企业ID筛选条件
    ent_id = request.args.get('enterprise_id', '')
    # 判断是否有企业ID筛选
    if ent_id:
        # 执行SQL：查询指定企业的征信记录
        cursor.execute(
            "SELECT ch.*, e.company_name FROM credit_history ch LEFT JOIN enterprise e ON ch.enterprise_id=e.id WHERE ch.enterprise_id=%s ORDER BY ch.record_date DESC",
            (ent_id,))
    else:
        # 执行SQL：查询前100条征信记录
        cursor.execute(
            "SELECT ch.*, e.company_name FROM credit_history ch LEFT JOIN enterprise e ON ch.enterprise_id=e.id ORDER BY ch.record_date DESC LIMIT 100")
    # 获取征信记录列表
    records = cursor.fetchall()
    # 执行SQL：查询所有企业（用于筛选下拉框）
    cursor.execute("SELECT id, company_name FROM enterprise")
    # 获取企业列表
    enterprises = cursor.fetchall()
    # 关闭数据库连接
    db.close()
    # 渲染征信记录页面，传递记录、企业列表、选中的企业ID
    return render_template('employee/credit_records.html', records=records, enterprises=enterprises,
                           selected_ent=ent_id)


# 定义员工评估结果路由：URL为/employee/assessment_results，需登录且角色为employee
@app.route('/employee/assessment_results')
@login_required
@role_required('employee')
def employee_assessment_results():
    # 获取数据库连接
    db = get_db()
    # 创建游标
    cursor = db.cursor()
    # 从URL参数获取等级筛选条件
    grade = request.args.get('grade', '')
    # 判断是否有等级筛选
    if grade:
        # 执行SQL：查询指定等级的评估记录
        cursor.execute(
            "SELECT ca.*, e.company_name FROM credit_assessment ca LEFT JOIN enterprise e ON ca.enterprise_id=e.id WHERE ca.grade=%s ORDER BY ca.assess_time DESC",
            (grade,))
    else:
        # 执行SQL：查询前100条评估记录
        cursor.execute(
            "SELECT ca.*, e.company_name FROM credit_assessment ca LEFT JOIN enterprise e ON ca.enterprise_id=e.id ORDER BY ca.assess_time DESC LIMIT 100")
    # 获取评估记录列表
    assessments = cursor.fetchall()
    # 关闭数据库连接
    db.close()
    # 渲染评估结果页面，传递评估记录和选中的等级
    return render_template('employee/assessment_results.html', assessments=assessments, selected_grade=grade)


# 定义员工贷款管理路由：URL为/employee/loan_manage，支持GET和POST，需登录且角色为employee
@app.route('/employee/loan_manage', methods=['GET', 'POST'])
@login_required
@role_required('employee')
def employee_loan_manage():
    # 获取数据库连接
    db = get_db()
    # 创建游标
    cursor = db.cursor()
    # 判断请求方法是否为POST
    if request.method == 'POST':
        # 从表单获取贷款ID
        loan_id = request.form.get('loan_id')
        # 从表单获取操作类型（approve/reject）
        action = request.form.get('action')
        # 处理批准操作
        if action == 'approve':
            # 执行SQL：更新贷款状态为repaying（还款中）
            cursor.execute("UPDATE loan SET status='repaying', approve_time=NOW() WHERE id=%s", (loan_id,))
            # 发送批准成功提示
            flash('贷款已批准')
        # 处理拒绝操作
        elif action == 'reject':
            # 执行SQL：更新贷款状态为rejected（已拒绝）
            cursor.execute("UPDATE loan SET status='rejected', approve_time=NOW() WHERE id=%s", (loan_id,))
            # 发送拒绝成功提示
            flash('贷款已拒绝')
        # 提交事务
        db.commit()
    # 从URL参数获取状态筛选条件
    status = request.args.get('status', '')
    # 判断是否有状态筛选
    if status:
        # 执行SQL：查询指定状态的贷款记录
        cursor.execute(
            "SELECT l.*, e.company_name FROM loan l LEFT JOIN enterprise e ON l.enterprise_id=e.id WHERE l.status=%s ORDER BY l.apply_time DESC",
            (status,))
    else:
        # 执行SQL：查询所有贷款记录
        cursor.execute(
            "SELECT l.*, e.company_name FROM loan l LEFT JOIN enterprise e ON l.enterprise_id=e.id ORDER BY l.apply_time DESC")
    # 获取贷款记录列表
    loans = cursor.fetchall()
    # 关闭数据库连接
    db.close()
    # 渲染贷款管理页面，传递贷款记录和选中的状态
    return render_template('employee/loan_manage.html', loans=loans, selected_status=status)


# 定义员工交易记录路由：URL为/employee/transaction_records，需登录且角色为employee
@app.route('/employee/transaction_records')
@login_required
@role_required('employee')
def employee_transaction_records():
    # 获取数据库连接
    db = get_db()
    # 创建游标
    cursor = db.cursor()
    # 从URL参数获取企业ID筛选条件
    ent_id = request.args.get('enterprise_id', '')
    # 判断是否有企业ID筛选
    if ent_id:
        # 执行SQL：查询指定企业的交易记录
        cursor.execute(
            "SELECT t.*, e.company_name FROM transaction t LEFT JOIN enterprise e ON t.enterprise_id=e.id WHERE t.enterprise_id=%s ORDER BY t.create_time DESC",
            (ent_id,))
    else:
        # 执行SQL：查询前100条交易记录
        cursor.execute(
            "SELECT t.*, e.company_name FROM transaction t LEFT JOIN enterprise e ON t.enterprise_id=e.id ORDER BY t.create_time DESC LIMIT 100")
    # 获取交易记录列表
    transactions = cursor.fetchall()
    # 执行SQL：查询所有企业（用于筛选下拉框）
    cursor.execute("SELECT id, company_name FROM enterprise")
    # 获取企业列表
    enterprises = cursor.fetchall()
    # 关闭数据库连接
    db.close()
    # 渲染交易记录页面，传递交易记录、企业列表、选中的企业ID
    return render_template('employee/transaction_records.html', transactions=transactions, enterprises=enterprises,
                           selected_ent=ent_id)


# 定义员工风险预警路由：URL为/employee/risk_warning，需登录且角色为employee
@app.route('/employee/risk_warning')
@login_required
@role_required('employee')
def employee_risk_warning():
    # 获取数据库连接
    db = get_db()
    # 创建游标
    cursor = db.cursor()

    # 执行SQL：查询高风险企业列表（按评分升序，取前20）
    cursor.execute("""
        SELECT e.id, e.company_name, ca.score, ca.grade, ca.assess_time,
               (SELECT SUM(remaining_amount) FROM loan WHERE enterprise_id=e.id AND status='repaying') as total_debt
        FROM enterprise e
        LEFT JOIN credit_assessment ca ON e.id = ca.enterprise_id
        WHERE ca.id = (SELECT MAX(id) FROM credit_assessment WHERE enterprise_id = e.id)
        ORDER BY ca.score ASC
        LIMIT 20
    """)
    # 获取高风险企业列表
    risk_enterprises = cursor.fetchall()

    # 执行SQL：查询各等级企业数量
    cursor.execute("""
        SELECT ca.grade, COUNT(DISTINCT e.id) as cnt
        FROM enterprise e
        LEFT JOIN credit_assessment ca ON e.id = ca.enterprise_id
        WHERE ca.id = (SELECT MAX(id) FROM credit_assessment WHERE enterprise_id = e.id)
        GROUP BY ca.grade
    """)
    # 获取等级分布数据
    grade_distribution = cursor.fetchall()

    # 执行SQL：查询贷款风险统计
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN status='pending' THEN 1 END) as pending_count,
            COUNT(CASE WHEN status='repaying' THEN 1 END) as repaying_count,
            SUM(CASE WHEN status='repaying' THEN remaining_amount ELSE 0 END) as total_debt,
            SUM(loan_amount) as total_loan
        FROM loan
    """)
    # 获取贷款统计数据
    loan_stats = cursor.fetchone()

    # 执行SQL：查询近30天评估趋势
    cursor.execute("""
        SELECT DATE(assess_time) as date, AVG(score) as avg_score, COUNT(*) as count
        FROM credit_assessment
        WHERE assess_time >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY DATE(assess_time)
        ORDER BY date
    """)
    # 获取评估趋势数据
    assessment_trend = cursor.fetchall()

    # 执行SQL：查询风险预警企业（评分<50）
    cursor.execute("""
        SELECT e.company_name, ca.score, ca.grade, ca.assess_time
        FROM enterprise e
        JOIN credit_assessment ca ON e.id = ca.enterprise_id
        WHERE ca.id = (SELECT MAX(id) FROM credit_assessment WHERE enterprise_id = e.id)
        AND ca.score < 50
        ORDER BY ca.score ASC
    """)
    # 获取预警企业列表
    warning_enterprises = cursor.fetchall()

    # 关闭数据库连接
    db.close()
    # 渲染员工风险预警页面，传递各类风险数据
    return render_template('employee/risk_warning.html',
                           risk_enterprises=risk_enterprises,
                           grade_distribution=grade_distribution,
                           loan_stats=loan_stats,
                           assessment_trend=assessment_trend,
                           warning_enterprises=warning_enterprises)


# ==================== 管理员端路由 ====================
# 定义管理员仪表盘路由：URL为/admin/dashboard，需登录且角色为admin
@app.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    # 获取数据库连接
    db = get_db()
    # 创建游标
    cursor = db.cursor()
    # 执行SQL：查询企业用户数量
    cursor.execute("SELECT COUNT(*) as cnt FROM user WHERE role='enterprise'")
    # 获取企业用户数量
    ent_users = cursor.fetchone()['cnt']
    # 执行SQL：查询员工用户数量
    cursor.execute("SELECT COUNT(*) as cnt FROM user WHERE role='employee'")
    # 获取员工用户数量
    emp_users = cursor.fetchone()['cnt']
    # 执行SQL：查询待审核内容数量
    cursor.execute("SELECT COUNT(*) as cnt FROM content_review WHERE status=0")
    # 获取待审核数量
    pending_reviews = cursor.fetchone()['cnt']
    # 执行SQL：查询总贷款数量
    cursor.execute("SELECT COUNT(*) as cnt FROM loan")
    # 获取总贷款数量
    total_loans = cursor.fetchone()['cnt']
    # 执行SQL：查询总账户余额
    cursor.execute("SELECT SUM(balance) as total FROM account")
    # 获取总账户余额
    total_balance = cursor.fetchone()['total'] or 0
    # 关闭数据库连接
    db.close()
    # 渲染管理员仪表盘，传递各类统计数据
    return render_template('admin/dashboard.html', ent_users=ent_users, emp_users=emp_users,
                           pending_reviews=pending_reviews, total_loans=total_loans, total_balance=total_balance)


# 定义管理员用户管理路由：URL为/admin/user_manage，支持GET和POST，需登录且角色为admin
@app.route('/admin/user_manage', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_user_manage():
    # 获取数据库连接
    db = get_db()
    # 创建游标
    cursor = db.cursor()
    # 判断请求方法是否为POST
    if request.method == 'POST':
        # 从表单获取操作类型（add/edit/delete）
        action = request.form.get('action')
        # 处理添加用户
        if action == 'add':
            # 执行SQL：插入用户记录
            cursor.execute(
                "INSERT INTO user (username, password, name, role, phone, email, status, create_time, update_time) VALUES (%s, %s, %s, %s, %s, %s, 1, NOW(), NOW())",
                (request.form.get('username'), request.form.get('password'), request.form.get('name'),
                 request.form.get('role'), request.form.get('phone'), request.form.get('email')))
            # 发送添加成功提示
            flash('用户添加成功')
        # 处理编辑用户
        elif action == 'edit':
            # 执行SQL：更新用户信息
            cursor.execute(
                "UPDATE user SET name=%s, role=%s, phone=%s, email=%s, status=%s, update_time=NOW() WHERE id=%s", (
                request.form.get('name'), request.form.get('role'), request.form.get('phone'),
                request.form.get('email'), request.form.get('status'), request.form.get('user_id')))
            # 发送更新成功提示
            flash('用户更新成功')
        # 处理删除用户
        elif action == 'delete':
            # 执行SQL：删除用户记录
            cursor.execute("DELETE FROM user WHERE id=%s", (request.form.get('user_id'),))
            # 发送删除成功提示
            flash('用户删除成功')
        # 提交事务
        db.commit()

        if __name__ == '__main__':
            app.run(debug=True, port=5001)