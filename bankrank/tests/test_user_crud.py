# -*- coding: utf-8 -*-
"""
Property-Based Tests for User CRUD Operations

**Property 8: User CRUD Round-Trip**
**Validates: Requirements 14.2, 14.3, 14.4**

For any valid user data, creating a user then retrieving it should return equivalent data;
updating then retrieving should return updated data; deleting then retrieving should return not found.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
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


def create_user(username, password, name, role, phone=None, email=None):
    """Create a user in the database"""
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO user (username, password, name, role, phone, email, status, create_time, update_time)
                VALUES (%s, %s, %s, %s, %s, %s, 1, NOW(), NOW())
            """
            cursor.execute(sql, (username, password, name, role, phone, email))
            connection.commit()
            return cursor.lastrowid
    except pymysql.Error as e:
        print(f"Create user error: {e}")
        connection.rollback()
        return None
    finally:
        connection.close()


def get_user_by_id(user_id):
    """Get user by ID"""
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM user WHERE id = %s"
            cursor.execute(sql, (user_id,))
            return cursor.fetchone()
    except pymysql.Error as e:
        print(f"Get user error: {e}")
        return None
    finally:
        connection.close()


def update_user(user_id, name=None, phone=None, email=None):
    """Update user information"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        with connection.cursor() as cursor:
            updates = []
            params = []
            
            if name is not None:
                updates.append("name = %s")
                params.append(name)
            if phone is not None:
                updates.append("phone = %s")
                params.append(phone)
            if email is not None:
                updates.append("email = %s")
                params.append(email)
            
            if not updates:
                return True
            
            updates.append("update_time = NOW()")
            params.append(user_id)
            
            sql = f"UPDATE user SET {', '.join(updates)} WHERE id = %s"
            cursor.execute(sql, params)
            connection.commit()
            return cursor.rowcount > 0
    except pymysql.Error as e:
        print(f"Update user error: {e}")
        connection.rollback()
        return False
    finally:
        connection.close()


def delete_user(user_id):
    """Delete user by ID"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        with connection.cursor() as cursor:
            sql = "DELETE FROM user WHERE id = %s"
            cursor.execute(sql, (user_id,))
            connection.commit()
            return cursor.rowcount > 0
    except pymysql.Error as e:
        print(f"Delete user error: {e}")
        connection.rollback()
        return False
    finally:
        connection.close()


def cleanup_test_user(username):
    """Clean up test user by username"""
    connection = get_db_connection()
    if not connection:
        return
    
    try:
        with connection.cursor() as cursor:
            sql = "DELETE FROM user WHERE username = %s"
            cursor.execute(sql, (username,))
            connection.commit()
    except pymysql.Error:
        pass
    finally:
        connection.close()


# Strategy for generating valid usernames (alphanumeric, 3-20 chars)
username_strategy = st.text(
    alphabet=st.sampled_from('abcdefghijklmnopqrstuvwxyz0123456789'),
    min_size=3,
    max_size=20
).map(lambda x: f"test_{x}")

# Strategy for generating valid passwords (6-20 chars)
password_strategy = st.text(
    alphabet=st.sampled_from('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'),
    min_size=6,
    max_size=20
)

# Strategy for generating valid names (Chinese or English, 2-50 chars)
name_strategy = st.text(
    alphabet=st.sampled_from('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'),
    min_size=2,
    max_size=50
)

# Strategy for generating valid roles
role_strategy = st.sampled_from(['enterprise', 'employee', 'admin'])

# Strategy for generating valid phone numbers (optional)
phone_strategy = st.one_of(
    st.none(),
    st.text(alphabet=st.sampled_from('0123456789'), min_size=11, max_size=11)
)

# Strategy for generating valid emails (optional)
email_strategy = st.one_of(
    st.none(),
    st.emails()
)


class TestUserCRUDRoundTrip:
    """
    Property 8: User CRUD Round-Trip
    
    Feature: bank-credit-assessment-system, Property 8: User CRUD Round-Trip
    Validates: Requirements 14.2, 14.3, 14.4
    """
    
    @given(
        username=username_strategy,
        password=password_strategy,
        name=name_strategy,
        role=role_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_create_read_returns_same_data(self, username, password, name, role):
        """
        Property: For any valid user data, creating a user then retrieving it 
        should return equivalent data.
        
        **Feature: bank-credit-assessment-system, Property 8: User CRUD Round-Trip**
        **Validates: Requirements 14.2**
        """
        # Ensure unique username for this test
        assume(len(username) >= 5)
        assume(len(name) >= 2)
        
        # Clean up any existing test user
        cleanup_test_user(username)
        
        try:
            # Create user
            user_id = create_user(username, password, name, role)
            assume(user_id is not None)
            
            # Read user
            user = get_user_by_id(user_id)
            
            # Verify round-trip
            assert user is not None, "User should be retrievable after creation"
            assert user['username'] == username, "Username should match"
            assert user['password'] == password, "Password should match"
            assert user['name'] == name, "Name should match"
            assert user['role'] == role, "Role should match"
            assert user['status'] == 1, "Status should be active (1)"
            
        finally:
            # Cleanup
            cleanup_test_user(username)
    
    @given(
        username=username_strategy,
        password=password_strategy,
        name=name_strategy,
        role=role_strategy,
        new_name=name_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_update_read_returns_updated_data(self, username, password, name, role, new_name):
        """
        Property: For any valid user data, updating then retrieving should return updated data.
        
        **Feature: bank-credit-assessment-system, Property 8: User CRUD Round-Trip**
        **Validates: Requirements 14.3**
        """
        # Ensure unique username and different names
        assume(len(username) >= 5)
        assume(len(name) >= 2)
        assume(len(new_name) >= 2)
        assume(name != new_name)
        
        # Clean up any existing test user
        cleanup_test_user(username)
        
        try:
            # Create user
            user_id = create_user(username, password, name, role)
            assume(user_id is not None)
            
            # Update user
            update_success = update_user(user_id, name=new_name)
            assert update_success, "Update should succeed"
            
            # Read user
            user = get_user_by_id(user_id)
            
            # Verify update
            assert user is not None, "User should be retrievable after update"
            assert user['name'] == new_name, "Name should be updated"
            assert user['username'] == username, "Username should remain unchanged"
            assert user['role'] == role, "Role should remain unchanged"
            
        finally:
            # Cleanup
            cleanup_test_user(username)
    
    @given(
        username=username_strategy,
        password=password_strategy,
        name=name_strategy,
        role=role_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_delete_read_returns_not_found(self, username, password, name, role):
        """
        Property: For any valid user data, deleting then retrieving should return not found.
        
        **Feature: bank-credit-assessment-system, Property 8: User CRUD Round-Trip**
        **Validates: Requirements 14.4**
        """
        # Ensure unique username for this test
        assume(len(username) >= 5)
        assume(len(name) >= 2)
        
        # Clean up any existing test user
        cleanup_test_user(username)
        
        try:
            # Create user
            user_id = create_user(username, password, name, role)
            assume(user_id is not None)
            
            # Verify user exists
            user = get_user_by_id(user_id)
            assert user is not None, "User should exist before deletion"
            
            # Delete user
            delete_success = delete_user(user_id)
            assert delete_success, "Delete should succeed"
            
            # Read user - should return None
            user = get_user_by_id(user_id)
            assert user is None, "User should not be found after deletion"
            
        finally:
            # Cleanup (in case test failed before deletion)
            cleanup_test_user(username)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
