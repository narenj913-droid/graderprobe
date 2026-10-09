from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PublicWorkflowInputSafetyTests(unittest.TestCase):
    def test_composite_action_does_not_interpolate_inputs_into_shell_or_js(self):
        content = (ROOT / "action.yml").read_text(encoding="utf-8")
        self.assertNotIn('mkdir -p "${{ inputs.output-dir }}"', content)
        self.assertNotIn('graderprobe run "${{ inputs.task }}"', content)
        self.assertNotIn("const dir = '${{ inputs.output-dir }}';", content)
        self.assertIn('GRADERPROBE_TASK: ${{ inputs.task }}', content)
        self.assertIn('process.env.GRADERPROBE_OUTPUT_DIR', content)
        self.assertIn("github.event.pull_request.head.repo.full_name == github.repository", content)
        self.assertIn('run: pip install "$GRADERPROBE_ACTION_PATH"', content)

    def test_dispatch_task_uses_environment_variable(self):
        content = (ROOT / ".github/workflows/boundary.yml").read_text(encoding="utf-8")
        self.assertNotIn('run: graderprobe run "${{ github.event.inputs.task }}"', content)
        self.assertIn('GRADERPROBE_TASK: ${{ inputs.task }}', content)
        self.assertIn('graderprobe run "$GRADERPROBE_TASK"', content)

    def test_semantic_base_ref_uses_environment_variable(self):
        content = (ROOT / ".github/workflows/semantic-maintainer.yml").read_text(encoding="utf-8")
        self.assertNotIn('--base-ref "${{ inputs.base-ref }}"', content)
        self.assertIn('GRADERPROBE_BASE_REF: ${{ inputs.base-ref }}', content)
        self.assertIn('--base-ref "$GRADERPROBE_BASE_REF"', content)

    def test_action_validates_paths_and_enums_before_execution(self):
        content = (ROOT / "action.yml").read_text(encoding="utf-8")
        self.assertIn("Validate action inputs", content)
        self.assertIn("inside_workspace(os.environ[\"GRADERPROBE_TASK\"]", content)
        self.assertIn("inside_workspace(os.environ[\"GRADERPROBE_OUTPUT_DIR\"]", content)
        self.assertIn("none|high|medium|any", content)

    def test_shell_scripts_do_not_interpolate_expressions_into_run_blocks(self):
        workflow_paths = sorted((ROOT / ".github/workflows").glob("*.yml"))
        for path in workflow_paths:
            content = path.read_text(encoding="utf-8")
            in_run_block = False
            base_indent = None
            for line in content.splitlines():
                if line.lstrip().startswith("run: |") or line.lstrip().startswith("run: >"):
                    in_run_block = True
                    base_indent = len(line) - len(line.lstrip())
                    continue
                if in_run_block:
                    if line.strip() and (len(line) - len(line.lstrip())) <= base_indent:
                        in_run_block = False
                        base_indent = None
                    elif "${{" in line:
                        self.fail(f"unsafe expression interpolation in shell run block: {path.relative_to(ROOT)}: {line.strip()}")

    def test_contract_lock_is_required_by_its_workflow(self):
        content = (ROOT / ".github/workflows/contract-lock.yml").read_text(encoding="utf-8")
        self.assertIn("Require committed evaluation contract lock", content)
        self.assertIn("if [ ! -f graderprobe.lock.json ]", content)
        self.assertNotIn("if: ${{ hashFiles('graderprobe.lock.json') != '' }}", content)

    def test_external_actions_are_pinned_to_full_commit_shas(self):
        import re

        action_files = [ROOT / "action.yml", *sorted((ROOT / ".github/workflows").glob("*.yml"))]
        uses_re = re.compile(r"^\s*uses:\s*([^\s]+)", re.MULTILINE)
        for path in action_files:
            content = path.read_text(encoding="utf-8")
            for ref in uses_re.findall(content):
                if ref.startswith("./"):
                    continue
                self.assertRegex(
                    ref,
                    r"^[^@]+@[0-9a-f]{40}$",
                    f"External action must be pinned to a full immutable SHA: {path.relative_to(ROOT)} uses {ref}",
                )

    def test_dependabot_updates_github_actions_and_python_dependencies(self):
        content = (ROOT / ".github/dependabot.yml").read_text(encoding="utf-8")
        self.assertIn("package-ecosystem: github-actions", content)
        self.assertIn("package-ecosystem: pip", content)
        self.assertIn("interval: weekly", content)


if __name__ == "__main__":
    unittest.main()
