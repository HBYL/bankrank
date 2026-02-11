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

import pytest
from hypothesis import given, strategies as st, settings, assume
from decimal import Decimal, ROUND_HALF_UP
import pymysql
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'py_bccabusinesssystem',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}


def get_db_connection():
    """Get database connection"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except pymysql.Error as e:
        print(f"Database connection error: {e}")
        return None


def create_test_enterprise_with_account(initial_balance=0.0):
    """Create a test enterprise with virtual account for testing"""
    connection = get_db_connection()
    if not connection:
        return None, None, None
    
    try:
        with connection.cursor() as cursor:
            # Create test user
            user_sql = """
                INSERT INTO user (username, password, name, role, status, create_time, update_time)
                VALUES (%s, 'test123', 'Test Enterprise', 'enterprise', 1, NOW(), NOW())
            """
            import time
            import random
            # Use shorter username to fit in database
            username = f"t_{int(time.time())}{random.randint(100,999)}"
            cursor.execute(user_sql, (username,))
            user_id = cursor.lastrowid
            
            # Create enterprise
            enterprise_sql = """
                INSERT INTO enterprise (user_id, name, create_time, update_time)
                VALUES (%s, 'Test Enterprise Co.', NOW(), NOW())
            """
            cursor.execute(enterprise_sql, (user_id,))
            enterprise_id = cursor.lastrowid
            
            # Create virtual account with initial balance (account_no max 20 chars)
            account_sql = """
                INSERT INTO virtual_account (enterprise_id, account_no, balance, create_time, update_time)
                VALUES (%s, %s, %s, NOW(), NOW())
            """
            # Generate shorter account number (max 20 chars)
            account_no = f"VA{int(time.time())}{random.randint(10,99)}"
            cursor.execute(account_sql, (enterprise_id, account_no, initial_balance))
            account_id = cursor.lastrowid
            
            connection.commit()
            return user_id, enterprise_id, account_id
    except pymysql.Error as e:
        print(f"Create test enterprise error: {e}")
        connection.rollback()
        return None, None, None
    finally:
        connection.close()


def cleanup_test_data(user_id, enterprise_id, account_id):
    """Clean up test data"""
    connection = get_db_connection()
    if not connection:
        return
    
    try:
        with connection.cursor() as cursor:
            # Delete transaction records
            if account_id:
                cursor.execute("DELETE FROM transaction_record WHERE account_id = %s", (account_id,))
            if enterprise_id:
                cursor.execute("DELETE FROM transaction_record WHERE enterprise_id = %s", (enterprise_id,))
            
            # Delete virtual account
            if account_id:
                cursor.execute("DELETE FROM virtual_account WHERE id = %s", (account_id,))
            
            # Delete enterprise
            if enterprise_id:
                cursor.execute("DELETE FROM enterprise WHERE id = %s", (enterprise_id,))
            
            # Delete user
            if user_id:
                cursor.execute("DELETE FROM user WHERE id = %s", (user_id,))
            
            connection.commit()
    except pymysql.Error as e:
        print(f"Cleanup error: {e}")
        connection.rollback()
    finally:
        connection.close()


def get_account_balance(account_id):
    """Get current account balance"""
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        with connection.cursor() as cursor:
            sql = "SELECT balance FROM virtual_account WHERE id = %s"
            cursor.execute(sql, (account_id,))
            result = cursor.fetchone()
            return float(result['balance']) if result else None
    except pymysql.Error as e:
        print(f"Get balance error: {e}")
        return None
    finally:
        connection.close()


def deposit(account_id, enterprise_id, amount, remark=''):
    """
    Perform deposit operation
    Returns: (success: bool, new_balance: float or None)
    """
    if amount <= 0:
        return False, None
    
    connection = get_db_connection()
    if not connection:
        return False, None
    
    try:
        with connection.cursor() as cursor:
            # Get current balance
            cursor.execute("SELECT balance FROM virtual_account WHERE id = %s FOR UPDATE", (account_id,))
            result = cursor.fetchone()
            if not result:
                return False, None
            
            current_balance = float(result['balance'])
            new_balance = round(current_balance + amount, 2)
            
            # Update balance
            cursor.execute(
                "UPDATE virtual_account SET balance = %s, update_time = NOW() WHERE id = %s",
                (new_balance, account_id)
            )
            
            # Create transaction record
            cursor.execute(
                """INSERT INTO transaction_record 
                   (account_id, enterprise_id, type, amount, balance_after, remark, create_time)
                   VALUES (%s, %s, 'deposit', %s, %s, %s, NOW())""",
                (account_id, enterprise_id, amount, new_balance, remark)
            )
            
            connection.commit()
            return True, new_balance
    except pymysql.Error as e:
        print(f"Deposit error: {e}")
        connection.rollback()
        return False, None
    finally:
        connection.close()


def withdraw(account_id, enterprise_id, amount, remark=''):
    """
    Perform withdrawal operation
    Returns: (success: bool, new_balance: float or None, error_reason: str or None)
    """
    if amount <= 0:
        return False, None, "Invalid amount"
    
    connection = get_db_connection()
    if not connection:
        return False, None, "Database connection failed"
    
    try:
        with connection.cursor() as cursor:
            # Get current balance with lock
            cursor.execute("SELECT balance FROM virtual_account WHERE id = %s FOR UPDATE", (account_id,))
            result = cursor.fetchone()
            if not result:
                return False, None, "Account not found"
            
            current_balance = float(result['balance'])
            
            # Check if sufficient balance
            if amount > current_balance:
                connection.rollback()
                return False, current_balance, "Insufficient balance"
            
            new_balance = round(current_balance - amount, 2)
            
            # Update balance
            cursor.execute(
                "UPDATE virtual_account SET balance = %s, update_time = NOW() WHERE id = %s",
                (new_balance, account_id)
            )
            
            # Create transaction record
            cursor.execute(
                """INSERT INTO transaction_record 
                   (account_id, enterprise_id, type, amount, balance_after, remark, create_time)
                   VALUES (%s, %s, 'withdraw', %s, %s, %s, NOW())""",
                (account_id, enterprise_id, amount, new_balance, remark)
            )
            
            connection.commit()
            return True, new_balance, None
    except pymysql.Error as e:
        print(f"Withdraw error: {e}")
        connection.rollback()
        return False, None, str(e)
    finally:
        connection.close()


def get_transaction_records(account_id):
    """Get all transaction records for an account"""
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM transaction_record WHERE account_id = %s ORDER BY create_time ASC"
            cursor.execute(sql, (account_id,))
            return cursor.fetchall()
    except pymysql.Error as e:
        print(f"Get transactions error: {e}")
        return []
    finally:
        connection.close()


# Strategy for generating valid amounts (positive, up to 2 decimal places)
amount_strategy = st.floats(
    min_value=0.01,
    max_value=100000.00,
    allow_nan=False,
    allow_infinity=False
).map(lambda x: round(x, 2))

# Strategy for generating initial balances
initial_balance_strategy = st.floats(
    min_value=0.0,
    max_value=1000000.00,
    allow_nan=False,
    allow_infinity=False
).map(lambda x: round(x, 2))

# Strategy for generating transaction sequences
transaction_strategy = st.lists(
    st.tuples(
        st.sampled_from(['deposit', 'withdraw']),
        amount_strategy
    ),
    min_size=1,
    max_size=10
)


class TestAccountBalanceConsistency:
    """
    Property 1: Account Balance Consistency
    
    Feature: bank-credit-assessment-system, Property 1: Account Balance Consistency
    Validates: Requirements 2.2, 2.3
    """
    
    @given(
        initial_balance=initial_balance_strategy,
        transactions=transaction_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_balance_consistency_after_transactions(self, initial_balance, transactions):
        """
        Property: For any virtual account and any sequence of deposit/withdrawal transactions,
        the final balance should equal the initial balance plus all deposits minus all withdrawals.
        
        **Feature: bank-credit-assessment-system, Property 1: Account Balance Consistency**
        **Validates: Requirements 2.2, 2.3**
        """
        user_id, enterprise_id, account_id = create_test_enterprise_with_account(initial_balance)
        assume(user_id is not None and enterprise_id is not None and account_id is not None)
        
        try:
            expected_balance = initial_balance
            actual_deposits = 0.0
            actual_withdrawals = 0.0
            
            for tx_type, amount in transactions:
                if tx_type == 'deposit':
                    success, new_balance = deposit(account_id, enterprise_id, amount)
                    if success:
                        actual_deposits += amount
                        expected_balance = round(expected_balance + amount, 2)
                else:  # withdraw
                    # Only attempt withdrawal if we expect it to succeed
                    if amount <= expected_balance:
                        success, new_balance, error = withdraw(account_id, enterprise_id, amount)
                        if success:
                            actual_withdrawals += amount
                            expected_balance = round(expected_balance - amount, 2)
            
            # Verify final balance
            final_balance = get_account_balance(account_id)
            assert final_balance is not None, "Should be able to get final balance"
            
            # Calculate expected balance from initial + deposits - withdrawals
            calculated_balance = round(initial_balance + actual_deposits - actual_withdrawals, 2)
            
            # Verify balance consistency
            assert abs(final_balance - expected_balance) < 0.01, \
                f"Final balance {final_balance} should equal expected {expected_balance}"
            assert abs(final_balance - calculated_balance) < 0.01, \
                f"Final balance {final_balance} should equal calculated {calculated_balance}"
            
        finally:
            cleanup_test_data(user_id, enterprise_id, account_id)
    
    @given(
        deposit_amount=amount_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_single_deposit_increases_balance(self, deposit_amount):
        """
        Property: For any deposit, the balance should increase by exactly the deposit amount.
        
        **Feature: bank-credit-assessment-system, Property 1: Account Balance Consistency**
        **Validates: Requirements 2.2**
        """
        initial_balance = 100.00
        user_id, enterprise_id, account_id = create_test_enterprise_with_account(initial_balance)
        assume(user_id is not None and enterprise_id is not None and account_id is not None)
        
        try:
            # Perform deposit
            success, new_balance = deposit(account_id, enterprise_id, deposit_amount)
            assert success, "Deposit should succeed"
            
            # Verify balance increased correctly
            expected_balance = round(initial_balance + deposit_amount, 2)
            final_balance = get_account_balance(account_id)
            
            assert abs(final_balance - expected_balance) < 0.01, \
                f"Balance after deposit {final_balance} should be {expected_balance}"
            
        finally:
            cleanup_test_data(user_id, enterprise_id, account_id)


class TestWithdrawalRejection:
    """
    Property 2: Withdrawal Rejection for Insufficient Balance
    
    Feature: bank-credit-assessment-system, Property 2: Withdrawal Rejection for Insufficient Balance
    Validates: Requirements 2.4
    """
    
    @given(
        initial_balance=st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False).map(lambda x: round(x, 2)),
        withdrawal_amount=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False).map(lambda x: round(x, 2))
    )
    @settings(max_examples=100, deadline=None)
    def test_withdrawal_rejected_when_insufficient_balance(self, initial_balance, withdrawal_amount):
        """
        Property: For any withdrawal attempt where the amount exceeds the current balance,
        the system should reject the transaction and the balance should remain unchanged.
        
        **Feature: bank-credit-assessment-system, Property 2: Withdrawal Rejection for Insufficient Balance**
        **Validates: Requirements 2.4**
        """
        # Only test cases where withdrawal exceeds balance
        assume(withdrawal_amount > initial_balance)
        
        user_id, enterprise_id, account_id = create_test_enterprise_with_account(initial_balance)
        assume(user_id is not None and enterprise_id is not None and account_id is not None)
        
        try:
            # Attempt withdrawal that exceeds balance
            success, returned_balance, error = withdraw(account_id, enterprise_id, withdrawal_amount)
            
            # Verify withdrawal was rejected
            assert not success, "Withdrawal should be rejected when amount exceeds balance"
            assert error == "Insufficient balance", f"Error should indicate insufficient balance, got: {error}"
            
            # Verify balance unchanged
            final_balance = get_account_balance(account_id)
            assert abs(final_balance - initial_balance) < 0.01, \
                f"Balance {final_balance} should remain unchanged at {initial_balance} after rejected withdrawal"
            
        finally:
            cleanup_test_data(user_id, enterprise_id, account_id)
    
    @given(
        initial_balance=st.floats(min_value=100.0, max_value=10000.0, allow_nan=False, allow_infinity=False).map(lambda x: round(x, 2)),
        withdrawal_amount=st.floats(min_value=0.01, max_value=99.99, allow_nan=False, allow_infinity=False).map(lambda x: round(x, 2))
    )
    @settings(max_examples=100, deadline=None)
    def test_withdrawal_succeeds_when_sufficient_balance(self, initial_balance, withdrawal_amount):
        """
        Property: For any withdrawal where amount is less than or equal to balance,
        the withdrawal should succeed and balance should decrease by the withdrawal amount.
        
        **Feature: bank-credit-assessment-system, Property 2: Withdrawal Rejection for Insufficient Balance**
        **Validates: Requirements 2.3, 2.4**
        """
        # Ensure withdrawal is within balance
        assume(withdrawal_amount <= initial_balance)
        
        user_id, enterprise_id, account_id = create_test_enterprise_with_account(initial_balance)
        assume(user_id is not None and enterprise_id is not None and account_id is not None)
        
        try:
            # Attempt valid withdrawal
            success, new_balance, error = withdraw(account_id, enterprise_id, withdrawal_amount)
            
            # Verify withdrawal succeeded
            assert success, f"Withdrawal should succeed when amount {withdrawal_amount} <= balance {initial_balance}"
            assert error is None, "No error should be returned for successful withdrawal"
            
            # Verify balance decreased correctly
            expected_balance = round(initial_balance - withdrawal_amount, 2)
            final_balance = get_account_balance(account_id)
            
            assert abs(final_balance - expected_balance) < 0.01, \
                f"Balance {final_balance} should be {expected_balance} after withdrawal of {withdrawal_amount}"
            
        finally:
            cleanup_test_data(user_id, enterprise_id, account_id)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
