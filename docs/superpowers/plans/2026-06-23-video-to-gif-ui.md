# Video-to-GIF UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a plain HTML homepage for uploading MP4 files and viewing/downloading converted GIFs through the existing FastAPI app.

**Architecture:** Keep a single FastAPI app in `main.py` that renders `templates/index.html`, exposes `/api/video-to-gif` for `FormData` uploads, and serves generated GIF files from the mounted `outputs` directory. Use browser-side JavaScript to submit the form, show loading/error states, preview the generated GIF, and separate open-vs-download actions.

**Tech Stack:** FastAPI, Jinja2Templates, plain HTML/CSS/JavaScript, pytest, FastAPI TestClient

---

### Task 1: Lock desired HTTP behavior with tests

**Files:**
- Create: `test_main.py`
- Test: `test_main.py`

- [ ] **Step 1: Write the failing tests**

```python
from io import BytesIO
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_index_renders_upload_interface():
    response = client.get("/")

    assert response.status_code == 200
    assert "Chuyển đổi sang GIF" in response.text


def test_video_to_gif_rejects_non_mp4_upload():
    response = client.post(
        "/api/video-to-gif",
        files={"file": ("sample.txt", BytesIO(b"not-mp4"), "text/plain")},
    )

    assert response.status_code == 400
    assert response.json() == {
        "status": "error",
        "message": "Chỉ hỗ trợ file .mp4",
    }


@patch("main.subprocess.run")
def test_video_to_gif_returns_public_gif_url(mock_run):
    mock_run.return_value = Mock(returncode=0)

    response = client.post(
        "/api/video-to-gif",
        files={"file": ("sample.mp4", BytesIO(b"fake-mp4"), "video/mp4")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["gif_url"].startswith("/outputs/")
    assert body["gif_url"].endswith(".gif")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest test_main.py -v`
Expected: FAIL because the current response shape and/or HTML behavior do not yet match the new UI requirements.

- [ ] **Step 3: Write minimal implementation**

Update `main.py` so `/` renders the upload page, `/api/video-to-gif` only accepts `.mp4`, omits the `-t` ffmpeg flag unless a duration is explicitly provided, and returns `{"status":"success","gif_url":"/outputs/<id>.gif"}` or `{"status":"error","message":"..."}`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest test_main.py -v`
Expected: PASS

### Task 2: Implement the homepage interaction

**Files:**
- Modify: `templates/index.html`
- Test: `test_main.py`

- [ ] **Step 1: Write the failing UI test expectation**

Add or tighten the `/` route test so the page contains upload UI, loading text hook, preview/result sections, and separate view/download actions.

- [ ] **Step 2: Run the targeted test to verify it fails**

Run: `pytest test_main.py::test_index_renders_upload_interface -v`
Expected: FAIL until the new template is in place.

- [ ] **Step 3: Write minimal template implementation**

Render a single-page interface with:

```html
<form id="upload-form">
  <input id="file-input" name="file" type="file" accept=".mp4,video/mp4" required>
  <button id="submit-button" type="submit">Chuyển đổi sang GIF</button>
</form>
<div id="status-message"></div>
<img id="gif-image" alt="GIF preview">
<a id="gif-link" target="_blank" rel="noopener noreferrer"></a>
<a id="download-link" download>Tải xuống</a>
```

Use plain JavaScript to submit `FormData`, disable the button during processing, show clear error messages, update the preview, set the view link to open in a new tab, and keep download behavior on the dedicated button.

- [ ] **Step 4: Run the targeted test to verify it passes**

Run: `pytest test_main.py::test_index_renders_upload_interface -v`
Expected: PASS

### Task 3: Verify the integrated change

**Files:**
- Modify: `main.py`
- Modify: `templates/index.html`
- Test: `test_main.py`

- [ ] **Step 1: Run the focused test suite**

Run: `pytest test_main.py -v`
Expected: PASS

- [ ] **Step 2: Run project verification**

Run: `./bin/brew lgtm`
Expected: PASS if the repository exposes the Homebrew validation command; otherwise record that the command is unavailable in this project and report the limitation clearly.
