# Accessibility Checklist

> Ported from [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT)

## Keyboard Navigation

- [ ] All interactive elements reachable via Tab
- [ ] Focus order is logical (matches visual order)
- [ ] Visible focus indicator on all interactive elements
- [ ] No keyboard traps
- [ ] Skip-to-content link available

## Screen Readers

- [ ] Semantic HTML elements used (`<button>`, `<nav>`, `<main>`, `<header>`)
- [ ] Images have meaningful `alt` text (decorative images use `alt=""`)
- [ ] Form inputs have associated `<label>` elements
- [ ] Dynamic content updates use `aria-live` regions
- [ ] Page has a descriptive `<title>`

## Visual Design

- [ ] Text contrast ≥ 4.5:1 for normal text (WCAG AA)
- [ ] Text contrast ≥ 3:1 for large text (≥18px bold or ≥24px)
- [ ] Information not conveyed by color alone
- [ ] Content readable at 200% zoom
- [ ] Responsive design works at 320px width

## Forms & Interaction

- [ ] Error messages are descriptive and associated with fields
- [ ] Required fields clearly indicated
- [ ] Sufficient time to complete actions (no auto-timeout without warning)
- [ ] Touch targets ≥ 44×44px

## Testing Tools

- axe-core / axe DevTools browser extension
- Lighthouse accessibility audit
- Screen reader testing (VoiceOver, NVDA, JAWS)
- Keyboard-only navigation test

## See Also

- `cs-frontend-ui` skill for UI engineering with accessibility
