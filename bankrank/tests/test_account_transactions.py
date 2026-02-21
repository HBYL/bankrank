# -*- coding: utf-8 -*-
"""
Property-Based Tests for Account Transactions (Deposit/Withdrawal)

**Property 1: Account Balance Consistency**
**Property 2: Withdrawal Rejection for Insufficient Balance**
**Validates: Requirements 2.2, 2.3, 2.4**

For any virtual account and any sequence of deposit/withdrawal transactions, 
the final balance should equal the initial balance plus all deposits minus all withdrawals.
For any withdrawal attempt where the amount exceeds the current balance, 
the system should reject the transaction and the balance should remain unchanged.
"""

# 导入pytest测试框架，用于编写和执行测试用例
import pytest
# 从hypothesis库导入属性测试核心组件：given(定义测试数据策略)、strategies(生成测试数据)、settings(配置测试运行参数)、assume(过滤无效测试数据)
from hypothesis import given, strategies as st, settings, assume
# 导入Decimal(高精度小数)和ROUND_HALF_UP(四舍五入规则)，解决金融计算浮点精度问题
from decimal import Decimal, ROUND_HALF_UP
# 导入pymysql库，用于连接MySQL数据库执行CRUD操作
import pymysql
# 导入sys库，用于修改Python解释器的系统路径
import sys
# 导入os库，用于处理文件路径和操作系统相关操作
import os

# 将当前文件的父目录添加到Python路径中，确保能导入上级目录的模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 定义数据库连接配置字典，包含连接MySQL所需的所有参数
DB_CONFIG = {
    'host': 'localhost',  # 数据库主机地址（本地）
    'user': 'root',  # 数据库用户名
    'password': '123456',  # 数据库密码
    'database': 'py_bccabusinesssystem',  # 要连接的数据库名
    'charset': 'utf8mb4',  # 字符集（支持所有Unicode字符）
    'cursorclass': pymysql.cursors.DictCursor  # 游标类型（查询结果以字典形式返回）
}


def get_db_connection():
    """Get database connection：获取数据库连接的工具函数"""
    try:
        # 使用pymysql.connect创建数据库连接，解包DB_CONFIG字典作为参数
        connection = pymysql.connect(**DB_CONFIG)
        # 返回创建成功的数据库连接对象
        return connection
    # 捕获pymysql相关异常（如连接失败、认证错误等）
    except pymysql.Error as e:
        # 打印数据库连接错误信息，便于调试
        print(f"Database connection error: {e}")
        # 连接失败时返回None
        return None


def create_test_enterprise_with_account(initial_balance=0.0):
    """Create a test enterprise with virtual account for testing：创建测试用企业及虚拟账户"""
    # 调用get_db_connection获取数据库连接
    connection = get_db_connection()
    # 如果连接失败，返回三个None（user_id/enterprise_id/account_id）
    if not connection:
        return None, None, None

    try:
        # 使用上下文管理器创建游标对象（自动管理游标生命周期）
        with connection.cursor() as cursor:
            # 定义插入测试用户的SQL语句（企业角色，状态启用）
            user_sql = """
                INSERT INTO user (username, password, name, role, status, create_time, update_time)
                VALUES (%s, 'test123', 'Test Enterprise', 'enterprise', 1, NOW(), NOW())
            """
            # 导入time模块，用于生成时间戳（避免用户名重复）
            import time
            # 导入random模块，用于生成随机数（避免用户名重复）
            import random
            # 生成短用户名（避免数据库字段长度限制）：t_ + 时间戳 + 三位随机数
            username = f"t_{int(time.time())}{random.randint(100, 999)}"
            # 执行插入用户SQL，传入用户名参数
            cursor.execute(user_sql, (username,))
            # 获取刚插入用户的ID（自增主键）
            user_id = cursor.lastrowid

            # 定义插入企业信息的SQL语句
            enterprise_sql = """
                INSERT INTO enterprise (user_id, name, create_time, update_time)
                VALUES (%s, 'Test Enterprise Co.', NOW(), NOW())
            """
            # 执行插入企业SQL，传入用户ID参数
            cursor.execute(enterprise_sql, (user_id,))
            # 获取刚插入企业的ID（自增主键）
            enterprise_id = cursor.lastrowid

            # 定义插入虚拟账户的SQL语句（含初始余额）
            account_sql = """
                INSERT INTO virtual_account (enterprise_id, account_no, balance, create_time, update_time)
                VALUES (%s, %s, %s, NOW(), NOW())
            """
            # 生成短账户号（最大20字符）：VA + 时间戳 + 两位随机数
            account_no = f"VA{int(time.time())}{random.randint(10, 99)}"
            # 执行插入账户SQL，传入企业ID、账户号、初始余额参数
            cursor.execute(account_sql, (enterprise_id, account_no, initial_balance))
            # 获取刚插入账户的ID（自增主键）
            account_id = cursor.lastrowid

            # 提交事务（确保所有插入操作生效）
            connection.commit()
            # 返回创建的用户ID、企业ID、账户ID
            return user_id, enterprise_id, account_id
    # 捕获pymysql相关异常（如SQL语法错误、字段长度超限等）
    except pymysql.Error as e:
        # 打印创建测试数据错误信息
        print(f"Create test enterprise error: {e}")
        # 异常时回滚事务（撤销已执行的插入操作）
        connection.rollback()
        # 异常时返回三个None
        return None, None, None
    finally:
        # 无论是否异常，最终关闭数据库连接（释放资源）
        connection.close()


def cleanup_test_data(user_id, enterprise_id, account_id):
    """Clean up test data：清理测试数据（避免污染数据库）"""
    # 获取数据库连接
    connection = get_db_connection()
    # 连接失败则直接返回
    if not connection:
        return

    try:
        # 创建游标对象
        with connection.cursor() as cursor:
            # 删除该账户关联的交易记录（先删子表，避免外键约束）
            if account_id:
                cursor.execute("DELETE FROM transaction_record WHERE account_id = %s", (account_id,))
            # 额外删除该企业关联的交易记录（双重保障）
            if enterprise_id:
                cursor.execute("DELETE FROM transaction_record WHERE enterprise_id = %s", (enterprise_id,))

            # 删除虚拟账户记录
            if account_id:
                cursor.execute("DELETE FROM virtual_account WHERE id = %s", (account_id,))

            # 删除企业记录
            if enterprise_id:
                cursor.execute("DELETE FROM enterprise WHERE id = %s", (enterprise_id,))

            # 删除用户记录
            if user_id:
                cursor.execute("DELETE FROM user WHERE id = %s", (user_id,))

            # 提交删除操作的事务
            connection.commit()
    # 捕获删除数据时的异常
    except pymysql.Error as e:
        # 打印清理数据错误信息
        print(f"Cleanup error: {e}")
        # 异常时回滚事务
        connection.rollback()
    finally:
        # 关闭数据库连接
        connection.close()


def get_account_balance(account_id):
    """Get current account balance：获取账户当前余额"""
    # 获取数据库连接
    connection = get_db_connection()
    # 连接失败返回None
    if not connection:
        return None

    try:
        # 创建游标对象
        with connection.cursor() as cursor:
            # 定义查询账户余额的SQL语句
            sql = "SELECT balance FROM virtual_account WHERE id = %s"
            # 执行查询，传入账户ID参数
            cursor.execute(sql, (account_id,))
            # 获取查询结果（单行）
            result = cursor.fetchone()
            # 有结果则返回浮点型余额，无结果返回None
            return float(result['balance']) if result else None
    # 捕获查询余额时的异常
    except pymysql.Error as e:
        # 打印获取余额错误信息
        print(f"Get balance error: {e}")
        # 异常时返回None
        return None
    finally:
        # 关闭数据库连接
        connection.close()


def deposit(account_id, enterprise_id, amount, remark=''):
    """
    Perform deposit operation：执行存款操作
    Returns: (success: bool, new_balance: float or None)
    """
    # 校验存款金额：必须大于0，否则返回失败
    if amount <= 0:
        return False, None

    # 获取数据库连接
    connection = get_db_connection()
    # 连接失败返回失败
    if not connection:
        return False, None

    try:
        # 创建游标对象
        with connection.cursor() as cursor:
            # 查询当前余额并加行锁（FOR UPDATE：防止并发修改，保证数据一致性）
            cursor.execute("SELECT balance FROM virtual_account WHERE id = %s FOR UPDATE", (account_id,))
            # 获取查询结果
            result = cursor.fetchone()
            # 账户不存在则返回失败
            if not result:
                return False, None

            # 转换当前余额为浮点型
            current_balance = float(result['balance'])
            # 计算新余额：当前余额+存款金额，保留两位小数（金融计算标准）
            new_balance = round(current_balance + amount, 2)

            # 更新账户余额
            cursor.execute(
                "UPDATE virtual_account SET balance = %s, update_time = NOW() WHERE id = %s",
                (new_balance, account_id)
            )

            # 插入交易记录（记录存款操作）
            cursor.execute(
                """INSERT INTO transaction_record 
                   (account_id, enterprise_id, type, amount, balance_after, remark, create_time)
                   VALUES (%s, %s, 'deposit', %s, %s, %s, NOW())""",
                (account_id, enterprise_id, amount, new_balance, remark)
            )

            # 提交事务（确保更新和插入操作生效）
            connection.commit()
            # 返回成功状态和新余额
            return True, new_balance
    # 捕获存款操作异常
    except pymysql.Error as e:
        # 打印存款错误信息
        print(f"Deposit error: {e}")
        # 异常时回滚事务
        connection.rollback()
        # 返回失败状态和None
        return False, None
    finally:
        # 关闭数据库连接
        connection.close()


def withdraw(account_id, enterprise_id, amount, remark=''):
    """
    Perform withdrawal operation：执行取款操作
    Returns: (success: bool, new_balance: float or None, error_reason: str or None)
    """
    # 校验取款金额：必须大于0，否则返回失败并提示无效金额
    if amount <= 0:
        return False, None, "Invalid amount"

    # 获取数据库连接
    connection = get_db_connection()
    # 连接失败返回失败并提示数据库连接失败
    if not connection:
        return False, None, "Database connection failed"

    try:
        # 创建游标对象
        with connection.cursor() as cursor:
            # 查询当前余额并加行锁（FOR UPDATE：防止并发修改）
            cursor.execute("SELECT balance FROM virtual_account WHERE id = %s FOR UPDATE", (account_id,))
            # 获取查询结果
            result = cursor.fetchone()
            # 账户不存在则返回失败并提示账户未找到
            if not result:
                return False, None, "Account not found"

            # 转换当前余额为浮点型
            current_balance = float(result['balance'])

            # 校验余额是否充足：取款金额大于当前余额则拒绝
            if amount > current_balance:
                # 回滚事务（无修改，仅释放锁）
                connection.rollback()
                # 返回失败、原余额、余额不足提示
                return False, current_balance, "Insufficient balance"

            # 计算新余额：当前余额-取款金额，保留两位小数
            new_balance = round(current_balance - amount, 2)

            # 更新账户余额
            cursor.execute(
                "UPDATE virtual_account SET balance = %s, update_time = NOW() WHERE id = %s",
                (new_balance, account_id)
            )

            # 插入交易记录（记录取款操作）
            cursor.execute(
                """INSERT INTO transaction_record 
                   (account_id, enterprise_id, type, amount, balance_after, remark, create_time)
                   VALUES (%s, %s, 'withdraw', %s, %s, %s, NOW())""",
                (account_id, enterprise_id, amount, new_balance, remark)
            )

            # 提交事务
            connection.commit()
            # 返回成功状态、新余额、无错误信息
            return True, new_balance, None
    # 捕获取款操作异常
    except pymysql.Error as e:
        # 打印取款错误信息
        print(f"Withdraw error: {e}")
        # 异常时回滚事务
        connection.rollback()
        # 返回失败、None、异常信息
        return False, None, str(e)
    finally:
        # 关闭数据库连接
        connection.close()


def get_transaction_records(account_id):
    """Get all transaction records for an account：获取账户所有交易记录"""
    # 获取数据库连接
    connection = get_db_connection()
    # 连接失败返回空列表
    if not connection:
        return []

    try:
        # 创建游标对象
        with connection.cursor() as cursor:
            # 定义查询交易记录的SQL（按创建时间升序）
            sql = "SELECT * FROM transaction_record WHERE account_id = %s ORDER BY create_time ASC"
            # 执行查询，传入账户ID参数
            cursor.execute(sql, (account_id,))
            # 返回所有交易记录（列表形式）
            return cursor.fetchall()
    # 捕获查询交易记录异常
    except pymysql.Error as e:
        # 打印查询交易记录错误信息
        print(f"Get transactions error: {e}")
        # 异常时返回空列表
        return []
    finally:
        # 关闭数据库连接
        connection.close()


# 定义有效金额生成策略：正数、最多两位小数、0.01~100000.00之间
amount_strategy = st.floats(
    min_value=0.01,  # 最小值：0.01
    max_value=100000.00,  # 最大值：100000.00
    allow_nan=False,  # 不允许NaN（非数字）
    allow_infinity=False  # 不允许无穷大
).map(lambda x: round(x, 2))  # 映射：保留两位小数

# 定义初始余额生成策略：非负数、最多两位小数、0.0~1000000.00之间
initial_balance_strategy = st.floats(
    min_value=0.0,  # 最小值：0.0
    max_value=1000000.00,  # 最大值：1000000.00
    allow_nan=False,  # 不允许NaN
    allow_infinity=False  # 不允许无穷大
).map(lambda x: round(x, 2))  # 映射：保留两位小数

# 定义交易序列生成策略：列表形式，元素为(交易类型, 金额)，1~10笔交易
transaction_strategy = st.lists(
    st.tuples(
        st.sampled_from(['deposit', 'withdraw']),  # 交易类型：存款/取款随机选择
        amount_strategy  # 交易金额：使用上面定义的金额策略
    ),
    min_size=1,  # 最少1笔交易
    max_size=10  # 最多10笔交易
)


class TestAccountBalanceConsistency:
    """
    Property 1: Account Balance Consistency：账户余额一致性测试类

    Feature: bank-credit-assessment-system, Property 1: Account Balance Consistency
    Validates: Requirements 2.2, 2.3
    """

    # 使用hypothesis装饰器：传入初始余额和交易序列的生成策略
    @given(
        initial_balance=initial_balance_strategy,  # 初始余额参数：使用初始余额生成策略
        transactions=transaction_strategy  # 交易序列参数：使用交易序列生成策略
    )
    # 配置测试运行参数：最大用例数100，无超时限制
    @settings(max_examples=100, deadline=None)
    def test_balance_consistency_after_transactions(self, initial_balance, transactions):
        """
        Property: For any virtual account and any sequence of deposit/withdrawal transactions,
        the final balance should equal the initial balance plus all deposits minus all withdrawals.

        **Feature: bank-credit-assessment-system, Property 1: Account Balance Consistency**
        **Validates: Requirements 2.2, 2.3**
        """
        # 创建测试企业和账户，传入初始余额
        user_id, enterprise_id, account_id = create_test_enterprise_with_account(initial_balance)
        # 过滤无效测试数据：如果创建失败则跳过该用例
        assume(user_id is not None and enterprise_id is not None and account_id is not None)

        try:
            # 初始化预期余额为初始余额
            expected_balance = initial_balance
            # 初始化实际存款总额为0
            actual_deposits = 0.0
            # 初始化实际取款总额为0
            actual_withdrawals = 0.0

            # 遍历交易序列中的每一笔交易
            for tx_type, amount in transactions:
                # 处理存款交易
                if tx_type == 'deposit':
                    # 执行存款操作
                    success, new_balance = deposit(account_id, enterprise_id, amount)
                    # 存款成功时更新统计
                    if success:
                        actual_deposits += amount  # 累加存款金额
                        expected_balance = round(expected_balance + amount, 2)  # 更新预期余额
                # 处理取款交易
                else:  # withdraw
                    # 仅当预期余额足够时尝试取款（过滤无效取款场景）
                    if amount <= expected_balance:
                        # 执行取款操作
                        success, new_balance, error = withdraw(account_id, enterprise_id, amount)
                        # 取款成功时更新统计
                        if success:
                            actual_withdrawals += amount  # 累加取款金额
                            expected_balance = round(expected_balance - amount, 2)  # 更新预期余额

            # 获取账户最终实际余额
            final_balance = get_account_balance(account_id)
            # 断言：能成功获取最终余额
            assert final_balance is not None, "Should be able to get final balance"

            # 计算理论余额：初始余额 + 实际存款 - 实际取款
            calculated_balance = round(initial_balance + actual_deposits - actual_withdrawals, 2)

            # 断言1：最终实际余额 ≈ 预期余额（允许0.01误差，解决浮点精度）
            assert abs(final_balance - expected_balance) < 0.01, \
                f"Final balance {final_balance} should equal expected {expected_balance}"
            # 断言2：最终实际余额 ≈ 理论余额（允许0.01误差）
            assert abs(final_balance - calculated_balance) < 0.01, \
                f"Final balance {final_balance} should equal calculated {calculated_balance}"

        finally:
            # 无论测试是否通过，最终清理测试数据
            cleanup_test_data(user_id, enterprise_id, account_id)

    # 使用hypothesis装饰器：传入存款金额生成策略
    @given(
        deposit_amount=amount_strategy  # 存款金额参数：使用金额生成策略
    )
    # 配置测试运行参数：最大用例数100，无超时限制
    @settings(max_examples=100, deadline=None)
    def test_single_deposit_increases_balance(self, deposit_amount):
        """
        Property: For any deposit, the balance should increase by exactly the deposit amount.

        **Feature: bank-credit-assessment-system, Property 1: Account Balance Consistency**
        **Validates: Requirements 2.2**
        """
        # 固定初始余额为100.00
        initial_balance = 100.00
        # 创建测试企业和账户
        user_id, enterprise_id, account_id = create_test_enterprise_with_account(initial_balance)
        # 过滤无效测试数据
        assume(user_id is not None and enterprise_id is not None and account_id is not None)

        try:
            # 执行存款操作
            success, new_balance = deposit(account_id, enterprise_id, deposit_amount)
            # 断言：存款操作成功
            assert success, "Deposit should succeed"

            # 计算预期余额：初始余额 + 存款金额
            expected_balance = round(initial_balance + deposit_amount, 2)
            # 获取账户最终实际余额
            final_balance = get_account_balance(account_id)

            # 断言：最终余额 ≈ 预期余额（允许0.01误差）
            assert abs(final_balance - expected_balance) < 0.01, \
                f"Balance after deposit {final_balance} should be {expected_balance}"

        finally:
            # 清理测试数据
            cleanup_test_data(user_id, enterprise_id, account_id)


class TestWithdrawalRejection:
    """
    Property 2: Withdrawal Rejection for Insufficient Balance：取款余额不足拒绝测试类

    Feature: bank-credit-assessment-system, Property 2: Withdrawal Rejection for Insufficient Balance
    Validates: Requirements 2.4
    """

    # 使用hypothesis装饰器：传入初始余额和取款金额生成策略
    @given(
        initial_balance=st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False).map(
            lambda x: round(x, 2)),  # 初始余额：0.0~1000.0
        withdrawal_amount=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False).map(
            lambda x: round(x, 2))  # 取款金额：0.01~10000.0
    )
    # 配置测试运行参数：最大用例数100，无超时限制
    @settings(max_examples=100, deadline=None)
    def test_withdrawal_rejected_when_insufficient_balance(self, initial_balance, withdrawal_amount):
        """
        Property: For any withdrawal attempt where the amount exceeds the current balance,
        the system should reject the transaction and the balance should remain unchanged.

        **Feature: bank-credit-assessment-system, Property 2: Withdrawal Rejection for Insufficient Balance**
        **Validates: Requirements 2.4**
        """
        # 过滤测试数据：仅保留取款金额 > 初始余额的场景
        assume(withdrawal_amount > initial_balance)

        # 创建测试企业和账户
        user_id, enterprise_id, account_id = create_test_enterprise_with_account(initial_balance)
        # 过滤无效测试数据
        assume(user_id is not None and enterprise_id is not None and account_id is not None)

        try:
            # 尝试执行取款操作（金额超出余额）
            success, returned_balance, error = withdraw(account_id, enterprise_id, withdrawal_amount)

            # 断言1：取款操作失败
            assert not success, "Withdrawal should be rejected when amount exceeds balance"
            # 断言2：错误原因是"余额不足"
            assert error == "Insufficient balance", f"Error should indicate insufficient balance, got: {error}"

            # 获取账户最终实际余额
            final_balance = get_account_balance(account_id)
            # 断言3：最终余额 ≈ 初始余额（余额未变化）
            assert abs(final_balance - initial_balance) < 0.01, \
                f"Balance {final_balance} should remain unchanged at {initial_balance} after rejected withdrawal"

        finally:
            # 清理测试数据
            cleanup_test_data(user_id, enterprise_id, account_id)

    # 使用hypothesis装饰器：传入初始余额和取款金额生成策略
    @given(
        initial_balance=st.floats(min_value=100.0, max_value=10000.0, allow_nan=False, allow_infinity=False).map(
            lambda x: round(x, 2)),  # 初始余额：100.0~10000.0
        withdrawal_amount=st.floats(min_value=0.01, max_value=99.99, allow_nan=False, allow_infinity=False).map(
            lambda x: round(x, 2))  # 取款金额：0.01~99.99
    )
    # 配置测试运行参数：最大用例数100，无超时限制
    @settings(max_examples=100, deadline=None)
    def test_withdrawal_succeeds_when_sufficient_balance(self, initial_balance, withdrawal_amount):
        """
        Property: For any withdrawal where amount is less than or equal to balance,
        the withdrawal should succeed and balance should decrease by the withdrawal amount.

        **Feature: bank-credit-assessment-system, Property 2: Withdrawal Rejection for Insufficient Balance**
        **Validates: Requirements 2.3, 2.4**
        """
        # 过滤测试数据：仅保留取款金额 ≤ 初始余额的场景
        assume(withdrawal_amount <= initial_balance)

        # 创建测试企业和账户
        user_id, enterprise_id, account_id = create_test_enterprise_with_account(initial_balance)
        # 过滤无效测试数据
        assume(user_id is not None and enterprise_id is not None and account_id is not None)

        try:
            # 尝试执行有效取款操作
            success, new_balance, error = withdraw(account_id, enterprise_id, withdrawal_amount)

            # 断言1：取款操作成功
            assert success, f"Withdrawal should succeed when amount {withdrawal_amount} <= balance {initial_balance}"
            # 断言2：无错误信息返回
            assert error is None, "No error should be returned for successful withdrawal"

            # 计算预期余额：初始余额 - 取款金额
            expected_balance = round(initial_balance - withdrawal_amount, 2)
            # 获取账户最终实际余额
            final_balance = get_account_balance(account_id)

            # 断言3：最终余额 ≈ 预期余额（允许0.01误差）
            assert abs(final_balance - expected_balance) < 0.01, \
                f"Balance {final_balance} should be {expected_balance} after withdrawal of {withdrawal_amount}"

        finally:
            # 清理测试数据
            cleanup_test_data(user_id, enterprise_id, account_id)


# 主程序入口：当脚本直接运行时执行pytest测试
if __name__ == '__main__':
    # 调用pytest.main执行测试：-v（详细输出）、--tb=short（简短异常追踪）
    pytest.main([__file__, '-v', '--tb=short'])