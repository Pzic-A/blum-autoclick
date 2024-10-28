# Blum Autoclick Modified

## Requirements

- Python 3.8 or higher (make sure Python is added to your system's PATH)
- pip (Python package installer)

## Preparation

### 1. Install Python

1. Download the latest version of Python from the [official Python website](https://www.python.org/downloads/).
2. Follow the installation steps for your operating system.
3. **Make sure to check the box that says "Add Python to PATH"** during installation, so you can run Python commands in the terminal or command prompt.

To verify the installation, open a terminal or command prompt and run:

```bash
python --version
```


### 2. Clone the Repository
```bash
git clone https://github.com/winrhcp/blum-autoclick.git
cd blum-autoclick
```


# Setting Up the Virtual Environment

(For 1st time)
```bash
python -m venv venv
```

(For windows)
```bash
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
venv\Scripts\activate
```

```bash
pip install -r requirements.txt
```


### RUN
```bash
python main.py
```