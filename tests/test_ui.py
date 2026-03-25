"""
Playwright end-to-end tests.

Two suites:
  - TestStaticPage  – exercises docs/index.html loaded as a file:// URL
  - TestFlaskPage   – exercises the live Flask server (live_server fixture)

Run all:       pytest tests/test_ui.py
Static only:   pytest tests/test_ui.py -k Static
Flask only:    pytest tests/test_ui.py -k Flask
"""

import json
import pathlib

import pytest
from playwright.sync_api import Page, expect

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

PHRASE = "the quick brown fox"
STATIC_HTML = pathlib.Path(__file__).parent.parent / "docs" / "index.html"


def _type_phrase(page: Page, input_selector: str) -> None:
    """Type every character of PHRASE into the hidden capture input."""
    inp = page.locator(input_selector)
    inp.focus()
    for ch in PHRASE:
        page.keyboard.type(ch, delay=30)


def _fake_profile(name: str, n: int = 5) -> dict:
    """Generate a realistic-looking stored profile for the static page."""
    length = len(PHRASE)
    mean_dwell = [80.0 + i * 1.5 for i in range(length)]
    std_dwell = [15.0] * length
    mean_flight = [50.0 + i for i in range(length - 1)]
    std_flight = [25.0] * (length - 1)
    return {
        "meanDwell": mean_dwell,
        "stdDwell": std_dwell,
        "meanFlight": mean_flight,
        "stdFlight": std_flight,
        "numSamples": n,
    }


def _seed_static_profiles(page: Page, names: list[str]) -> None:
    """Inject profiles into localStorage before the page script runs."""
    profiles = {name: _fake_profile(name) for name in names}
    page.add_init_script(f"""
        localStorage.setItem('kd-profiles', JSON.stringify({json.dumps(profiles)}));
        localStorage.setItem('kd-phrase', JSON.stringify("{PHRASE}"));
        localStorage.setItem('kd-samples', JSON.stringify(5));
        """)


# ---------------------------------------------------------------------------
# Static page tests
# ---------------------------------------------------------------------------


class TestStaticPage:
    """Tests that run against docs/index.html served as a file:// URL."""

    @pytest.fixture(autouse=True)
    def _setup(self, request, page: Page):
        self.page = page
        self.url = STATIC_HTML.as_uri()

    # ── Basic load ──────────────────────────────────────────────────────

    def test_page_title(self):
        self.page.goto(self.url)
        expect(self.page).to_have_title("Keystroke Dynamics Demo")

    def test_three_tabs_visible(self):
        self.page.goto(self.url)
        for label in ("Enrol", "Identify", "Students"):
            expect(self.page.get_by_role("button", name=label)).to_be_visible()

    def test_enrol_tab_active_by_default(self):
        self.page.goto(self.url)
        expect(self.page.locator("#tab-enroll")).to_be_visible()
        expect(self.page.locator("#tab-identify")).to_be_hidden()

    # ── Tab switching ───────────────────────────────────────────────────

    def test_switch_to_identify_tab(self):
        self.page.goto(self.url)
        self.page.locator('[data-tab="identify"]').click()
        expect(self.page.locator("#tab-identify")).to_be_visible()
        expect(self.page.locator("#tab-enroll")).to_be_hidden()

    def test_switch_to_students_tab(self):
        self.page.goto(self.url)
        self.page.locator('[data-tab="students"]').click()
        expect(self.page.locator("#tab-students")).to_be_visible()

    # ── Enrol flow ──────────────────────────────────────────────────────

    def test_start_enroll_requires_name(self):
        self.page.goto(self.url)
        self.page.locator("#btn-start-enroll").click()
        # typing card should NOT appear without a name
        expect(self.page.locator("#enroll-typing-card")).to_be_hidden()

    def test_typing_card_appears_after_name_entered(self):
        self.page.goto(self.url)
        self.page.fill("#enroll-name", "Alice")
        self.page.locator("#btn-start-enroll").click()
        expect(self.page.locator("#enroll-typing-card")).to_be_visible()

    def test_phrase_displayed_in_enroll_card(self):
        self.page.goto(self.url)
        self.page.fill("#enroll-name", "Bob")
        self.page.locator("#btn-start-enroll").click()
        phrase_el = self.page.locator("#enroll-phrase-display")
        expect(phrase_el).to_be_visible()
        # Each character is wrapped in a span; inner_text separates spans with \n
        # and renders spaces as \xa0 — normalise before comparing.
        raw = phrase_el.inner_text()
        normalised = raw.replace("\n", "").replace("\xa0", " ")
        assert normalised == PHRASE

    # ── Students tab ────────────────────────────────────────────────────

    def test_empty_student_list_shows_placeholder(self):
        self.page.goto(self.url)
        self.page.locator('[data-tab="students"]').click()
        expect(self.page.locator("#student-list")).to_contain_text("No students")

    def test_seeded_profiles_appear_in_student_list(self):
        _seed_static_profiles(self.page, ["Charlie", "Diana"])
        self.page.goto(self.url)
        self.page.locator('[data-tab="students"]').click()
        expect(self.page.locator("#student-list")).to_contain_text("Charlie")
        expect(self.page.locator("#student-list")).to_contain_text("Diana")

    # ── Stats modal ─────────────────────────────────────────────────────

    def test_stats_modal_opens_and_closes(self):
        _seed_static_profiles(self.page, ["Eve"])
        self.page.goto(self.url)
        self.page.locator('[data-tab="students"]').click()
        self.page.get_by_role("button", name="View Stats").first.click()
        modal = self.page.locator("#profile-modal")
        expect(modal).to_be_visible()
        # Close via ×
        self.page.locator("#btn-close-modal").click()
        expect(modal).to_be_hidden()

    def test_stats_modal_shows_correct_name(self):
        _seed_static_profiles(self.page, ["Frank"])
        self.page.goto(self.url)
        self.page.locator('[data-tab="students"]').click()
        self.page.get_by_role("button", name="View Stats").first.click()
        expect(self.page.locator("#modal-student-name")).to_have_text("Frank")

    def test_stats_modal_closes_on_escape(self):
        _seed_static_profiles(self.page, ["Grace"])
        self.page.goto(self.url)
        self.page.locator('[data-tab="students"]').click()
        self.page.get_by_role("button", name="View Stats").first.click()
        self.page.keyboard.press("Escape")
        expect(self.page.locator("#profile-modal")).to_be_hidden()

    # ── Delete student ──────────────────────────────────────────────────

    def test_delete_removes_student(self):
        _seed_static_profiles(self.page, ["Heidi", "Ivan"])
        self.page.goto(self.url)
        self.page.locator('[data-tab="students"]').click()
        # The delete button triggers a confirm() dialog — accept it automatically
        self.page.on("dialog", lambda d: d.accept())
        self.page.locator(".student-item").first.get_by_role(
            "button", name="Delete"
        ).click()
        # After deletion only one student should remain
        expect(self.page.locator(".student-item")).to_have_count(1)


# ---------------------------------------------------------------------------
# Flask page tests
# ---------------------------------------------------------------------------


class TestFlaskPage:
    """Tests that run against the live Flask server."""

    @pytest.fixture(autouse=True)
    def _setup(self, live_server: str, page: Page):
        self.page = page
        self.base = live_server

    def _goto(self, path: str = "/") -> None:
        self.page.goto(self.base + path)

    def _enroll_via_api(self, name: str) -> None:
        """Enroll a profile directly via the API (bypasses UI typing)."""
        length = len(PHRASE)
        samples = [
            {
                "dwell": [80.0 + j + i * 1.5 for i in range(length)],
                "flight": [50.0 + j + i for i in range(length - 1)],
            }
            for j in range(5)
        ]
        self.page.request.post(
            self.base + "/api/enroll",
            data=json.dumps({"name": name, "samples": samples}),
            headers={"Content-Type": "application/json"},
        )

    # ── Basic load ──────────────────────────────────────────────────────

    def test_page_title(self):
        self._goto()
        expect(self.page).to_have_title("Keystroke Dynamics Demo")

    def test_three_tabs_visible(self):
        self._goto()
        for label in ("Enrol", "Identify", "Students"):
            expect(self.page.get_by_role("button", name=label)).to_be_visible()

    def test_phrase_shown_in_enrol_tab(self):
        self._goto()
        self.page.fill("#enroll-name", "Test")
        self.page.locator("#btn-start-enroll").click()
        phrase_el = self.page.locator("#enroll-phrase-display")
        expect(phrase_el).to_be_visible()
        raw = phrase_el.inner_text()
        normalised = raw.replace("\n", "").replace("\xa0", " ")
        assert normalised == PHRASE

    # ── Tab switching ───────────────────────────────────────────────────

    def test_switch_to_identify_tab(self):
        self._goto()
        self.page.locator('[data-tab="identify"]').click()
        expect(self.page.locator("#tab-identify")).to_be_visible()

    def test_switch_to_students_tab(self):
        self._goto()
        self.page.locator('[data-tab="students"]').click()
        expect(self.page.locator("#tab-students")).to_be_visible()

    # ── Students tab reflects API state ─────────────────────────────────

    def test_enrolled_name_appears_in_students(self):
        self._enroll_via_api("Judy")
        self._goto()
        self.page.locator('[data-tab="students"]').click()
        expect(self.page.locator("#student-list")).to_contain_text("Judy")

    # ── Stats modal ─────────────────────────────────────────────────────

    def test_stats_modal_opens_for_enrolled_student(self):
        self._enroll_via_api("Karl")
        self._goto()
        self.page.locator('[data-tab="students"]').click()
        # Target Karl's row specifically — live_server accumulates profiles across tests
        self.page.locator(".student-item").filter(has_text="Karl").get_by_role(
            "button", name="View Stats"
        ).click()
        expect(self.page.locator("#profile-modal")).to_be_visible()
        expect(self.page.locator("#modal-student-name")).to_contain_text("Karl")

    def test_stats_modal_closes_on_x(self):
        self._enroll_via_api("Laura")
        self._goto()
        self.page.locator('[data-tab="students"]').click()
        self.page.locator(".student-item").filter(has_text="Laura").get_by_role(
            "button", name="View Stats"
        ).click()
        self.page.locator("#btn-close-modal").click()
        expect(self.page.locator("#profile-modal")).to_be_hidden()

    # ── Start enroll requires name ───────────────────────────────────────

    def test_start_enroll_requires_name(self):
        self._goto()
        self.page.locator("#btn-start-enroll").click()
        expect(self.page.locator("#enroll-typing-card")).to_be_hidden()
