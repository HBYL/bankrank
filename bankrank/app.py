from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import pymysql
import os
from datetime import datetime
import json
import requests

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
    debt_ratio = float(data.get('debt_ratio', 50))
    if debt_ratio < 30: scores['debt'] = 7
    elif debt_ratio < 50: scores['debt'] = 5
    elif debt_ratio < 70: scores['debt'] = 3
    else: scores['debt'] = 1
    
    # 3. 现金流评分 (0-7分)
    cashflow_scores = {'excellent': 7, 'good': 5, 'normal': 3, 'poor': 1}
    scores['cashflow'] = cashflow_scores.get(data.get('cash_flow', 'normal'), 3)
    
    # 4. 诉讼记录评分 (0-7分)
    litigation = int(data.get('litigation_count', 0))
    if litigation == 0: scores['litigation'] = 7
    elif litigation <= 2: scores['litigation'] = 5
    elif litigation <= 5: scores['litigation'] = 2
    else: scores['litigation'] = 0
    
    # 5. 企业成立年限 (0-7分)
    years = int(data.get('company_years', 3))
    if years >= 10: scores['years'] = 7
    elif years >= 5: scores['years'] = 5
    elif years >= 3: scores['years'] = 3
    else: scores['years'] = 1
    
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
    if total_score >= 80: grade = 'A'
    elif total_score >= 60: grade = 'B'
    elif total_score >= 40: grade = 'C'
    else: grade = 'D'
    
    # 计算风险预警指标
    risk_indicators = calculate_risk_indicators(data, scores, total_score)
    
    return total_score, grade, scores, risk_indicators

# 风险预警指标计算
def calculate_risk_indicators(data, scores, total_score):
    indicators = {
        'overall_risk': 'low' if total_score >= 70 else ('medium' if total_score >= 50 else 'high'),
        'financial_risk': 'low' if scores.get('debt', 0) + scores.get('cashflow', 0) + scores.get('profit', 0) >= 15 else ('medium' if scores.get('debt', 0) + scores.get('cashflow', 0) + scores.get('profit', 0) >= 10 else 'high'),
        'legal_risk': 'low' if scores.get('litigation', 0) >= 5 else ('medium' if scores.get('litigation', 0) >= 2 else 'high'),
        'operational_risk': 'low' if scores.get('supply_chain', 0) + scores.get('market_position', 0) >= 8 else ('medium' if scores.get('supply_chain', 0) + scores.get('market_position', 0) >= 5 else 'high'),
        'credit_risk': 'low' if scores.get('bank_credit', 0) + scores.get('tax_credit', 0) >= 10 else ('medium' if scores.get('bank_credit', 0) + scores.get('tax_credit', 0) >= 6 else 'high'),
    }
    return indicators

# AI咨询回答函数 - 使用火山引擎API
def get_ai_response(question):
    # 业务关键词过滤
    business_keywords = ['信用', '评估', '贷款', '还款', '征信', '上传', '营业执照', '企业信息', '存款', '取款', '账户', '利率', '审核', '评分', '银行', '企业', '资金', '申请', '审批']
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
        if role == 'admin': return redirect(url_for('admin_dashboard'))
        elif role == 'employee': return redirect(url_for('employee_dashboard'))
        else: return redirect(url_for('enterprise_dashboard'))
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
            if user['role'] == 'admin': return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'employee': return redirect(url_for('employee_dashboard'))
            else: return redirect(url_for('enterprise_dashboard'))
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
        cursor.execute("INSERT INTO user (username, password, name, role, phone, email, status, create_time, update_time) VALUES (%s, %s, %s, 'enterprise', %s, %s, 1, NOW(), NOW())", (username, password, name, phone, email))
        user_id = cursor.lastrowid
        cursor.execute("INSERT INTO enterprise (user_id, company_name, create_time, update_time) VALUES (%s, %s, NOW(), NOW())", (user_id, name))
        enterprise_id = cursor.lastrowid
        account_no = f"6222{str(enterprise_id).zfill(12)}"
        cursor.execute("INSERT INTO account (enterprise_id, account_no, balance, create_time, update_time) VALUES (%s, %s, 0, NOW(), NOW())", (enterprise_id, account_no))
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
    cursor.execute("SELECT COUNT(*) as cnt, SUM(remaining_amount) as total FROM loan WHERE enterprise_id=%s AND status='repaying'", (ent_id,))
    loan_info = cursor.fetchone()
    cursor.execute("SELECT score, grade FROM credit_assessment WHERE enterprise_id=%s ORDER BY assess_time DESC LIMIT 1", (ent_id,))
    credit = cursor.fetchone()
    db.close()
    return render_template('enterprise/dashboard.html', balance=balance, loan_count=loan_info['cnt'] or 0, loan_total=loan_info['total'] or 0, credit=credit)

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
        amount = float(request.form.get('amount', 0))
        remark = request.form.get('remark', '')
        if amount <= 0:
            flash('金额必须大于0')
        elif action == 'withdraw' and amount > account['balance']:
            flash('余额不足')
        else:
            new_balance = account['balance'] + amount if action == 'deposit' else account['balance'] - amount
            cursor.execute("UPDATE account SET balance=%s, update_time=NOW() WHERE id=%s", (new_balance, account['id']))
            trans_type = 'deposit' if action == 'deposit' else 'withdraw'
            cursor.execute("INSERT INTO transaction (account_id, enterprise_id, trans_type, amount, balance_after, remark, create_time) VALUES (%s, %s, %s, %s, %s, %s, NOW())", (account['id'], ent_id, trans_type, amount, new_balance, remark))
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
            amount = float(request.form.get('loan_amount', 0))
            term = int(request.form.get('loan_term', 12))
            loan_no = f"LN{datetime.now().strftime('%Y%m%d%H%M%S')}"
            cursor.execute("INSERT INTO loan (enterprise_id, loan_no, loan_amount, interest_rate, loan_term, remaining_amount, status, apply_time, create_time) VALUES (%s, %s, %s, 4.35, %s, %s, 'pending', NOW(), NOW())", (ent_id, loan_no, amount, term, amount))
            db.commit()
            flash('贷款申请已提交')
        elif action == 'repay':
            loan_id = request.form.get('loan_id')
            repay_amount = float(request.form.get('repay_amount', 0))
            cursor.execute("SELECT * FROM loan WHERE id=%s AND enterprise_id=%s", (loan_id, ent_id))
            loan = cursor.fetchone()
            if loan and repay_amount > 0:
                interest = repay_amount * 0.1
                principal = repay_amount - interest
                new_remaining = max(0, loan['remaining_amount'] - principal)
                new_status = 'completed' if new_remaining == 0 else 'repaying'
                cursor.execute("UPDATE loan SET remaining_amount=%s, status=%s WHERE id=%s", (new_remaining, new_status, loan_id))
                cursor.execute("INSERT INTO repayment (loan_id, enterprise_id, repay_amount, principal, interest, repay_date, status, actual_repay_time, create_time) VALUES (%s, %s, %s, %s, %s, CURDATE(), 'paid', NOW(), NOW())", (loan_id, ent_id, repay_amount, principal, interest))
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
            cursor.execute("UPDATE enterprise SET company_name=%s, credit_code=%s, legal_person=%s, registered_capital=%s, industry=%s, address=%s, update_time=NOW() WHERE user_id=%s", (company_name, credit_code, legal_person, registered_capital, industry, address, session['user_id']))
            if 'business_license' in request.files:
                file = request.files['business_license']
                if file and file.filename:
                    filename = f"license_{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    cursor.execute("UPDATE enterprise SET business_license=%s, license_status=0 WHERE user_id=%s", (filename, session['user_id']))
                    cursor.execute("INSERT INTO content_review (enterprise_id, content_type, content_path, status, create_time) VALUES (%s, 'license', %s, 0, NOW())", (enterprise['id'], filename))
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
    cursor.execute("SELECT * FROM credit_assessment WHERE enterprise_id=%s ORDER BY assess_time DESC LIMIT 1", (ent_id,))
    latest = cursor.fetchone()
    cursor.execute("SELECT score, assess_time FROM credit_assessment WHERE enterprise_id=%s ORDER BY assess_time DESC LIMIT 12", (ent_id,))
    history = cursor.fetchall()
    cursor.execute("SELECT grade, COUNT(*) as cnt FROM credit_assessment GROUP BY grade")
    grade_dist = cursor.fetchall()
    cursor.execute("SELECT AVG(score) as avg_score FROM credit_assessment")
    avg = cursor.fetchone()
    # 获取风险预警数据
    cursor.execute("SELECT questionnaire_data FROM credit_assessment WHERE enterprise_id=%s ORDER BY assess_time DESC LIMIT 1", (ent_id,))
    latest_data = cursor.fetchone()
    risk_indicators = None
    if latest_data and latest_data.get('questionnaire_data'):
        try:
            data = json.loads(latest_data['questionnaire_data']) if isinstance(latest_data['questionnaire_data'], str) else latest_data['questionnaire_data']
            _, _, scores, risk_indicators = calculate_credit_score(data)
        except:
            risk_indicators = None
    db.close()
    return render_template('enterprise/credit_visual.html', latest=latest, history=list(reversed(history)), grade_dist=grade_dist, avg_score=avg['avg_score'] or 0, risk_indicators=risk_indicators)

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
    cursor.execute("SELECT * FROM credit_assessment WHERE enterprise_id=%s ORDER BY assess_time DESC LIMIT 1", (ent_id,))
    latest = cursor.fetchone()
    
    # 获取历史评估趋势
    cursor.execute("SELECT score, grade, assess_time FROM credit_assessment WHERE enterprise_id=%s ORDER BY assess_time DESC LIMIT 12", (ent_id,))
    history = cursor.fetchall()
    
    # 获取贷款风险数据
    cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN status='repaying' THEN remaining_amount ELSE 0 END) as debt FROM loan WHERE enterprise_id=%s", (ent_id,))
    loan_risk = cursor.fetchone()
    
    # 获取交易波动数据
    cursor.execute("SELECT DATE(create_time) as date, SUM(CASE WHEN trans_type='deposit' THEN amount ELSE -amount END) as net_flow FROM transaction WHERE enterprise_id=%s AND create_time >= DATE_SUB(NOW(), INTERVAL 30 DAY) GROUP BY DATE(create_time) ORDER BY date", (ent_id,))
    cash_flow = cursor.fetchall()
    
    # 计算风险指标
    risk_indicators = None
    if latest and latest.get('questionnaire_data'):
        try:
            data = json.loads(latest['questionnaire_data']) if isinstance(latest['questionnaire_data'], str) else latest['questionnaire_data']
            _, _, scores, risk_indicators = calculate_credit_score(data)
        except:
            risk_indicators = {'overall_risk': 'medium', 'financial_risk': 'medium', 'legal_risk': 'low', 'operational_risk': 'medium', 'credit_risk': 'medium'}
    
    db.close()
    return render_template('enterprise/risk_warning.html', latest=latest, history=list(reversed(history)), loan_risk=loan_risk, cash_flow=cash_flow, risk_indicators=risk_indicators)

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
        cursor.execute("INSERT INTO credit_assessment (enterprise_id, score, grade, industry_score, debt_score, cashflow_score, litigation_score, questionnaire_data, assess_time, create_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())", 
            (enterprise['id'], score, grade, scores.get('industry', 0), scores.get('debt', 0), scores.get('cashflow', 0), scores.get('litigation', 0), json.dumps(data)))
        db.commit()
        result = {'score': score, 'grade': grade, 'scores': scores, 'risk_indicators': risk_indicators}
        flash(f'评估完成！您的信用评分为{score}分，等级为{grade}')
    cursor.execute("SELECT * FROM credit_assessment WHERE enterprise_id=%s ORDER BY assess_time DESC LIMIT 5", (enterprise['id'],))
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
            cursor.execute("INSERT INTO ai_consultation (enterprise_id, question, answer, create_time) VALUES (%s, %s, %s, NOW())", (ent['id'], question, answer))
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
    cursor.execute("SELECT grade, COUNT(*) as cnt FROM credit_assessment ca INNER JOIN (SELECT enterprise_id, MAX(assess_time) as max_time FROM credit_assessment GROUP BY enterprise_id) latest ON ca.enterprise_id=latest.enterprise_id AND ca.assess_time=latest.max_time GROUP BY grade")
    grade_stats = cursor.fetchall()
    db.close()
    return render_template('employee/dashboard.html', ent_count=ent_count, pending_loans=pending_loans, active_loans=active_loans, total_loan=total_loan, grade_stats=grade_stats)

@app.route('/employee/enterprise_list')
@login_required
@role_required('employee')
def employee_enterprise_list():
    db = get_db()
    cursor = db.cursor()
    search = request.args.get('search', '')
    if search:
        cursor.execute("SELECT e.*, u.phone, u.email FROM enterprise e LEFT JOIN user u ON e.user_id=u.id WHERE e.company_name LIKE %s OR e.credit_code LIKE %s", (f'%{search}%', f'%{search}%'))
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
        cursor.execute("SELECT ch.*, e.company_name FROM credit_history ch LEFT JOIN enterprise e ON ch.enterprise_id=e.id WHERE ch.enterprise_id=%s ORDER BY ch.record_date DESC", (ent_id,))
    else:
        cursor.execute("SELECT ch.*, e.company_name FROM credit_history ch LEFT JOIN enterprise e ON ch.enterprise_id=e.id ORDER BY ch.record_date DESC LIMIT 100")
    records = cursor.fetchall()
    cursor.execute("SELECT id, company_name FROM enterprise")
    enterprises = cursor.fetchall()
    db.close()
    return render_template('employee/credit_records.html', records=records, enterprises=enterprises, selected_ent=ent_id)

@app.route('/employee/assessment_results')
@login_required
@role_required('employee')
def employee_assessment_results():
    db = get_db()
    cursor = db.cursor()
    grade = request.args.get('grade', '')
    if grade:
        cursor.execute("SELECT ca.*, e.company_name FROM credit_assessment ca LEFT JOIN enterprise e ON ca.enterprise_id=e.id WHERE ca.grade=%s ORDER BY ca.assess_time DESC", (grade,))
    else:
        cursor.execute("SELECT ca.*, e.company_name FROM credit_assessment ca LEFT JOIN enterprise e ON ca.enterprise_id=e.id ORDER BY ca.assess_time DESC LIMIT 100")
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
        cursor.execute("SELECT l.*, e.company_name FROM loan l LEFT JOIN enterprise e ON l.enterprise_id=e.id WHERE l.status=%s ORDER BY l.apply_time DESC", (status,))
    else:
        cursor.execute("SELECT l.*, e.company_name FROM loan l LEFT JOIN enterprise e ON l.enterprise_id=e.id ORDER BY l.apply_time DESC")
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
        cursor.execute("SELECT t.*, e.company_name FROM transaction t LEFT JOIN enterprise e ON t.enterprise_id=e.id WHERE t.enterprise_id=%s ORDER BY t.create_time DESC", (ent_id,))
    else:
        cursor.execute("SELECT t.*, e.company_name FROM transaction t LEFT JOIN enterprise e ON t.enterprise_id=e.id ORDER BY t.create_time DESC LIMIT 100")
    transactions = cursor.fetchall()
    cursor.execute("SELECT id, company_name FROM enterprise")
    enterprises = cursor.fetchall()
    db.close()
    return render_template('employee/transaction_records.html', transactions=transactions, enterprises=enterprises, selected_ent=ent_id)

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
    return render_template('admin/dashboard.html', ent_users=ent_users, emp_users=emp_users, pending_reviews=pending_reviews, total_loans=total_loans, total_balance=total_balance)

@app.route('/admin/user_manage', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_user_manage():
    db = get_db()
    cursor = db.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            cursor.execute("INSERT INTO user (username, password, name, role, phone, email, status, create_time, update_time) VALUES (%s, %s, %s, %s, %s, %s, 1, NOW(), NOW())", (request.form.get('username'), request.form.get('password'), request.form.get('name'), request.form.get('role'), request.form.get('phone'), request.form.get('email')))
            flash('用户添加成功')
        elif action == 'edit':
            cursor.execute("UPDATE user SET name=%s, role=%s, phone=%s, email=%s, status=%s, update_time=NOW() WHERE id=%s", (request.form.get('name'), request.form.get('role'), request.form.get('phone'), request.form.get('email'), request.form.get('status'), request.form.get('user_id')))
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
        cursor.execute("UPDATE content_review SET status=%s, review_comment=%s, reviewer_id=%s, review_time=NOW() WHERE id=%s", (status, comment, session['user_id'], review_id))
        cursor.execute("SELECT enterprise_id, content_type FROM content_review WHERE id=%s", (review_id,))
        review = cursor.fetchone()
        if review and review['content_type'] == 'license':
            cursor.execute("UPDATE enterprise SET license_status=%s, review_comment=%s WHERE id=%s", (status, comment, review['enterprise_id']))
        db.commit()
        flash('审核完成')
    status_filter = request.args.get('status', '0')
    cursor.execute("SELECT cr.*, e.company_name FROM content_review cr LEFT JOIN enterprise e ON cr.enterprise_id=e.id WHERE cr.status=%s ORDER BY cr.create_time DESC", (status_filter,))
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
            cursor.execute("INSERT INTO external_link (link_name, link_url, link_type, status, create_time, update_time) VALUES (%s, %s, %s, 1, NOW(), NOW())", (request.form.get('link_name'), request.form.get('link_url'), request.form.get('link_type')))
            flash('链接添加成功')
        elif action == 'edit':
            cursor.execute("UPDATE external_link SET link_name=%s, link_url=%s, link_type=%s, status=%s, update_time=NOW() WHERE id=%s", (request.form.get('link_name'), request.form.get('link_url'), request.form.get('link_type'), request.form.get('status'), request.form.get('link_id')))
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
            cursor.execute("INSERT INTO enterprise (user_id, company_name, credit_code, legal_person, registered_capital, industry, address, license_status, create_time, update_time) VALUES (%s, %s, %s, %s, %s, %s, %s, 0, NOW(), NOW())", (request.form.get('user_id'), request.form.get('company_name'), request.form.get('credit_code'), request.form.get('legal_person'), request.form.get('registered_capital'), request.form.get('industry'), request.form.get('address')))
            flash('企业添加成功')
        elif action == 'edit':
            cursor.execute("UPDATE enterprise SET company_name=%s, credit_code=%s, legal_person=%s, registered_capital=%s, industry=%s, address=%s, license_status=%s, update_time=NOW() WHERE id=%s", (request.form.get('company_name'), request.form.get('credit_code'), request.form.get('legal_person'), request.form.get('registered_capital'), request.form.get('industry'), request.form.get('address'), request.form.get('license_status'), request.form.get('enterprise_id')))
            flash('企业更新成功')
        elif action == 'delete':
            cursor.execute("DELETE FROM enterprise WHERE id=%s", (request.form.get('enterprise_id'),))
            flash('企业删除成功')
        db.commit()
    search = request.args.get('search', '')
    if search:
        cursor.execute("SELECT * FROM enterprise WHERE company_name LIKE %s OR credit_code LIKE %s ORDER BY id DESC", (f'%{search}%', f'%{search}%'))
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
            cursor.execute("INSERT INTO transaction (account_id, enterprise_id, trans_type, amount, balance_after, remark, create_time) VALUES (%s, %s, %s, %s, %s, %s, NOW())", (request.form.get('account_id'), request.form.get('enterprise_id'), request.form.get('trans_type'), request.form.get('amount'), request.form.get('balance_after'), request.form.get('remark')))
            flash('交易添加成功')
        elif action == 'edit':
            cursor.execute("UPDATE transaction SET trans_type=%s, amount=%s, balance_after=%s, remark=%s WHERE id=%s", (request.form.get('trans_type'), request.form.get('amount'), request.form.get('balance_after'), request.form.get('remark'), request.form.get('trans_id')))
            flash('交易更新成功')
        elif action == 'delete':
            cursor.execute("DELETE FROM transaction WHERE id=%s", (request.form.get('trans_id'),))
            flash('交易删除成功')
        db.commit()
    ent_id = request.args.get('enterprise_id', '')
    if ent_id:
        cursor.execute("SELECT t.*, e.company_name FROM transaction t LEFT JOIN enterprise e ON t.enterprise_id=e.id WHERE t.enterprise_id=%s ORDER BY t.create_time DESC", (ent_id,))
    else:
        cursor.execute("SELECT t.*, e.company_name FROM transaction t LEFT JOIN enterprise e ON t.enterprise_id=e.id ORDER BY t.create_time DESC LIMIT 200")
    transactions = cursor.fetchall()
    cursor.execute("SELECT id, company_name FROM enterprise")
    enterprises = cursor.fetchall()
    db.close()
    return render_template('admin/transaction_data.html', transactions=transactions, enterprises=enterprises, selected_ent=ent_id)

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
            cursor.execute("INSERT INTO loan (enterprise_id, loan_no, loan_amount, interest_rate, loan_term, remaining_amount, status, apply_time, create_time) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())", (request.form.get('enterprise_id'), loan_no, request.form.get('loan_amount'), request.form.get('interest_rate'), request.form.get('loan_term'), request.form.get('loan_amount'), request.form.get('status')))
            flash('贷款添加成功')
        elif action == 'edit':
            cursor.execute("UPDATE loan SET loan_amount=%s, interest_rate=%s, loan_term=%s, remaining_amount=%s, status=%s WHERE id=%s", (request.form.get('loan_amount'), request.form.get('interest_rate'), request.form.get('loan_term'), request.form.get('remaining_amount'), request.form.get('status'), request.form.get('loan_id')))
            flash('贷款更新成功')
        elif action == 'delete':
            cursor.execute("DELETE FROM loan WHERE id=%s", (request.form.get('loan_id'),))
            flash('贷款删除成功')
        db.commit()
    status = request.args.get('status', '')
    if status:
        cursor.execute("SELECT l.*, e.company_name FROM loan l LEFT JOIN enterprise e ON l.enterprise_id=e.id WHERE l.status=%s ORDER BY l.create_time DESC", (status,))
    else:
        cursor.execute("SELECT l.*, e.company_name FROM loan l LEFT JOIN enterprise e ON l.enterprise_id=e.id ORDER BY l.create_time DESC")
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
            cursor.execute("INSERT INTO repayment (loan_id, enterprise_id, repay_amount, principal, interest, repay_date, status, create_time) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())", (request.form.get('loan_id'), request.form.get('enterprise_id'), request.form.get('repay_amount'), request.form.get('principal'), request.form.get('interest'), request.form.get('repay_date'), request.form.get('status')))
            flash('还款记录添加成功')
        elif action == 'edit':
            cursor.execute("UPDATE repayment SET repay_amount=%s, principal=%s, interest=%s, repay_date=%s, status=%s WHERE id=%s", (request.form.get('repay_amount'), request.form.get('principal'), request.form.get('interest'), request.form.get('repay_date'), request.form.get('status'), request.form.get('repay_id')))
            flash('还款记录更新成功')
        elif action == 'delete':
            cursor.execute("DELETE FROM repayment WHERE id=%s", (request.form.get('repay_id'),))
            flash('还款记录删除成功')
        db.commit()
    loan_id = request.args.get('loan_id', '')
    if loan_id:
        cursor.execute("SELECT r.*, e.company_name, l.loan_no FROM repayment r LEFT JOIN enterprise e ON r.enterprise_id=e.id LEFT JOIN loan l ON r.loan_id=l.id WHERE r.loan_id=%s ORDER BY r.create_time DESC", (loan_id,))
    else:
        cursor.execute("SELECT r.*, e.company_name, l.loan_no FROM repayment r LEFT JOIN enterprise e ON r.enterprise_id=e.id LEFT JOIN loan l ON r.loan_id=l.id ORDER BY r.create_time DESC LIMIT 200")
    repayments = cursor.fetchall()
    cursor.execute("SELECT id, loan_no FROM loan")
    loans = cursor.fetchall()
    cursor.execute("SELECT id, company_name FROM enterprise")
    enterprises = cursor.fetchall()
    db.close()
    return render_template('admin/repayment_data.html', repayments=repayments, loans=loans, enterprises=enterprises, selected_loan=loan_id)

@app.route('/admin/assessment_data', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_assessment_data():
    db = get_db()
    cursor = db.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            cursor.execute("INSERT INTO credit_assessment (enterprise_id, score, grade, industry_score, debt_score, cashflow_score, litigation_score, assess_time, create_time) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())", (request.form.get('enterprise_id'), request.form.get('score'), request.form.get('grade'), request.form.get('industry_score'), request.form.get('debt_score'), request.form.get('cashflow_score'), request.form.get('litigation_score')))
            flash('评估记录添加成功')
        elif action == 'edit':
            cursor.execute("UPDATE credit_assessment SET score=%s, grade=%s, industry_score=%s, debt_score=%s, cashflow_score=%s, litigation_score=%s WHERE id=%s", (request.form.get('score'), request.form.get('grade'), request.form.get('industry_score'), request.form.get('debt_score'), request.form.get('cashflow_score'), request.form.get('litigation_score'), request.form.get('assess_id')))
            flash('评估记录更新成功')
        elif action == 'delete':
            cursor.execute("DELETE FROM credit_assessment WHERE id=%s", (request.form.get('assess_id'),))
            flash('评估记录删除成功')
        db.commit()
    grade = request.args.get('grade', '')
    if grade:
        cursor.execute("SELECT ca.*, e.company_name FROM credit_assessment ca LEFT JOIN enterprise e ON ca.enterprise_id=e.id WHERE ca.grade=%s ORDER BY ca.assess_time DESC", (grade,))
    else:
        cursor.execute("SELECT ca.*, e.company_name FROM credit_assessment ca LEFT JOIN enterprise e ON ca.enterprise_id=e.id ORDER BY ca.assess_time DESC LIMIT 200")
    assessments = cursor.fetchall()
    cursor.execute("SELECT id, company_name FROM enterprise")
    enterprises = cursor.fetchall()
    db.close()
    return render_template('admin/assessment_data.html', assessments=assessments, enterprises=enterprises, selected_grade=grade)

@app.route('/admin/credit_history_data', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_credit_history_data():
    db = get_db()
    cursor = db.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            cursor.execute("INSERT INTO credit_history (enterprise_id, record_type, record_source, record_content, record_date, create_time) VALUES (%s, %s, %s, %s, %s, NOW())", (request.form.get('enterprise_id'), request.form.get('record_type'), request.form.get('record_source'), request.form.get('record_content'), request.form.get('record_date')))
            flash('征信记录添加成功')
        elif action == 'edit':
            cursor.execute("UPDATE credit_history SET record_type=%s, record_source=%s, record_content=%s, record_date=%s WHERE id=%s", (request.form.get('record_type'), request.form.get('record_source'), request.form.get('record_content'), request.form.get('record_date'), request.form.get('record_id')))
            flash('征信记录更新成功')
        elif action == 'delete':
            cursor.execute("DELETE FROM credit_history WHERE id=%s", (request.form.get('record_id'),))
            flash('征信记录删除成功')
        db.commit()
    ent_id = request.args.get('enterprise_id', '')
    if ent_id:
        cursor.execute("SELECT ch.*, e.company_name FROM credit_history ch LEFT JOIN enterprise e ON ch.enterprise_id=e.id WHERE ch.enterprise_id=%s ORDER BY ch.record_date DESC", (ent_id,))
    else:
        cursor.execute("SELECT ch.*, e.company_name FROM credit_history ch LEFT JOIN enterprise e ON ch.enterprise_id=e.id ORDER BY ch.record_date DESC LIMIT 200")
    records = cursor.fetchall()
    cursor.execute("SELECT id, company_name FROM enterprise")
    enterprises = cursor.fetchall()
    db.close()
    return render_template('admin/credit_history_data.html', records=records, enterprises=enterprises, selected_ent=ent_id)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
