import os
import unittest
import shutil
import tempfile
from unittest.mock import patch, MagicMock
from planner import LocalLLMClient, load_prompt_file

class TestGamePlanner(unittest.TestCase):
    def setUp(self):
        self.test_output_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_output_dir)

    def test_load_prompt_file_success(self):
        path = "prompts/architect_system.txt"
        if os.path.exists(path):
            content = load_prompt_file(path)
            self.assertIn("Lead Game Architect", content)

    def test_mock_client_responses(self):
        client = LocalLLMClient(mock=True)
        # Verify mock response for phase 1 architect
        resp1 = client.generate("Lead Game Architect system prompt", "PHASE 1 instructions")
        self.assertIn("Cyberpunk Vault Raiders", resp1)
        self.assertIn("mutator_zone_device", resp1)

        # Verify mock response for phase 2 architect
        resp2 = client.generate("Lead Game Architect", "PHASE 2 instructions")
        self.assertIn("player_perk_data", resp2)
        self.assertIn("weak_map", resp2)

    @patch("rich.console.Console.input")
    def test_full_pipeline_mock_execution(self, mock_input):
        # We simulate the user choosing 'C' to refine once, 
        # providing feedback 'Test beginner shields', 
        # and then choosing 'F' to finalize and exit.
        mock_input.side_effect = ["C", "Test beginner shields", "F"]
        
        import sys
        test_args = [
            "planner.py",
            "--concept", "Fortnite Battle Royale with RPG Perk Decks",
            "--mock",
            "--output-dir", self.test_output_dir
        ]
        
        with patch.object(sys, 'argv', test_args):
            from planner import main
            # Run the planner main loop
            try:
                main()
            except SystemExit as e:
                self.assertEqual(e.code, 0, "SystemExit raised with non-zero status code")
        
        # Verify that expected output documents are created
        expected_files = [
            "phase1_architect_pitch.md",
            "phase1_critic_audit.md",
            "phase2_architect_verse.md",
            "phase2_critic_audit.md",
            "phase3_architect_economy.md",
            "phase3_critic_audit.md",
            "refinement_cycle_1_critic.md",
            "refinement_cycle_1_architect.md",
            "final_dopamine_audit.md",
            "game_design_document.md"
        ]
        
        for filename in expected_files:
            file_path = os.path.join(self.test_output_dir, filename)
            self.assertTrue(
                os.path.exists(file_path),
                f"Expected file {filename} was not created"
            )
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertGreater(len(content), 0, f"File {filename} is empty")

if __name__ == "__main__":
    unittest.main()
