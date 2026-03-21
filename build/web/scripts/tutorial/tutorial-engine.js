/**
 * Neo-Hack: Gridlock v3.2 — Interactive Tutorial Engine
 * Step-based engine with highlight boxes, arrows, and instructional text.
 * Steps require the player to perform indicated actions before advancing.
 */

import { events, Events } from '../game-events.js';
import { TUTORIAL_STEPS } from './tutorial-steps.js';

export class TutorialEngine {
  constructor() {
    // Overlay elements
    this.overlay = document.createElement('div');
    this.overlay.id = 'tutorial-overlay';
    this.overlay.className = 'tutorial-overlay';
    this.overlay.style.display = 'none';
    document.body.appendChild(this.overlay);

    this.panel = document.createElement('div');
    this.panel.id = 'tutorial-engine-panel';
    this.panel.className = 'tutorial-engine-panel';
    this.panel.style.display = 'none';
    document.body.appendChild(this.panel);

    this._steps = [...TUTORIAL_STEPS];
    this._currentIndex = -1;
    this._active = false;
    this._eventUnsub = null;
    this._skipTimeout = null;
  }

  get isActive() { return this._active; }
  get currentStep() { return this._steps[this._currentIndex] || null; }

  /**
   * Start the tutorial from the beginning.
   */
  start() {
    this._active = true;
    this._currentIndex = -1;
    this.overlay.style.display = 'block';
    this.panel.style.display = 'block';
    this.next();
  }

  /**
   * Advance to next step.
   */
  next() {
    this._cleanup();
    this._currentIndex++;

    if (this._currentIndex >= this._steps.length) {
      this.finish();
      return;
    }

    const step = this.currentStep;
    this._renderStep(step);
    this._applyHighlight(step);
    this._waitForEvent(step);
  }

  /**
   * Skip to a specific step by ID.
   */
  skipTo(stepId) {
    const idx = this._steps.findIndex(s => s.id === stepId);
    if (idx !== -1) {
      this._cleanup();
      this._currentIndex = idx - 1;
      this.next();
    }
  }

  /**
   * End the tutorial.
   */
  finish() {
    this._cleanup();
    this._active = false;
    this.overlay.style.display = 'none';
    this.panel.style.display = 'none';
    localStorage.setItem('nh_tutorial_done', 'true');
  }

  /**
   * Check if the user has completed the tutorial before.
   */
  static isDone() {
    return localStorage.getItem('nh_tutorial_done') === 'true';
  }

  /**
   * Reset tutorial completion flag.
   */
  static reset() {
    localStorage.removeItem('nh_tutorial_done');
  }

  _renderStep(step) {
    const isLast = this._currentIndex >= this._steps.length - 1;
    const showNext = !step.autoAdvance;
    const stepNum = this._currentIndex + 1;
    const totalSteps = this._steps.length;

    this.panel.innerHTML = `
      <div class="tutorial-engine-panel__header">
        <span class="tutorial-engine-panel__title">${step.title}</span>
        <span class="tutorial-engine-panel__progress">${stepNum} / ${totalSteps}</span>
      </div>
      <div class="tutorial-engine-panel__body">
        <p class="tutorial-engine-panel__text">${step.text}</p>
      </div>
      <div class="tutorial-engine-panel__footer">
        ${showNext ? `<button class="btn btn-primary tutorial-engine-panel__next" id="btn-tut-engine-next">${isLast ? 'FINISH' : 'NEXT >>'}</button>` : `<span class="tutorial-engine-panel__waiting">Perform the action to continue...</span>`}
        <button class="btn tutorial-engine-panel__skip" id="btn-tut-engine-skip">SKIP TUTORIAL</button>
      </div>
    `;

    // Bind next button
    const nextBtn = this.panel.querySelector('#btn-tut-engine-next');
    if (nextBtn) {
      nextBtn.addEventListener('click', () => this.next());
    }

    // Bind skip button
    const skipBtn = this.panel.querySelector('#btn-tut-engine-skip');
    if (skipBtn) {
      skipBtn.addEventListener('click', () => this.finish());
    }

    // Auto-advance timeout fallback (30s)
    if (step.autoAdvance && step.waitForEvent) {
      this._skipTimeout = setTimeout(() => {
        // Show a manual next button after timeout
        const waiting = this.panel.querySelector('.tutorial-engine-panel__waiting');
        if (waiting) {
          waiting.innerHTML = '<button class="btn btn-primary" id="btn-tut-timeout">CONTINUE >></button>';
          this.panel.querySelector('#btn-tut-timeout')?.addEventListener('click', () => this.next());
        }
      }, 30000);
    }
  }

  _applyHighlight(step) {
    // Clear previous highlights
    document.querySelectorAll('.tutorial-highlight').forEach(el => el.classList.remove('tutorial-highlight'));

    if (!step.highlight) {
      this.overlay.innerHTML = '';
      return;
    }

    const target = document.querySelector(step.highlight);
    if (target) {
      target.classList.add('tutorial-highlight');

      // Position an arrow if specified
      if (step.arrow) {
        const rect = target.getBoundingClientRect();
        this.overlay.innerHTML = `<div class="tutorial-arrow tutorial-arrow--${step.arrow}" style="
          left: ${rect.left + rect.width / 2}px;
          top: ${rect.top + rect.height / 2}px;
        "></div>`;
      } else {
        this.overlay.innerHTML = '';
      }
    }
  }

  _waitForEvent(step) {
    if (!step.waitForEvent || !step.autoAdvance) return;

    this._eventUnsub = events.on(step.waitForEvent, (payload) => {
      // Apply optional filter
      if (step.waitFilter && !step.waitFilter(payload)) return;

      // Small delay for visual feedback
      setTimeout(() => this.next(), 500);
    });
  }

  _cleanup() {
    if (this._eventUnsub) {
      this._eventUnsub();
      this._eventUnsub = null;
    }
    if (this._skipTimeout) {
      clearTimeout(this._skipTimeout);
      this._skipTimeout = null;
    }
    document.querySelectorAll('.tutorial-highlight').forEach(el => el.classList.remove('tutorial-highlight'));
  }

  destroy() {
    this._cleanup();
    this.overlay.remove();
    this.panel.remove();
  }
}
