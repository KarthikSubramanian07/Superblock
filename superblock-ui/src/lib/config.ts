// Behavioural constants — same on every machine.
// Edit these to change app behaviour without touching component code.

// Hour the app opens on (6–22). 14 = 2 PM peak stress.
export const INITIAL_HOUR = 14

// Delay before auto-selecting the first hotspot on load (ms).
export const AUTO_SELECT_DELAY_MS = 800

// Artificial delay for the mock simulation spinner (ms).
// Set to 0 when the live backend handles simulation natively.
export const SIM_MOCK_DELAY_MS = 1500
