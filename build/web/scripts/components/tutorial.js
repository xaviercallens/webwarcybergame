/**
 * Neo-Hack: Gridlock v3.3.0 - Operative Induction Tutorial Overlay
 * Guides new players through their first interactions.
 */

export class TutorialOverlay {
  constructor() {
    this.steps = [
      {
        text: "Operative, we've detected an intrusion. Select NODE-04 on the map to begin analysis.",
        targetSelector: "#btn-nav-map", // Just a demo selector
        tip: "Always check adjacent nodes."
      },
      {
        text: "Good. Now initiate a Malware Scan on the selected subnet to uncover hidden vectors.",
        targetSelector: "#btn-scan-malware",
        tip: "Scanning costs CU but reveals hidden threats."
      },
      {
        text: "Threat identified. Deploy an ICE Breaker exploit to bypass their outer firewall.",
        targetSelector: "#btn-deploy-exploit",
        tip: "ICE Breakers have a high success rate against baseline defense scripts."
      },
      {
        text: "The node is vulnerable. Execute the Data Siphon protocol to exfiltrate the payload.",
        targetSelector: "#btn-data-siphon",
        tip: "Keep an eye on the trace tracker while siphoning."
      },
      {
        text: "Payload secured. Return to the main command hub to review your XP dossier. COACH out.",
        targetSelector: "#btn-nav-hub",
        tip: "Check your dossier regularly to track rank progression."
      }
    ];
    this.currentStep = 0;
    this.isActive = false;
  }

  init() {
    this.el = document.getElementById('view-tutorial-overlay');
    this.textEl = document.getElementById('tut-text');
    this.progressEl = document.getElementById('tut-progress');
    this.tooltipEl = document.getElementById('tut-tooltip');
    this.tooltipTextEl = document.getElementById('tut-tooltip-text');

    const skipBtn = document.getElementById('btn-tut-skip');
    if (skipBtn) {
      skipBtn.addEventListener('click', () => this.endTutorial());
    }

    // In a real implementation we would listen for game state events
    // For this build, we add a mock keybind "T" to start it
    window.addEventListener('keydown', (e) => {
      if (e.key === 't' || e.key === 'T') {
        if (!this.isActive) {
          this.startTutorial();
        } else {
          this.nextStep();
        }
      }
    });

    // Check if player is new (mock logic: check localStorage)
    const hasCompleted = localStorage.getItem('nh_tutorial_completed');
    if (!hasCompleted) {
      // Delay start slightly on first load
      setTimeout(() => this.startTutorial(), 2000);
    }
  }

  startTutorial() {
    this.currentStep = 0;
    this.isActive = true;
    if (this.el) {
      this.el.style.display = 'block';
      this.el.style.pointerEvents = 'auto'; // allow clicks on skip button
    }
    this.renderStep();
  }

  nextStep() {
    if (!this.isActive) return;
    this.currentStep++;
    if (this.currentStep >= this.steps.length) {
      this.endTutorial();
    } else {
      this.renderStep();
    }
  }

  endTutorial() {
    this.isActive = false;
    if (this.el) {
      this.el.style.display = 'none';
      this.el.style.pointerEvents = 'none';
    }
    this.removeHighlights();
    localStorage.setItem('nh_tutorial_completed', 'true');
  }

  renderStep() {
    const step = this.steps[this.currentStep];
    if (!step) return;

    // Update Text
    if (this.textEl) this.textEl.textContent = step.text;
    if (this.progressEl) this.progressEl.textContent = `STEP ${this.currentStep + 1} / ${this.steps.length}`;

    // Tooltip
    if (this.tooltipEl && this.tooltipTextEl) {
      this.tooltipTextEl.textContent = step.tip;
      this.tooltipEl.style.display = 'block';
      // Moked position center top
      this.tooltipEl.style.top = '20%';
      this.tooltipEl.style.left = '50%';
      this.tooltipEl.style.transform = 'translateX(-50%)';
    }

    this.removeHighlights();
    this.highlightTarget(step.targetSelector);
  }

  highlightTarget(selector) {
    // In a full implementation, we'd query the selector, bring its zIndex up,
    // and highlight it.
    const target = document.querySelector(selector);
    if (!target) return;
    target.classList.add('tutorial-highlight');
  }

  removeHighlights() {
    document.querySelectorAll('.tutorial-highlight').forEach(el => {
      el.classList.remove('tutorial-highlight');
    });
  }
}
