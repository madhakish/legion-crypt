import importlib.util
from pathlib import Path
import tempfile
import unittest

PATH = Path(__file__).with_name("spec_plan.py")
SPEC = importlib.util.spec_from_file_location("spec_plan", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.write(MODULE.CONFIG["entry"])

    def write(self, name):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# synthetic fixture; never executed\n")
        return path

    def test_basename_mapping_deduplicates(self):
        self.write("spec/nested/widget_spec.rb")
        result = MODULE.plan(self.root, ["lib/widget.rb", "lib/widget.rb"])
        self.assertEqual(result["spec_candidates"], ["spec/nested/widget_spec.rb"])
        self.assertFalse(result["executed"])

    def test_unknown_change_is_not_silently_covered(self):
        self.assertEqual(MODULE.plan(self.root, ["lib/unknown.rb"])["unmapped_paths"], ["lib/unknown.rb"])

    def test_traversal_and_absolute_paths_rejected(self):
        for path in ["../outside.rb", "/tmp/outside.rb"]:
            with self.assertRaises(ValueError):
                MODULE.plan(self.root, [path])

    def test_symlink_escape_is_rejected(self):
        (self.root / "outside").symlink_to(self.root.parent, target_is_directory=True)
        with self.assertRaises(ValueError):
            MODULE.plan(self.root, ["outside/file.rb"])

    def test_stale_curated_patterns_are_visible(self):
        result = MODULE.plan(self.root, [MODULE.CONFIG["example"]])
        self.assertTrue(result["stale_patterns"])
        self.assertTrue(result["review_notes"])

    def test_curated_patterns_are_current(self):
        root = PATH.resolve().parents[1]
        for _, patterns, _ in MODULE.CONFIG["groups"]:
            for pattern in patterns:
                self.assertTrue(list(root.glob(pattern)), pattern)

    def test_symlink_spec_not_returned(self):
        self.write("outside.rb")
        (self.root / "spec").mkdir()
        (self.root / "spec/widget_spec.rb").symlink_to(self.root / "outside.rb")
        self.assertEqual(MODULE.plan(self.root, ["lib/widget.rb"])["spec_candidates"], [])

    def test_explicit_spec_is_preserved(self):
        self.write("spec/nested/check_spec.rb")
        result = MODULE.plan(self.root, ["spec/nested/check_spec.rb"])
        self.assertEqual(result["spec_candidates"], ["spec/nested/check_spec.rb"])

    def test_real_repository_candidates_exist(self):
        root = PATH.resolve().parents[1]
        result = MODULE.plan(root, [MODULE.CONFIG["example"]])
        self.assertTrue(result["spec_candidates"])
        self.assertEqual(result["stale_patterns"], [])
        self.assertTrue(all((root / p).is_file() for p in result["spec_candidates"]))


if __name__ == "__main__":
    unittest.main()
