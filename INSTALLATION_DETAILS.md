# 🤖 Robot Speech Visual Feedback Desktop App

This Python application handles real-time audio intensity visualization and communication with Furhat robots.

## ⚠️ Critical Version Requirement

The `furhat-realtime-api` requires **Python 3.10 or higher**. This is due to the use of modern Union type hinting (the `|` operator). Using Python 3.9 or lower will result in a `TypeError`.

---

## 🛠 Setup & Installation

### 1. Version Check

Ensure your global Python version is 3.10+. If not, download the latest version from [python.org](https://python.org).

### 2. Create and Activate Virtual Environment

Delete any existing `venv` folders if you are switching versions or operating systems.

#### **macOS / Linux**

```bash
# Create using specific version (if multiple installed)
/opt/homebrew/bin/python3.13 -m venv venv

# Activate
source venv/bin/activate

# Verify
python --version  # Must be 3.10+

```

#### **Windows (PowerShell)**

```powershell
# Create
python -m venv venv

# Activate (Fix execution policy if script is blocked)
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1

# Verify
python --version  # Must be 3.10+

```

### 3. Install Dependencies

Once the environment is active:

```bash
pip install numpy scipy matplotlib pyserial PySide6 qasync websockets furhat-realtime-api

```

---

## 🚀 Running the App

### **macOS / Linux**

```bash
python3 main.py

```

### **Windows**

On Windows, use `python` instead of `python3` to ensure the terminal uses the local virtual environment rather than the global system Python.

```powershell
python main.py

```

---

## 💡 Common Pitfalls & Solutions

| Problem | Cause | Solution |
| --- | --- | --- |
| `TypeError: unsupported operand type(s) for |` | Running on Python < 3.10 | Recreate `venv` with Python 3.10+. |
| `ModuleNotFoundError: No module named 'qasync'` | Using `python3` on Windows | Use `python` instead of `python3`. |
| `Activate.ps1 cannot be loaded...` | Windows Script Policy | Run `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `Serial port not found` | OS Device Naming | **Mac:** `/dev/tty...` — **Windows:** `COM3`, `COM4`, etc. |

---