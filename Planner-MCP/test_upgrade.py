#!/usr/bin/env python3
"""
Planner MCP Server v2.0 - Validation Test Suite

Tests all new functionality to ensure upgrade was successful.
Run this after deploying the upgraded server.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

# Add server directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from server import PlannerAuth, GraphAPIClient
except ImportError:
    print("ERROR: Could not import server.py")
    print("Make sure you're running this from the server directory")
    sys.exit(1)


class TestSuite:
    """Test suite for Planner MCP v2.0"""
    
    def __init__(self):
        self.auth = PlannerAuth()
        self.client = GraphAPIClient(self.auth)
        self.test_results = []
    
    def log_test(self, name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "✓ PASS" if passed else "✗ FAIL"
        self.test_results.append((name, passed, message))
        print(f"{status}: {name}")
        if message:
            print(f"       {message}")
    
    async def test_authentication(self):
        """Test 1: Authentication"""
        print("\n[Test 1] Authentication")
        print("-" * 50)
        try:
            token = await self.auth.get_token()
            self.log_test(
                "Authentication", 
                bool(token and len(token) > 0),
                f"Token acquired ({len(token)} chars)"
            )
        except Exception as e:
            self.log_test("Authentication", False, str(e))
    
    async def test_list_tasks(self):
        """Test 2: List Tasks"""
        print("\n[Test 2] List Tasks")
        print("-" * 50)
        try:
            tasks = await self.client.list_tasks()
            self.log_test(
                "List Tasks",
                isinstance(tasks, list),
                f"Retrieved {len(tasks)} incomplete tasks"
            )
            return tasks
        except Exception as e:
            self.log_test("List Tasks", False, str(e))
            return []
    
    async def test_get_task_details(self, task_id: str):
        """Test 3: Get Task Details (NEW FEATURE)"""
        print("\n[Test 3] Get Task Details (NEW in v2.0)")
        print("-" * 50)
        try:
            details = await self.client.get_task_details(task_id)
            
            # Verify all expected fields are present
            required_fields = [
                'id', 'title', 'bucketName', 'percentComplete',
                'description', 'checklist', 'etag'
            ]
            
            missing_fields = [f for f in required_fields if f not in details]
            
            if missing_fields:
                self.log_test(
                    "Get Task Details",
                    False,
                    f"Missing fields: {missing_fields}"
                )
            else:
                self.log_test(
                    "Get Task Details",
                    True,
                    f"Retrieved: {details['title']} | Bucket: {details['bucketName']}"
                )
                
                # Show sample of retrieved data
                print(f"\n       Sample Data Retrieved:")
                print(f"       Title: {details['title']}")
                print(f"       Bucket: {details['bucketName']}")
                print(f"       Status: {details['percentComplete']}% complete")
                print(f"       Description: {details['description'][:100]}..." if details['description'] else "       Description: (empty)")
                print(f"       Checklist Items: {len(details.get('checklist', {}))}")
            
            return details
            
        except Exception as e:
            self.log_test("Get Task Details", False, str(e))
            return None
    
    async def test_create_task(self):
        """Test 4: Create Task with Description (ENHANCED)"""
        print("\n[Test 4] Create Task with Description (ENHANCED in v2.0)")
        print("-" * 50)
        
        test_title = f"[TEST] Upgrade Validation {datetime.now().strftime('%H:%M:%S')}"
        test_description = "This is a test task created by the v2.0 upgrade validation suite. Safe to delete."
        
        try:
            task = await self.client.create_task(
                title=test_title,
                bucket_name="Strategy & Intel",
                description=test_description
            )
            
            task_id = task.get('id')
            
            self.log_test(
                "Create Task",
                bool(task_id),
                f"Created task: {task_id}"
            )
            
            # Verify description was saved
            if task_id:
                print("       Verifying description was saved...")
                details = await self.client.get_task_details(task_id)
                if details.get('description') == test_description:
                    print("       ✓ Description verified")
                else:
                    print("       ✗ Description mismatch")
            
            return task_id
            
        except Exception as e:
            self.log_test("Create Task", False, str(e))
            return None
    
    async def test_update_task(self, task_id: str):
        """Test 5: Update Task (NEW FEATURE)"""
        print("\n[Test 5] Update Task (NEW in v2.0)")
        print("-" * 50)
        
        if not task_id:
            self.log_test("Update Task", False, "No task ID provided (create test may have failed)")
            return
        
        try:
            # Update multiple fields
            await self.client.update_task(
                task_id=task_id,
                percent_complete=50,
                description="UPDATED: This task was updated by the validation suite"
            )
            
            # Verify update
            details = await self.client.get_task_details(task_id)
            
            updated_correctly = (
                details.get('percentComplete') == 50 and
                'UPDATED' in details.get('description', '')
            )
            
            self.log_test(
                "Update Task",
                updated_correctly,
                f"Progress: {details.get('percentComplete')}% | Description updated"
            )
            
        except Exception as e:
            self.log_test("Update Task", False, str(e))
    
    async def run_all_tests(self, target_task_id: str = None):
        """Run complete test suite"""
        print("\n" + "=" * 70)
        print(" Charter & Stone - Planner MCP Server v2.0")
        print(" Validation Test Suite")
        print("=" * 70)
        
        # Test 1: Authentication
        await self.test_authentication()
        
        # Test 2: List tasks
        tasks = await self.test_list_tasks()
        
        # Test 3: Get task details
        if target_task_id:
            await self.test_get_task_details(target_task_id)
        elif tasks:
            # Use first task if no specific ID provided
            await self.test_get_task_details(tasks[0]['id'])
        
        # Test 4: Create task
        created_task_id = await self.test_create_task()
        
        # Test 5: Update task
        await self.test_update_task(created_task_id)
        
        # Summary
        print("\n" + "=" * 70)
        print(" Test Summary")
        print("=" * 70)
        
        passed = sum(1 for _, p, _ in self.test_results if p)
        total = len(self.test_results)
        
        print(f"\nTests Passed: {passed}/{total}")
        
        if passed == total:
            print("\n✓ ALL TESTS PASSED - Upgrade successful!")
        else:
            print("\n✗ SOME TESTS FAILED - Review errors above")
            print("\nFailed tests:")
            for name, passed, message in self.test_results:
                if not passed:
                    print(f"  - {name}: {message}")
        
        print("\n" + "=" * 70)
        
        if created_task_id:
            print(f"\nNOTE: Test task created with ID: {created_task_id}")
            print("You can safely delete this task from Planner")
        
        return passed == total


async def main():
    """Main test execution"""
    
    # You can specify a task ID to test get_task_details on a real task
    # Example: python test_upgrade.py CfZuItAUdUKOl_LCgsb1i2UAK1rq
    target_task_id = sys.argv[1] if len(sys.argv) > 1 else None
    
    if target_task_id:
        print(f"\nUsing target task ID: {target_task_id}")
    
    suite = TestSuite()
    success = await suite.run_all_tests(target_task_id)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
