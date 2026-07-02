# Accessibility Checklist (WCAG 2.1 AA - the HTML renderers)

> Applies to every HTML surface Cambium emits: the gate card (gen_gate_card.py), the sidebar run
> board (gen_board_pro.py), the in-chat board (gen_inline_board.py), the benchmark dashboard
> (gen_dashboard.py), and the static command center (dashboard.html). Complete it before shipping any
> change to those surfaces. Enforced by tests/test_accessibility.py, which renders each surface and
> asserts the items below are present. Aligned to WCAG 2.1 AA. Keep it short; each line is one check.

## Perceivable
- **Screen-reader summary:** the root carries a visually-hidden one-sentence summary of what the
  card, board, or dashboard shows (a .sr-only element, or role plus aria-label on the region).
- **.sr-only actually hides:** position:absolute; width:1px; height:1px; overflow:hidden;
  clip:rect(0 0 0 0) - hidden on screen, still read by assistive tech; never display:none.
- **Non-color status:** queued / working / done is conveyed by a text label, not color alone, and the
  label sits with its agent so the state is announced.
- **Contrast AA:** body and small text meet WCAG AA (4.5:1); muted-on-panel stops that fall short are
  nudged to a passing stop. Do not redesign; adjust the token minimally.
- **Alt text on images:** every informative image has alt text; decorative glyphs are aria-hidden.

## Operable
- **Keyboard operable:** every control is a real button or has role=button plus tabindex=0 and is
  activatable by Enter and Space; nothing is reachable by mouse only.
- **Visible focus:** interactive elements (the gate Approve / Revise / Reject buttons, filters, links)
  show a :focus-visible outline (outline: 2px solid accent; outline-offset: 2px).
- **Reduced motion:** every animation and transition is wrapped so motion-sensitive users are
  respected via @media (prefers-reduced-motion: reduce), and any auto-advancing timer is gated on it.

## Understandable and Robust
- **Semantic roles:** the agent list is role=list with role=listitem per card (or a semantic ul/li);
  the gate card region has an appropriate role and an aria-label naming the decision.
- **aria-live for dynamic regions:** the live-updating board announces streamed findings with
  aria-live=polite so a screen reader hears them without a manual refresh.
- **User text escaped:** any user-supplied text (the gate question, agent findings) stays
  HTML-escaped; the accessibility pass never opens an injection hole.

## Record
Attach the rendered surface to the change and confirm each line above. tests/test_accessibility.py is
the gate: if it fails, the surface is not accessible enough to ship. The Director signs off; a green
suite is necessary, not sufficient - a human still spot-checks with a screen reader when it matters.
