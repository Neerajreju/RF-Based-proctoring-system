# RF-Based AI Proctoring System

## Overview
The **RF-Based AI Proctoring System** is an advanced online exam monitoring solution that integrates **Software-Defined Radio (SDR)** technology with traditional AI-based proctoring tools. The system is designed to enhance exam security by detecting unauthorized electronic devices in the exam environment, monitoring student gaze, and ensuring adherence to exam rules.

---

## Features

- **RF-Based Device Detection**  
  Detects the presence of devices (like mobile phones or unauthorized electronics) within a 2-meter radius using SDR-based radio frequency analysis.

- **AI Face Detection**  
  Real-time monitoring of student identity and presence using computer vision.

- **Gaze Tracking**  
  Monitors student attention and flags suspicious behavior (looking away from the screen).

- **Mobile Device Detection**  
  Integrates YOLOv8 object detection to identify mobile devices during the exam.

- **Audio Monitoring**  
  Detects unusual sounds that may indicate cheating attempts.

- **Tab Monitoring & Control**  
  Prevents tab switching or minimizing the exam window to ensure focus.

- **Admin Dashboard**  
  - Set exam timer  
  - Enable/disable SDR module  
  - Receive real-time alerts for malpractice  
  - Generate unique exam links for students

- **Student Interface**  
  - Countdown timer  
  - Start/submit exam buttons  
  - Real-time monitoring feedback

---

## Tech Stack

- **Backend:** Python, Flask  
- **Frontend:** HTML, CSS, JavaScript  
- **AI & CV:** OpenCV, YOLOv8  
- **RF Detection:** Software-Defined Radio (SDR)  
- **Database:** SQLite or Cloud-based (optional for exam data)  

---

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/rf-proctoring-system.git
