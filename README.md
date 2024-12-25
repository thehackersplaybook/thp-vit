# The Hackers Playbook (THP) Valuable Internal Tools (VIT) 🛠️

[![GitHub license](https://img.shields.io/badge/license-MIT-blue)](#license)
[![Python](https://img.shields.io/badge/Python-3.8+-brightgreen)](https://www.python.org/)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen)](#contributors)

> 🚦 Disclaimer: VIT is an internal toolset under development and currently tailored for MacOSX. Please ensure compatibility before usage. 

---

## Introduction 🖋️

**Valuable Internal Tools (VIT)** is a curated suite of tools developed at _The Hackers Playbook_ to streamline and automate internal processes. These tools help us manage, organize, and extract value from everyday tasks. ⚡️

![AI Chip System](https://builtin.com/sites/www.builtin.com/files/2024-01/ai-chip.jpg)
> 💡 At THP, we take pride in calling ourselves "Automation Wizards". THP VIT is our attempt to help everyone automate effectively and easily. Consider this a starting point for greater automation adventures. 🔥

The first tool in the suite is:

**Auto Visual Researcher (AVR)**: A lightweight utility designed to:
- Automatically capture and analyze screenshots.
- Append OCR-processed data into a knowledge file (`running_knowledge_${date}.md`).
- Currently supports MacOSX with plans for broader compatibility in future iterations.

---

## Table of Contents 📚

- [Introduction](#introduction)
- [Problem Statement](#problem-statement)
- [Core Features](#core-features)
- [Setup Instructions](#setup-instructions)
- [Usage](#usage)
- [Contributors](#contributors)
- [License](#license)

---

## Problem Statement 💡

At _The Hackers Playbook_, we constantly handle rich visual data from screenshots and documents that require rapid analysis and documentation. Traditional workflows often slow us down with manual steps. VIT, starting with AVR, addresses these inefficiencies by automating the capture, analysis, and organization process.

---

## Core Features ⚙️

### Auto Visual Researcher (AVR)

1. **Shortcut-Based Screenshot Capture:**
   - Default shortcut: `CMD+X` (configurable via command-line).
   
2. **OCR Processing:**
   - Converts captured screenshots into readable text.

3. **Knowledge File Updates:**
   - Automatically appends extracted text into `~/thehackersplaybook/running_knowledge_${date}.md`.

4. **Lightweight & Background-Friendly:**
   - Runs silently in the background, awaiting user input.

---

## Setup Instructions 🔧

### Prerequisites:

- Python 3.8+
- MacOSX (for screenshot functionality)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd thp-vit
   ```

2. **Set up a virtual environment:**
   ```bash
   python3 -m venv env
   . env/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage 🔍

### Starting AVR

Run the following command to start AVR:

```bash
./run_thp_vit.sh avr
```

- AVR will run in the background, listening for the shortcut (default: `CMD+X`).
- Screenshots will be saved temporarily and processed.
- Processed text will be appended to the knowledge file.

### Configuring the Shortcut

You can change the default shortcut via command-line arguments:

```bash
python avr.py --shortcut cmd y
```

---

## Contributors 🤝

- **Aditya Patange** (Lead Developer)

We welcome contributions! Feel free to fork the repository, submit issues, or suggest improvements to our tools. Check out our [Contribution Guidelines](#).

---

## License 📄

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

> _"Automate your tasks, accelerate your knowledge." ~ Anonymous_ ✨

