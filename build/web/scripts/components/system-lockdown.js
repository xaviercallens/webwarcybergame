/**
 * Neo-Hack: Gridlock v4.1 — System Lockdown Component
 */
export class SystemLockdown {
  init() {
    const btnReboot = document.getElementById('btn-force-reboot');
    if (btnReboot) {
      btnReboot.addEventListener('click', () => this.forceReboot());
    }
    const btnTerminate = document.getElementById('btn-terminate-all');
    if (btnTerminate) {
      btnTerminate.addEventListener('click', () => this.terminateAll());
    }
  }

  forceReboot() {
    const log = document.getElementById('lockdown-log');
    if (log) {
      this.addLog(log, '>_ FORCE_REBOOT_INITIATED...');
      setTimeout(() => this.addLog(log, '>_ CLEARING_VOLATILE_MEMORY...'), 500);
      setTimeout(() => this.addLog(log, '>_ RESTARTING_KERNEL_SERVICES...'), 1200);
      setTimeout(() => this.addLog(log, '>_ SYSTEM_RESTORE: IN_PROGRESS'), 2000);
    }
  }

  terminateAll() {
    const log = document.getElementById('lockdown-log');
    if (log) {
      this.addLog(log, '>_ TERMINATE_ALL — EMERGENCY_PROTOCOL_ACTIVE');
      this.addLog(log, '>_ SEVERING_ALL_CONNECTIONS...');
    }
  }

  addLog(container, text) {
    const div = document.createElement('div');
    div.style.color = 'var(--color-text-muted)';
    div.style.fontFamily = 'var(--font-mono)';
    div.style.fontSize = 'var(--text-xs)';
    div.textContent = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
  }
}
