import unittest
import time
from fastapi.testclient import TestClient
from server import app, global_state

class TestGUIServer(unittest.TestCase):
    def setUp(self):
        import os
        os.environ["PLANNER_MOCK"] = "1"
        self.client = TestClient(app)
        # Force client into mock mode by configuring default mock state
        global_state.reset("Procedural extraction shooter")

    def tearDown(self):
        import os
        os.environ.pop("PLANNER_MOCK", None)

    def test_status_endpoint_initial(self):
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["phase"], "idle")
        self.assertFalse(data["is_waiting"])
        self.assertEqual(data["vram_status"], "Unloaded")

    def test_static_files_served(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Gemma 4 12B - Game Design Planner", response.text)

    def test_full_gui_orchestration_loop_mock(self):
        # We start the planner loop
        # We mock client in global state to enforce mock mode directly
        # Let's start the run
        start_resp = self.client.post("/api/start", json={"concept": "Heist Game UEFN"})
        self.assertEqual(start_resp.status_code, 200)
        self.assertEqual(start_resp.json()["status"], "started")

        # Disable autopilot to run in manual mode
        toggle_resp = self.client.post("/api/autopilot/toggle", json={"enable": False})
        self.assertEqual(toggle_resp.status_code, 200)

        # Wait a short moment for the background thread to run Phase 1, 2, 3 in mock mode 
        # and reach the refinement wait state.
        retries = 35
        reached_wait_state = False
        while retries > 0:
            time.sleep(0.2)
            status_resp = self.client.get("/api/status")
            status_data = status_resp.json()
            if status_data["is_waiting"] and status_data["phase"] == "refinement":
                reached_wait_state = True
                break
            retries -= 1

        self.assertTrue(reached_wait_state, "Server thread did not reach refinement wait state")
        self.assertIn("ECONOMY BALANCING", status_data["architect_content"])

        # Send refinement Action (C)
        action_resp = self.client.post("/api/action", json={"action": "C", "focus": "More weapon balance"})
        self.assertEqual(action_resp.status_code, 200)

        # Wait for it to complete the cycle and enter wait state again
        retries = 35
        updated = False
        while retries > 0:
            time.sleep(0.2)
            status_resp = self.client.get("/api/status")
            status_data = status_resp.json()
            if status_data["is_waiting"] and len(status_data["logs"]) > 0:
                # Check that refinement run was logged
                log_text = "".join(status_data["logs"])
                if "Refinement Cycle 1 Complete" in log_text:
                    updated = True
                    break
            retries -= 1

        self.assertTrue(updated, "Server did not execute refinement cycle")

        # Send Finalize Action (F)
        finalize_resp = self.client.post("/api/action", json={"action": "F"})
        self.assertEqual(finalize_resp.status_code, 200)

        # Wait for thread to finish compiling
        retries = 35
        finished = False
        while retries > 0:
            time.sleep(0.2)
            status_resp = self.client.get("/api/status")
            status_data = status_resp.json()
            if status_data["phase"] == "finished":
                finished = True
                break
            retries -= 1

        self.assertTrue(finished, "Server did not reach finished phase")
        self.assertIn("Final Game Design Document", status_data["final_gdd"])
        self.assertEqual(status_data["vram_status"], "Unloaded")

    def test_autopilot_loop_mock(self):
        # Start the planner loop (autopilot is True by default)
        start_resp = self.client.post("/api/start", json={"concept": "Heist Game UEFN"})
        self.assertEqual(start_resp.status_code, 200)
        self.assertEqual(start_resp.json()["status"], "started")

        # Wait a short moment for it to complete Phase 1-3 baseline and run at least one refinement cycle automatically
        retries = 35
        reached_refinement = False
        status_data = None
        while retries > 0:
            time.sleep(0.2)
            status_resp = self.client.get("/api/status")
            status_data = status_resp.json()
            if status_data["phase"] == "refinement":
                reached_refinement = True
                log_text = "".join(status_data["logs"])
                if "Refinement Cycle 1 Complete" in log_text:
                    break
            retries -= 1

        self.assertTrue(reached_refinement, "Server did not reach refinement automatically")
        self.assertFalse(status_data["is_waiting"], "Server should not be waiting in autopilot mode")

        # Test submitting a custom focus during autopilot
        action_resp = self.client.post("/api/action", json={"action": "C", "focus": "More high-risk vault mechanics"})
        self.assertEqual(action_resp.status_code, 200)

        # Toggle autopilot off
        toggle_resp = self.client.post("/api/autopilot/toggle", json={"enable": False})
        self.assertEqual(toggle_resp.status_code, 200)

        # Wait for it to pause at the end of the current cycle and enter wait state
        retries = 35
        paused = False
        while retries > 0:
            time.sleep(0.2)
            status_resp = self.client.get("/api/status")
            status_data = status_resp.json()
            if status_data["is_waiting"] and status_data["phase"] == "refinement":
                paused = True
                break
            retries -= 1

        self.assertTrue(paused, "Server did not pause after toggle")

        # Finalize design from wait state
        finalize_resp = self.client.post("/api/action", json={"action": "F"})
        self.assertEqual(finalize_resp.status_code, 200)

        # Wait for thread to finish compiling
        retries = 35
        finished = False
        while retries > 0:
            time.sleep(0.2)
            status_resp = self.client.get("/api/status")
            status_data = status_resp.json()
            if status_data["phase"] == "finished":
                finished = True
                break
            retries -= 1

        self.assertTrue(finished, "Server did not reach finished phase")
        self.assertIn("Final Game Design Document", status_data["final_gdd"])

    def test_abort_generation_mock(self):
        # Start the planner loop
        start_resp = self.client.post("/api/start", json={"concept": "Heist Game UEFN"})
        self.assertEqual(start_resp.status_code, 200)
        
        # Abort immediately
        abort_resp = self.client.post("/api/abort")
        self.assertEqual(abort_resp.status_code, 200)
        self.assertEqual(abort_resp.json()["status"], "ok")
        
        # Check that state has been reset to finished
        status_resp = self.client.get("/api/status")
        status_data = status_resp.json()
        self.assertEqual(status_data["phase"], "finished")
        self.assertFalse(status_data["is_waiting"])
        self.assertEqual(status_data["vram_status"], "Unloaded")
        self.assertIn("Generation aborted manually by user.", "".join(status_data["logs"]))

if __name__ == "__main__":
    unittest.main()
