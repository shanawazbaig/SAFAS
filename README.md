# SAFAS(Secure And FAst hardware Scheduler)

![alt text](https://github.com/amin-norollah/safas/blob/main/Logo-SAFAS.png)

Welcome to the SAFAS, Secure and Fast FPGA-based Hardware Scheduler for Accelerating Task Scheduling in Multi-core Systems.


Description
------------
The concept of a hardware scheduler involves separating the task scheduling unit from the Operating System (OS) and delegating it to a dedicated hardware unit in real-time connected embedded systems. The hardware scheduler has direct access to processing units and can perform parallel control on each unit, making it more efficient in managing hardware resources than the OS in multi-core systems.

The main objective of this project was to develop hardware for task scheduling that takes into account security concerns. With the increasing use of embedded systems in IoT technology, these systems have become vulnerable to security breaches. The SAFAS (Security Aware Flexible Architecture for Scheduling) is designed to schedule high-security, safety-critical tasks and their replicas to meet their deadlines and remain safe from schedule-based attacks.

In this project, Verilog hardware description language was used to develop the hardware, with an emphasis on using minimal hardware resources. The code in this repository has been simplified as much as possible and is available for research purposes to everyone.

**If you use SAFAS in your research, we would appreciate the following citation in any publications to which it has contributed:**

Journal paper: [A. Norollah, H. Beitollahi, Z. Kazemi, and M. Fazeli “A security-aware hardware scheduler for modern multi-core systems with hard real-time constraints”, Elsevier Microprocessors and Microsystems (MICPRO), 2022, DOI: 10.1016/j.micpro.2022.104716.](https://doi.org/10.1016/j.micpro.2022.104716)

Conference paper: [A. Norollah, Z. Kazemi, D. Derafshi, H. Beitollahi and M. Fazeli, "Protecting Security-Critical Real-Time Systems against Fault Attacks in Many-Core Platforms," 2022 CPSSI 4th International Symposium on Real-Time and Embedded Systems and Technologies (RTEST), 2022, pp. 1-6, doi: 10.1109/RTEST56034.2022.9850010.](https://doi.org/10.1109/RTEST56034.2022.9850010)

 >Get in touch with me by [a.norollah.official@gmail.com](mailto:a.norollah.official@gmail.com)

Structure
------------
The main structure of SAFAS is as follows:

1. The operating system is responsible for checking the accuracy of the information of each task immediately and sending it to the hardware scheduler.
2. The main queue that has the task of receiving the maximum number of characteristics of real-time tasks.
3. Main hardware scheduler that is responsible for receiving tasks and dispatching them to processing cores.
4. Network on the chip that is responsible for executing tasks (this part is outside the scope of the project).

![alt text](https://github.com/amin-norollah/safas/blob/main/MainArchitecture.jpg)

## 🚀 New: Advanced Scheduling Algorithms

This repository now includes **6 advanced scheduling algorithms** with comprehensive testing framework!

### Algorithms Implemented

1. **Hybrid EDF + SRJF** - Base hybrid scheduler (2× threshold)
2. **Adaptive Threshold** - Configurable threshold (1.5×, 2×, 2.5×)
3. **Multi-Level Priority** - 3-tier urgency system (Critical/Urgent/Normal)
4. **LLF Hybrid** - Least Laxity First with SRJF fallback
5. **Predictive Look-Ahead** - Proactive scheduling with future state prediction
6. **Dynamic Adaptive** - Self-tuning threshold based on performance

### 🏆 Performance Highlights

All algorithms achieved **100% success rate** in comprehensive testing!

| Algorithm | Avg Response Time | Best For |
|-----------|-------------------|----------|
| Pure EDF | 26.45 cycles 🥇 | Response time critical |
| LLF Hybrid | 27.43 cycles 🥈 | Balanced performance |
| Adaptive Threshold | 28.07 cycles | Variable workloads |
| Multi-Level | 28.77 cycles | Mixed criticality |

### Quick Start
```bash
cd verification

# Run comprehensive regression tests (36 test combinations)
python3 regression_tests.py

# Run performance analysis with insights
python3 performance_analysis.py

# Demo advanced algorithms
python3 advanced_schedulers.py
```

### 📚 Documentation
- **Quick Reference**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) ⭐ Start here!
- **Advanced Algorithms**: [ADVANCED_ALGORITHMS.md](ADVANCED_ALGORITHMS.md)
- **Implementation Guide**: [IMPLEMENTATION.md](IMPLEMENTATION.md)
- **Technical Details**: [HYBRID_SCHEDULER_README.md](HYBRID_SCHEDULER_README.md)
- **Complete Summary**: [SUMMARY.md](SUMMARY.md)
- **Academic Paper**: [documentation/hybrid_scheduler_report.tex](documentation/hybrid_scheduler_report.tex)

---

How to Use
------------
The project consists of three main components:

1. **Verilog Hardware Implementation**
   - Requires Xilinx Vivado for synthesis and simulation
   - FPGA-based hardware scheduler modules
   - Located in `source/` directory

2. **Task Generator (C++)**
   - Generates real-time task characteristics
   - Requires C++ compiler or Visual Studio
   - Located in `task generator/` directory

3. **Advanced Scheduling Algorithms (Python)** 🆕
   - 6 scheduling algorithms with comprehensive testing
   - Regression test suite and performance analysis
   - Located in `verification/` directory
   - See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for details
