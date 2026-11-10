# Accessibility

SuperBlock UI targets **WCAG 2.2 Level AA**.

## Built-in supports

- Document `lang`, descriptive page title, skip link into main content
- Landmarks: `header`, `main`, complementary sidebar, labelled map region
- Tablist for Agents / Hotspot / Simulation with arrow-key navigation
- Visible `:focus-visible` rings; demo toggle and time play/pause expose pressed state
- Keyboard hotspot selection (map overlay list and Hotspot panel list); map canvas remains pointer-primary
- Live regions for connection/hotspot/simulation status
- Mapbox viewport meta is restored so pinch-zoom / browser zoom stays available
- `prefers-reduced-motion` dampens decorative pulse/fade and stops continuous timeline looping
- Stacked layout under ~720px so 320px-wide viewports do not require two-dimensional scrolling

## Known limitations

- Deck.gl / Mapbox canvas hexes are not individually in the accessibility tree; use the hotspot lists or Hotspot panel instead
- World ID widget behaviour depends on `@worldcoin/idkit` and a backend RP context
- Live-backend paths (`/verify-human`, WebSocket tiles) need a running API to exercise end-to-end
